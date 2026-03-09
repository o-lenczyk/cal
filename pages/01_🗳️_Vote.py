import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from auth import (
    is_oauth_configured,
    is_logged_in,
    get_oauth_user,
    render_login_gate,
    render_logout_button,
)
from db.database import get_db
from db.models import Game, User, Preference
from db.user_helpers import get_user_by_google_id, get_user_by_name, get_or_create_user_by_oauth
from logic.scoring import calculate_scores
from ui.theme_toggle import render_theme_toggle

st.set_page_config(
    page_title="🗳️ Vote",
    page_icon="🗳️",
    layout="wide",
)

render_theme_toggle()
render_logout_button()

st.title("🗳️ Vote for Your Games")
st.markdown("Pick **1 to 3** board games for game night (in order of preference).")
st.markdown("---")

session = get_db()

# Get games sorted by popularity
scores = calculate_scores(session)
scores.sort(key=lambda s: s["voter_count"], reverse=True)
games = [s["game"] for s in scores]
game_map = {g.title: g for g in games}

if not games:
    st.warning("⚠️ No games available yet. Ask an admin to add some games first!")
    session.close()
    st.stop()

game_titles = [g.title for g in games]


# --- OAuth vs Legacy: determine current user ---
use_oauth = is_oauth_configured()
current_user: User | None = None
default_name = ""
default_choices = ["", "", ""]

if use_oauth:
    if not render_login_gate():
        session.close()
        st.stop()
    oauth = get_oauth_user()
    if oauth:
        current_user = get_user_by_google_id(session, oauth["google_id"])
        if current_user:
            default_name = current_user.name
            prefs = (
                session.query(Preference)
                .filter(Preference.user_id == current_user.id)
                .order_by(Preference.rank)
                .all()
            )
            for i, p in enumerate(prefs):
                if i < 3 and p.game.title in game_map:
                    default_choices[i] = p.game.title
        else:
            default_name = oauth["name"]
else:
    # Legacy: pre-fill from session or URL
    def _get_voter_param() -> str:
        if st.session_state.get("voter_name"):
            return st.session_state.voter_name
        try:
            v = st.query_params.get("voter")
            if isinstance(v, list) and v:
                return (v[0] or "").strip()
            if isinstance(v, str):
                return v.strip()
        except Exception:
            pass
        return ""

    saved_name = _get_voter_param()
    if saved_name:
        existing = get_user_by_name(session, saved_name.strip())
        if existing:
            current_user = existing
            default_name = existing.name
            prefs = (
                session.query(Preference)
                .filter(Preference.user_id == existing.id)
                .order_by(Preference.rank)
                .all()
            )
            for i, p in enumerate(prefs):
                if i < 3 and p.game.title in game_map:
                    default_choices[i] = p.game.title


# --- My Votes section (when logged in / identified and has votes) ---
if current_user and (default_choices[0] or default_choices[1] or default_choices[2]):
    with st.expander("📋 My current votes", expanded=True):
        prefs_display = [c for c in default_choices if c]
        for i, title in enumerate(prefs_display, start=1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            st.text(f"{emoji} {title}")
        st.caption("Change your choices below and submit to update.")
    st.markdown("---")


def _set_voter_param(name: str) -> None:
    st.session_state.voter_name = name
    try:
        if hasattr(st, "experimental_set_query_params"):
            st.experimental_set_query_params(voter=name)
        else:
            st.query_params["voter"] = name
    except Exception:
        pass


# --- Voting form ---
with st.form("vote_form"):
    st.subheader("Your Info")
    if use_oauth and is_logged_in():
        oauth = get_oauth_user()
        st.text_input("Your Name", value=oauth["name"] if oauth else "", disabled=True)
        user_name = (oauth["name"] if oauth else "").strip()
    else:
        user_name = st.text_input(
            "Your Name", placeholder="Enter your name...", value=default_name
        )

    st.subheader("Your Choices")
    if default_choices[0] or default_choices[1] or default_choices[2]:
        st.caption("Your previous vote is shown. Change and submit to update.")
    col1, col2, col3 = st.columns(3)

    opts = [""] + game_titles

    def _idx(choice: str) -> int:
        return opts.index(choice) if choice in opts else 0

    with col1:
        choice_1 = st.selectbox(
            "🥇 1st Choice (3 points)", options=opts, index=_idx(default_choices[0])
        )
    with col2:
        choice_2 = st.selectbox(
            "🥈 2nd Choice (2 points)", options=opts, index=_idx(default_choices[1])
        )
    with col3:
        choice_3 = st.selectbox(
            "🥉 3rd Choice (1 point)", options=opts, index=_idx(default_choices[2])
        )

    submitted = st.form_submit_button("🗳️ Submit Vote", use_container_width=True)

if submitted:
    errors = []
    choices = [c for c in [choice_1, choice_2, choice_3] if c]

    if use_oauth:
        if not user_name.strip():
            errors.append("Please log in to vote.")
    else:
        if not user_name.strip():
            errors.append("Please enter your name.")

    if len(choices) < 1:
        errors.append("Please select at least 1 game.")
    if len(choices) != len(set(choices)):
        errors.append("Each choice must be a different game.")

    if errors:
        for err in errors:
            st.error(f"❌ {err}")
    else:
        try:
            if use_oauth:
                oauth = get_oauth_user()
                if not oauth:
                    st.error("❌ Session expired. Please log in again.")
                else:
                    user = get_or_create_user_by_oauth(
                        session,
                        google_id=oauth["google_id"],
                        email=oauth["email"],
                        name=oauth["name"],
                    )
            else:
                existing_user = get_user_by_name(session, user_name.strip())
                if existing_user:
                    session.query(Preference).filter(
                        Preference.user_id == existing_user.id
                    ).delete()
                    user = existing_user
                    user.submitted_at = func.now()
                else:
                    user = User(name=user_name.strip())
                    session.add(user)
                    session.flush()

            session.query(Preference).filter(Preference.user_id == user.id).delete()
            for rank, choice_title in enumerate(choices, start=1):
                game = game_map[choice_title]
                pref = Preference(user_id=user.id, game_id=game.id, rank=rank)
                session.add(pref)
            user.submitted_at = func.now()
            session.commit()

            if not use_oauth:
                _set_voter_param(user_name.strip())
            st.success(f"✅ Vote submitted successfully for **{user.name}**!")
            st.balloons()
            st.rerun()

        except Exception as e:
            session.rollback()
            st.error(f"❌ Error submitting vote: {e}")

# Most popular games
popular = [s for s in scores if s["voter_count"] > 0][:10]
if popular:
    st.markdown("---")
    st.subheader("🔥 Most popular right now")
    popular_df = pd.DataFrame(
        [{"Game": s["game"].title, "Votes": s["voter_count"]} for s in popular]
    )
    st.table(popular_df)

# Who has voted
st.markdown("---")
st.subheader("📋 Who Has Voted")

users = session.query(User).order_by(User.submitted_at.desc()).all()

if users:
    for user in users:
        prefs = (
            session.query(Preference)
            .filter(Preference.user_id == user.id)
            .order_by(Preference.rank)
            .all()
        )
        pref_text = ", ".join(
            [f"{'🥇🥈🥉'[p.rank - 1]} {p.game.title}" for p in prefs]
        )
        st.text(f"👤 {user.name} — {pref_text}")
else:
    st.info("No votes yet. Be the first to vote!")

session.close()
