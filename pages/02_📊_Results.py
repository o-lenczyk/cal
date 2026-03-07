import streamlit as st
import pandas as pd

from db.database import get_db
from db.models import Game, User, Preference, TableInstance
from logic.scoring import calculate_scores
from logic.assignment import get_available_tables
from ui.theme_toggle import render_theme_toggle

st.set_page_config(page_title="Results", page_icon="📊", layout="wide")
render_theme_toggle()
st.title("📊 Results & Assignments")
st.markdown("---")

session = get_db()

# --- Game Scores ---
st.subheader("🏆 Game Scores")

scores = calculate_scores(session)

if scores:
    score_data = []
    for entry in scores:
        game = entry["game"]
        score_data.append({
            "Game": game.title,
            "Score": entry["score"],
            "Voters": entry["voter_count"],
            "1st ⭐": entry["n1"],
            "2nd ⭐": entry["n2"],
            "3rd ⭐": entry["n3"],
            "Min Players": game.min_players,
            "Max Players": game.max_players,
            "Selected": "✅" if game.is_selected else "❌",
        })

    df = pd.DataFrame(score_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No games or votes yet.")

# --- Table Assignments ---
st.markdown("---")
st.subheader("🪑 Table Assignments")

selected_games = session.query(Game).filter(Game.is_selected == True).order_by(Game.title).all()

if selected_games:
    for game in selected_games:
        tables = (
            session.query(TableInstance)
            .filter(TableInstance.game_id == game.id)
            .order_by(TableInstance.table_number)
            .all()
        )

        for table in tables:
            assigned_users = (
                session.query(User)
                .filter(User.assigned_table_id == table.id)
                .order_by(User.name)
                .all()
            )

            current = len(assigned_users)
            max_p = game.max_players

            with st.expander(
                f"🎲 {game.title} — Table {table.table_number} ({current}/{max_p} players)",
                expanded=True,
            ):
                if assigned_users:
                    for u in assigned_users:
                        st.text(f"  👤 {u.name}")
                else:
                    st.text("  (no players assigned yet)")
else:
    st.info("No games have been selected yet. An admin needs to run the scoring algorithm first.")

# --- Unassigned Players ---
st.markdown("---")
st.subheader("⚠️ Unassigned Players")

unassigned_users = (
    session.query(User)
    .filter(User.assigned_table_id.is_(None))
    .filter(User.submitted_at.isnot(None))
    .order_by(User.name)
    .all()
)

# Only show users who have actually voted (have preferences)
unassigned_with_votes = []
for u in unassigned_users:
    pref_count = session.query(Preference).filter(Preference.user_id == u.id).count()
    if pref_count > 0:
        unassigned_with_votes.append(u)

if unassigned_with_votes:
    st.warning(f"{len(unassigned_with_votes)} player(s) could not be automatically assigned:")

    for u in unassigned_with_votes:
        st.text(f"  👤 {u.name}")

    # Fallback: let unassigned players pick a table
    st.markdown("---")
    st.subheader("🔄 Manual Table Selection")
    st.markdown("If you're unassigned, pick an available table below:")

    available = get_available_tables(session)

    if available:
        # Select user
        unassigned_names = [u.name for u in unassigned_with_votes]
        selected_user_name = st.selectbox("Select your name:", options=[""] + unassigned_names)

        # Select table
        table_options = [
            f"{t['game'].title} — Table {t['table'].table_number} ({t['current_count']}/{t['game'].max_players}, {t['open_seats']} open)"
            for t in available
        ]
        selected_table_label = st.selectbox("Select a table:", options=[""] + table_options)

        if st.button("✅ Assign Me", use_container_width=True):
            if not selected_user_name or not selected_table_label:
                st.error("Please select both your name and a table.")
            else:
                table_idx = table_options.index(selected_table_label)
                table_info = available[table_idx]

                user = session.query(User).filter(User.name == selected_user_name).first()
                if user:
                    from logic.assignment import manually_assign_player
                    success = manually_assign_player(session, user.id, table_info["table"].id)
                    if success:
                        st.success(f"✅ {user.name} assigned to {table_info['game'].title} — Table {table_info['table'].table_number}!")
                        st.rerun()
                    else:
                        st.error("❌ Table is full. Please choose another.")
    else:
        st.error("No tables with open seats available.")
else:
    st.success("✅ All voters have been assigned to tables!")

session.close()
