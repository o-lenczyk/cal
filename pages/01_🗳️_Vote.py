import streamlit as st
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Game, User, Preference

st.set_page_config(page_title="Vote", page_icon="🗳️", layout="wide")
st.title("🗳️ Vote for Your Games")
st.markdown("Pick **1 to 3** board games for game night (in order of preference).")
st.markdown("---")


def get_games(session: Session) -> list[Game]:
    return session.query(Game).order_by(Game.title).all()


def get_existing_user(session: Session, name: str) -> User | None:
    return session.query(User).filter(User.name == name).first()


session = get_db()

games = get_games(session)

if not games:
    st.warning("⚠️ No games available yet. Ask an admin to add some games first!")
    session.close()
    st.stop()

game_titles = [g.title for g in games]
game_map = {g.title: g for g in games}

# Voting form
with st.form("vote_form"):
    st.subheader("Your Info")
    user_name = st.text_input("Your Name", placeholder="Enter your name...")

    st.subheader("Your Choices")
    col1, col2, col3 = st.columns(3)

    with col1:
        choice_1 = st.selectbox("🥇 1st Choice (3 points)", options=[""] + game_titles, index=0)
    with col2:
        choice_2 = st.selectbox("🥈 2nd Choice (2 points)", options=[""] + game_titles, index=0)
    with col3:
        choice_3 = st.selectbox("🥉 3rd Choice (1 point)", options=[""] + game_titles, index=0)

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
            st.success(f"✅ Vote submitted successfully for **{user_name.strip()}**!")
            st.balloons()

        except Exception as e:
            session.rollback()
            st.error(f"❌ Error submitting vote: {e}")

# Show current voters
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
