import streamlit as st
import pandas as pd

from auth import is_oauth_configured, is_logged_in, get_oauth_user, render_logout_button
from db.database import get_db
from db.models import Game, User, Preference, TableInstance, Table
from db.user_helpers import get_user_by_google_id
from logic.scoring import calculate_scores
from logic.assignment import get_available_tables, manually_assign_player
from ui.theme_toggle import render_theme_toggle

st.set_page_config(page_title="Results", page_icon="📊", layout="wide")
render_theme_toggle()
render_logout_button()
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

# Show by physical table (TableInstance links table + game)
table_instances = (
    session.query(TableInstance)
    .join(TableInstance.game)
    .join(TableInstance.table)
    .filter(Game.is_selected == True)
    .order_by(Table.sort_order)
    .all()
)

if table_instances:
    for ti in table_instances:
        assigned_users = (
            session.query(User)
            .filter(User.assigned_table_id == ti.id)
            .order_by(User.name)
            .all()
        )
        current = len(assigned_users)
        max_p = min(ti.table.capacity, ti.game.max_players)

        with st.expander(
            f"🎲 {ti.game.title} — {ti.table.name} ({current}/{max_p} players)",
            expanded=True,
        ):
                if assigned_users:
                    for u in assigned_users:
                        st.text(f"  👤 {u.name}")
                else:
                    st.text("  (no players assigned yet)")
else:
    st.info("No tables with games assigned yet. An admin needs to run scoring and assign games to tables.")

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
        # When OAuth is enabled and user is logged in, auto-detect if they're unassigned
        current_user_for_assign = None
        if is_oauth_configured() and is_logged_in():
            oauth = get_oauth_user()
            if oauth:
                u = get_user_by_google_id(session, oauth["google_id"])
                if u and u.assigned_table_id is None:
                    pref_count = session.query(Preference).filter(Preference.user_id == u.id).count()
                    if pref_count > 0:
                        current_user_for_assign = u

        if current_user_for_assign:
            st.info(f"**{current_user_for_assign.name}** — select a table to assign yourself:")
        else:
            current_user_for_assign = None

        table_options = [
            f"{t['game'].title} — {t['table'].table.name} ({t['current_count']}/{min(t['table'].table.capacity, t['game'].max_players)}, {t['open_seats']} open)"
            for t in available
        ]
        selected_table_label = st.selectbox("Select a table:", options=[""] + table_options)

        if not current_user_for_assign:
            unassigned_names = [u.name for u in unassigned_with_votes]
            selected_user_name = st.selectbox("Select your name:", options=[""] + unassigned_names)
        else:
            selected_user_name = current_user_for_assign.name

        if st.button("✅ Assign Me", use_container_width=True):
            if not selected_table_label:
                st.error("Please select a table.")
            elif not current_user_for_assign and not selected_user_name:
                st.error("Please select your name.")
            else:
                user = current_user_for_assign or session.query(User).filter(User.name == selected_user_name).first()
                if not user:
                    st.error("User not found.")
                else:
                    table_idx = table_options.index(selected_table_label)
                    table_info = available[table_idx]
                    success = manually_assign_player(session, user.id, table_info["table"].id)
                    if success:
                        st.success(f"✅ {user.name} assigned to {table_info['game'].title} — {table_info['table'].table.name}!")
                        st.rerun()
                    else:
                        st.error("❌ Table is full. Please choose another.")
    else:
        st.error("No tables with open seats available.")
else:
    st.success("✅ All voters have been assigned to tables!")

session.close()
