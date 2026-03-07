import os
import tempfile

import streamlit as st
import pandas as pd

from db.database import get_db
from db.models import Game, User, Preference, TableInstance, Table
from db.import_games import import_from_xlsx
from logic.scoring import calculate_scores, select_games
from logic.assignment import assign_players
from ui.theme_toggle import render_theme_toggle

st.set_page_config(page_title="Admin", page_icon="⚙️", layout="wide")
render_theme_toggle()
st.title("⚙️ Admin Dashboard")
st.markdown("---")

session = get_db()

# ============================================================
# Import from XLSX
# ============================================================
st.header("📥 Import from XLSX")
st.caption("Supports multi-sheet xlsx (incl. Kocie-gierce format). Uses BGG_Games sheet if present, else first sheet with Name column. Columns: ID, Name, Best With / Recommended With (e.g. '2–6 players').")
uploaded = st.file_uploader("Upload xlsx file", type=["xlsx"])
if uploaded and st.button("Import Games", use_container_width=True):
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = tmp.name
    try:
        result = import_from_xlsx(session, tmp_path)
        st.success(f"✅ Imported {result['added']} game(s), skipped {result['skipped']} (already exist)")
        if result["errors"]:
            st.warning("Some rows had errors: " + "; ".join(result["errors"][:5]))
        st.rerun()
    except Exception as e:
        session.rollback()
        st.error(f"❌ Import failed: {e}")
    finally:
        os.unlink(tmp_path)

st.markdown("---")

# ============================================================
# SECTION 2: Scoring & Assignment
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
# SECTION 3: Physical Tables & Game Assignment
# ============================================================
st.markdown("---")
st.header("🪑 Physical Tables")

physical_tables = session.query(Table).order_by(Table.sort_order).all()

with st.expander("➕ Add Physical Table", expanded=False):
    with st.form("add_table_form"):
        col1, col2 = st.columns(2)
        with col1:
            table_name = st.text_input("Table Name", placeholder="e.g. Table 1")
        with col2:
            table_capacity = st.number_input("Capacity (seats)", min_value=2, max_value=12, value=6)
        if st.form_submit_button("➕ Add Table"):
            if table_name.strip():
                next_order = (session.query(Table).count() or 0) + 1
                t = Table(name=table_name.strip(), capacity=table_capacity, sort_order=next_order)
                session.add(t)
                session.commit()
                st.success(f"✅ Added {table_name.strip()} ({table_capacity} seats)")
                st.rerun()
            else:
                st.error("Please enter a table name.")

# Edit / Delete physical tables
if physical_tables:
    st.subheader("📋 Current Tables")
    for t in physical_tables:
        ti = session.query(TableInstance).filter(TableInstance.table_id == t.id).first()
        game_name = ti.game.title if ti and ti.game else "(no game assigned)"
        count = session.query(User).filter(User.assigned_table_id == ti.id).count() if ti else 0
        cap = min(t.capacity, ti.game.max_players) if ti and ti.game else t.capacity

        with st.expander(f"**{t.name}** — {t.capacity} seats | {game_name} ({count}/{cap})", expanded=False):
            with st.form(f"edit_table_{t.id}"):
                new_name = st.text_input("Name", value=t.name, key=f"name_{t.id}")
                new_cap = st.number_input("Capacity", min_value=2, max_value=12, value=t.capacity, key=f"cap_{t.id}")
                if st.form_submit_button("💾 Save"):
                    t.name = new_name.strip()
                    t.capacity = new_cap
                    session.commit()
                    st.rerun()
            if st.button(f"🗑️ Delete Table", key=f"del_{t.id}"):
                if ti and session.query(User).filter(User.assigned_table_id == ti.id).count() > 0:
                    st.error("Can't delete — players assigned. Reset assignments first.")
                else:
                    if ti:
                        session.delete(ti)
                    session.delete(t)
                    session.commit()
                    st.rerun()

st.subheader("🎲 Assign Games to Tables")
st.caption("Assign a selected game to each physical table. Run 'Calculate Scores & Select Games' first.")
selected_games = session.query(Game).filter(Game.is_selected == True).order_by(Game.title).all()
game_opts = ["(no game)"] + [g.title for g in selected_games]

if physical_tables and selected_games:
    with st.form("assign_games_form"):
        assigns = {}
        for t in physical_tables:
            ti = session.query(TableInstance).filter(TableInstance.table_id == t.id).first()
            current = ti.game.title if ti and ti.game else "(no game)"
            idx = game_opts.index(current) if current in game_opts else 0
            assigns[t.id] = st.selectbox(f"{t.name}", options=game_opts, index=idx, key=f"assign_{t.id}")
        if st.form_submit_button("💾 Save Assignments"):
            for t in physical_tables:
                chosen = assigns[t.id]
                ti = session.query(TableInstance).filter(TableInstance.table_id == t.id).first()
                if chosen == "(no game)":
                    if ti:
                        session.delete(ti)
                else:
                    g = session.query(Game).filter(Game.title == chosen).first()
                    if g:
                        if ti:
                            ti.game_id = g.id
                        else:
                            session.add(TableInstance(table_id=t.id, game_id=g.id))
            session.commit()
            st.success("✅ Assignments saved.")
            st.rerun()
elif not physical_tables:
    st.info("Add physical tables above first.")
elif not selected_games:
    st.info("Run 'Calculate Scores & Select Games' first to select games.")

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
