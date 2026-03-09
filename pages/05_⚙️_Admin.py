import os
import tempfile

import streamlit as st
import pandas as pd

from i18n import t, get_language, set_language, LANGUAGES
from db.database import get_db
from db.models import Game, User, Preference, TableInstance, Table
from db.import_games import import_from_xlsx
from logic.scoring import calculate_scores, select_games
from logic.assignment import assign_players
from ui.theme_toggle import render_theme_toggle

st.set_page_config(page_title="Admin", page_icon="⚙️", layout="wide")
render_theme_toggle()
st.title(t("admin_title"))
st.markdown("---")

session = get_db()

# ============================================================
# Language selector (at top)
# ============================================================
st.header(t("admin_language"))
current_lang = get_language()
lang_choice = st.selectbox(
    t("admin_select_language"),
    options=list(LANGUAGES.keys()),
    format_func=lambda k: LANGUAGES[k],
    index=list(LANGUAGES.keys()).index(current_lang) if current_lang in LANGUAGES else 0,
    key="admin_lang_select",
    help=t("admin_language_help"),
)
if lang_choice != current_lang:
    set_language(lang_choice)
    st.success(t("admin_lang_updated", lang=LANGUAGES[lang_choice]))
    st.rerun()

st.markdown("---")

# ============================================================
# Import from XLSX
# ============================================================
st.header(t("admin_import"))
st.caption(t("admin_import_caption"))
uploaded = st.file_uploader(t("admin_upload"), type=["xlsx"])
if uploaded and st.button(t("admin_import_btn"), use_container_width=True):
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = tmp.name
    try:
        result = import_from_xlsx(session, tmp_path)
        st.success(t("admin_import_success", added=result["added"], skipped=result["skipped"]))
        if result["errors"]:
            err_str = "; ".join(result["errors"][:5])
            st.warning(t("admin_import_errors", errors=err_str))
        st.rerun()
    except Exception as e:
        session.rollback()
        st.error(t("admin_import_failed", error=str(e)))
    finally:
        os.unlink(tmp_path)

st.markdown("---")

# ============================================================
# SECTION 2: Scoring & Assignment
# ============================================================
st.markdown("---")
st.header(t("admin_algorithms"))

col1, col2, col3 = st.columns(3)

with col1:
    if st.button(t("admin_calc_scores"), use_container_width=True):
        selected = select_games(session)
        if selected:
            st.success(t("admin_calc_success", count=len(selected), games=", ".join(g.title for g in selected)))
        else:
            st.warning(t("admin_calc_warning"))
        st.rerun()

with col2:
    if st.button(t("admin_run_assignment"), use_container_width=True):
        result = assign_players(session)
        assigned_count = len(result["assigned"])
        unassigned_count = len(result["unassigned"])
        st.success(t("admin_assigned", assigned=assigned_count, unassigned=unassigned_count))
        if result["unassigned"]:
            st.warning(t("admin_unassigned_list", names=", ".join(u.name for u in result["unassigned"])))
        st.rerun()

with col3:
    if st.button(t("admin_reset"), use_container_width=True):
        session.query(User).update({User.assigned_table_id: None})
        session.commit()
        st.success(t("admin_reset_success"))
        st.rerun()

# ============================================================
# SECTION 3: Physical Tables & Game Assignment
# ============================================================
st.markdown("---")
st.header(t("admin_physical_tables"))

physical_tables = session.query(Table).order_by(Table.sort_order).all()

with st.expander(t("admin_add_table"), expanded=False):
    with st.form("add_table_form"):
        col1, col2 = st.columns(2)
        with col1:
            table_name = st.text_input(t("admin_table_name"), placeholder=t("admin_table_placeholder"))
        with col2:
            table_capacity = st.number_input(t("admin_capacity"), min_value=2, max_value=12, value=6)
        if st.form_submit_button(t("admin_add_table_btn")):
            if table_name.strip():
                next_order = (session.query(Table).count() or 0) + 1
                t_obj = Table(name=table_name.strip(), capacity=table_capacity, sort_order=next_order)
                session.add(t_obj)
                session.commit()
                st.success(t("admin_add_table_success", name=table_name.strip(), capacity=table_capacity))
                st.rerun()
            else:
                st.error(t("admin_table_name_err"))

# Edit / Delete physical tables
if physical_tables:
    st.subheader(t("admin_current_tables"))
    for tbl in physical_tables:
        ti = session.query(TableInstance).filter(TableInstance.table_id == tbl.id).first()
        game_name = ti.game.title if ti and ti.game else t("admin_no_game")
        count = session.query(User).filter(User.assigned_table_id == ti.id).count() if ti else 0
        cap = min(tbl.capacity, ti.game.max_players) if ti and ti.game else tbl.capacity

        with st.expander(f"**{tbl.name}** — {tbl.capacity} " + t("results_players") + f" | {game_name} ({count}/{cap})", expanded=False):
            with st.form(f"edit_table_{tbl.id}"):
                new_name = st.text_input(t("admin_name"), value=tbl.name, key=f"name_{tbl.id}")
                new_cap = st.number_input(t("admin_capacity"), min_value=2, max_value=12, value=tbl.capacity, key=f"cap_{tbl.id}")
                if st.form_submit_button(t("admin_save")):
                    tbl.name = new_name.strip()
                    tbl.capacity = new_cap
                    session.commit()
                    st.rerun()
            if st.button(t("admin_delete_table"), key=f"del_{tbl.id}"):
                if ti and session.query(User).filter(User.assigned_table_id == ti.id).count() > 0:
                    st.error(t("admin_cant_delete"))
                else:
                    if ti:
                        session.delete(ti)
                    session.delete(tbl)
                    session.commit()
                    st.rerun()

st.subheader(t("admin_assign_games"))
st.caption(t("admin_assign_caption"))
selected_games = session.query(Game).filter(Game.is_selected == True).order_by(Game.title).all()
game_opts = [t("admin_no_game_opt")] + [g.title for g in selected_games]

if physical_tables and selected_games:
    with st.form("assign_games_form"):
        assigns = {}
        for tbl in physical_tables:
            ti = session.query(TableInstance).filter(TableInstance.table_id == tbl.id).first()
            current = ti.game.title if ti and ti.game else t("admin_no_game_opt")
            idx = game_opts.index(current) if current in game_opts else 0
            assigns[tbl.id] = st.selectbox(tbl.name, options=game_opts, index=idx, key=f"assign_{tbl.id}")
        if st.form_submit_button(t("admin_save_assignments")):
            for tbl in physical_tables:
                chosen = assigns[tbl.id]
                ti = session.query(TableInstance).filter(TableInstance.table_id == tbl.id).first()
                if chosen == t("admin_no_game_opt"):
                    if ti:
                        session.delete(ti)
                else:
                    g = session.query(Game).filter(Game.title == chosen).first()
                    if g:
                        if ti:
                            ti.game_id = g.id
                        else:
                            session.add(TableInstance(table_id=tbl.id, game_id=g.id))
            session.commit()
            st.success(t("admin_assignments_saved"))
            st.rerun()
elif not physical_tables:
    st.info(t("admin_add_tables_first"))
elif not selected_games:
    st.info(t("admin_run_calc_first"))

# ============================================================
# SECTION 4: Overview
# ============================================================
st.markdown("---")
st.header(t("admin_overview"))

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
col1.metric(t("admin_total_users"), total_users)
col2.metric(t("admin_votes_submitted"), users_with_votes)
col3.metric(t("admin_players_assigned"), assigned_users)
col4.metric(t("admin_games_selected"), f"{selected_count}/{total_games}")

session.close()
