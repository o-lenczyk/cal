import streamlit as st
import pandas as pd

from db.database import get_db
from db.models import Game, User, Preference, TableInstance
from logic.scoring import calculate_scores, select_games
from logic.assignment import assign_players

st.set_page_config(page_title="Admin", page_icon="⚙️", layout="wide")
st.title("⚙️ Admin Dashboard")
st.markdown("---")

session = get_db()

# ============================================================
# SECTION 1: Game Management
# ============================================================
st.header("🎲 Game Management")

# Add new game
with st.expander("➕ Add New Game", expanded=False):
    with st.form("add_game_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_title = st.text_input("Game Title", placeholder="e.g. Catan")
        with col2:
            new_min = st.number_input("Min Players", min_value=1, max_value=20, value=2)
        with col3:
            new_max = st.number_input("Max Players", min_value=1, max_value=20, value=6)

        add_submitted = st.form_submit_button("➕ Add Game", use_container_width=True)

    if add_submitted:
        if not new_title.strip():
            st.error("❌ Please enter a game title.")
        elif new_min > new_max:
            st.error("❌ Min players cannot be greater than max players.")
        else:
            existing = session.query(Game).filter(Game.title == new_title.strip()).first()
            if existing:
                st.error(f"❌ Game '{new_title.strip()}' already exists.")
            else:
                game = Game(title=new_title.strip(), min_players=new_min, max_players=new_max)
                session.add(game)
                session.commit()
                st.success(f"✅ Added '{new_title.strip()}' ({new_min}-{new_max} players)")
                st.rerun()

# List existing games
games = session.query(Game).order_by(Game.title).all()

if games:
    st.subheader("📋 Current Games")

    game_data = []
    for g in games:
        table_count = session.query(TableInstance).filter(TableInstance.game_id == g.id).count()
        game_data.append({
            "ID": g.id,
            "Title": g.title,
            "Min Players": g.min_players,
            "Max Players": g.max_players,
            "Tables": table_count,
            "Selected": "✅" if g.is_selected else "❌",
        })

    df = pd.DataFrame(game_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Edit / Delete game
    with st.expander("✏️ Edit or Delete a Game", expanded=False):
        game_titles = [g.title for g in games]
        selected_game_title = st.selectbox("Select game to edit:", options=[""] + game_titles)

        if selected_game_title:
            game_to_edit = session.query(Game).filter(Game.title == selected_game_title).first()

            if game_to_edit:
                with st.form("edit_game_form"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        edit_title = st.text_input("Title", value=game_to_edit.title)
                    with col2:
                        edit_min = st.number_input("Min Players", min_value=1, max_value=20, value=game_to_edit.min_players)
                    with col3:
                        edit_max = st.number_input("Max Players", min_value=1, max_value=20, value=game_to_edit.max_players)

                    col_save, col_delete = st.columns(2)
                    with col_save:
                        save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)
                    with col_delete:
                        delete_btn = st.form_submit_button("🗑️ Delete Game", use_container_width=True)

                if save_btn:
                    if edit_min > edit_max:
                        st.error("❌ Min players cannot be greater than max players.")
                    else:
                        game_to_edit.title = edit_title.strip()
                        game_to_edit.min_players = edit_min
                        game_to_edit.max_players = edit_max
                        session.commit()
                        st.success(f"✅ Updated '{edit_title.strip()}'")
                        st.rerun()

                if delete_btn:
                    session.delete(game_to_edit)
                    session.commit()
                    st.success(f"✅ Deleted '{selected_game_title}'")
                    st.rerun()
else:
    st.info("No games added yet. Use the form above to add your first game!")

# ============================================================
# SECTION 2: Table Management
# ============================================================
st.markdown("---")
st.header("🪑 Table Management")

selected_games = session.query(Game).filter(Game.is_selected == True).order_by(Game.title).all()

if selected_games:
    for game in selected_games:
        tables = (
            session.query(TableInstance)
            .filter(TableInstance.game_id == game.id)
            .order_by(TableInstance.table_number)
            .all()
        )

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            player_info = []
            for t in tables:
                count = session.query(User).filter(User.assigned_table_id == t.id).count()
                player_info.append(f"T{t.table_number}: {count}/{game.max_players}")

            st.markdown(f"**{game.title}** — {len(tables)} table(s) | {' | '.join(player_info)}")

        with col2:
            if st.button(f"➕ Add Table", key=f"add_table_{game.id}"):
                next_num = max([t.table_number for t in tables], default=0) + 1
                new_table = TableInstance(game_id=game.id, table_number=next_num)
                session.add(new_table)
                session.commit()
                st.rerun()

        with col3:
            if len(tables) > 1:
                last_table = tables[-1]
                users_at_last = session.query(User).filter(User.assigned_table_id == last_table.id).count()
                if users_at_last == 0:
                    if st.button(f"➖ Remove Table", key=f"rm_table_{game.id}"):
                        session.delete(last_table)
                        session.commit()
                        st.rerun()
                else:
                    st.button(f"➖ Remove Table", key=f"rm_table_{game.id}", disabled=True, help="Can't remove — players assigned")
else:
    st.info("No games selected yet. Run the scoring algorithm first.")

# ============================================================
# SECTION 3: Scoring & Assignment
# ============================================================
st.markdown("---")
st.header("🚀 Run Algorithms")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Calculate Scores & Select Games", use_container_width=True):
        selected = select_games(session)
        if selected:
            st.success(f"✅ {len(selected)} game(s) selected: {', '.join(g.title for g in selected)}")
        else:
            st.warning("⚠️ No games met the selection criteria.")
        st.rerun()

with col2:
    if st.button("🪑 Run Player Assignment", use_container_width=True):
        result = assign_players(session)
        assigned_count = len(result["assigned"])
        unassigned_count = len(result["unassigned"])
        st.success(f"✅ {assigned_count} player(s) assigned, {unassigned_count} unassigned")
        if result["unassigned"]:
            st.warning("Unassigned: " + ", ".join(u.name for u in result["unassigned"]))
        st.rerun()

with col3:
    if st.button("🔄 Reset All Assignments", use_container_width=True):
        session.query(User).update({User.assigned_table_id: None})
        session.commit()
        st.success("✅ All assignments have been reset.")
        st.rerun()

# ============================================================
# SECTION 4: Overview
# ============================================================
st.markdown("---")
st.header("📈 Overview")

total_users = session.query(User).count()
users_with_votes = (
    session.query(User)
    .filter(User.submitted_at.isnot(None))
    .count()
)
assigned_users = session.query(User).filter(User.assigned_table_id.isnot(None)).count()
total_games = session.query(Game).count()
selected_count = session.query(Game).filter(Game.is_selected == True).count()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Users", total_users)
col2.metric("Votes Submitted", users_with_votes)
col3.metric("Players Assigned", assigned_users)
col4.metric("Games (Selected/Total)", f"{selected_count}/{total_games}")

session.close()
