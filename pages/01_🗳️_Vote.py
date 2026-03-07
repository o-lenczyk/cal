import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Game, User, Preference
from logic.scoring import calculate_scores
from ui.theme_toggle import render_theme_toggle

st.set_page_config(
    page_title="🗳️ Vote",
    page_icon="🗳️",
    layout="wide",
)

render_theme_toggle()
st.title("🗳️ Vote for Your Games")
st.markdown("Pick **1 to 3** board games for game night (in order of preference).")
st.markdown("---")


def get_existing_user(session: Session, name: str) -> User | None:
    return session.query(User).filter(User.name == name).first()


session = get_db()

# Get games sorted by popularity (most votes first, ignore weights)
scores = calculate_scores(session)
scores.sort(key=lambda s: s["voter_count"], reverse=True)
games = [s["game"] for s in scores]
game_map = {g.title: g for g in games}

if not games:
    st.warning("⚠️ No games available yet. Ask an admin to add some games first!")
    session.close()
    st.stop()

game_titles = [g.title for g in games]

# Pre-fill from session (same-session) or URL (survives refresh)
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


def _set_voter_param(name: str) -> None:
    st.session_state.voter_name = name
    try:
        if hasattr(st, "experimental_set_query_params"):
            st.experimental_set_query_params(voter=name)
        else:
            st.query_params["voter"] = name
    except Exception:
        pass


def _clear_voter_param() -> None:
    st.session_state.pop("voter_name", None)
    try:
        if hasattr(st, "experimental_get_query_params"):
            params = dict(st.experimental_get_query_params())
        else:
            params = dict(st.query_params)
        params.pop("voter", None)
        if hasattr(st, "experimental_set_query_params"):
            st.experimental_set_query_params(**{k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in params.items()})
        else:
            st.query_params.clear()
            for k, v in params.items():
                st.query_params[k] = v[0] if isinstance(v, list) and len(v) == 1 else v
    except Exception:
        pass

saved_name = _get_voter_param()
default_name = ""
default_choices = ["", "", ""]
if saved_name:
    existing = get_existing_user(session, saved_name.strip())
    if existing:
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

# "Vote as someone else" to clear URL param (hidden for now, may use later)
# if default_name:
#     if st.button("🔄 Vote as someone else", help="Clear saved name and vote as a different person"):
#         _clear_voter_param()
#         st.rerun()

# Voting form
with st.form("vote_form"):
    st.subheader("Your Info")
    user_name = st.text_input("Your Name", placeholder="Enter your name...", value=default_name)

    st.subheader("Your Choices")
    if default_choices[0] or default_choices[1] or default_choices[2]:
        st.caption("Your previous vote is shown. Change and submit to update.")
    col1, col2, col3 = st.columns(3)

    opts = [""] + game_titles

    def _idx(choice: str) -> int:
        return opts.index(choice) if choice in opts else 0

    with col1:
        choice_1 = st.selectbox("🥇 1st Choice (3 points)", options=opts, index=_idx(default_choices[0]))
    with col2:
        choice_2 = st.selectbox("🥈 2nd Choice (2 points)", options=opts, index=_idx(default_choices[1]))
    with col3:
        choice_3 = st.selectbox("🥉 3rd Choice (1 point)", options=opts, index=_idx(default_choices[2]))

    submitted = st.form_submit_button("🗳️ Submit Vote", use_container_width=True)

if submitted:
    # Validation
    errors = []

    if not user_name.strip():
        errors.append("Please enter your name.")

    choices = [c for c in [choice_1, choice_2, choice_3] if c]

    if len(choices) < 1:
        errors.append("Please select at least 1 game.")

    if len(choices) != len(set(choices)):
        errors.append("Each choice must be a different game.")

    if errors:
        for err in errors:
            st.error(f"❌ {err}")
    else:
        try:
            # Check if user already voted
            existing_user = get_existing_user(session, user_name.strip())

            if existing_user:
                # Update existing vote
                session.query(Preference).filter(Preference.user_id == existing_user.id).delete()
                user = existing_user
                # Update submission timestamp
                from sqlalchemy.sql import func
                user.submitted_at = func.now()
            else:
                # Create new user
                user = User(name=user_name.strip())
                session.add(user)
                session.flush()

            # Add preferences (only for selected choices, ranks 1, 2, 3)
            for rank, choice_title in enumerate(choices, start=1):
                game = game_map[choice_title]
                pref = Preference(user_id=user.id, game_id=game.id, rank=rank)
                session.add(pref)

            session.commit()
            # Save voter name to session + URL so it persists across refresh
            _set_voter_param(user_name.strip())
            st.success(f"✅ Vote submitted successfully for **{user_name.strip()}**!")
            st.balloons()
            st.rerun()  # Reload so form shows saved name and votes

        except Exception as e:
            session.rollback()
            st.error(f"❌ Error submitting vote: {e}")

# Most popular games (between voting and who has voted)
popular = [s for s in scores if s["voter_count"] > 0][:10]
if popular:
    st.markdown("---")
    st.subheader("🔥 Most popular right now")
    popular_df = pd.DataFrame([
        {"Game": s["game"].title, "Votes": s["voter_count"]} for s in popular
    ])
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
            [f"{'🥇🥈🥉'[p.rank-1]} {p.game.title}" for p in prefs]
        )
        st.text(f"👤 {user.name} — {pref_text}")
else:
    st.info("No votes yet. Be the first to vote!")

session.close()
