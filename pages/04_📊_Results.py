import streamlit as st
import pandas as pd

from i18n import t
from auth import is_oauth_configured, is_logged_in, get_oauth_user, render_logout_button
from db.database import get_db
from db.models import Game, User, Preference, TableInstance, Table
from db.user_helpers import get_user_by_google_id
from logic.scoring import calculate_scores
from logic.assignment import get_available_tables, manually_assign_player
from meeting_date import get_next_meeting_date
from ui.theme_toggle import render_theme_toggle

st.set_page_config(page_title="Results", page_icon="📊", layout="wide")
render_theme_toggle()
render_logout_button()
st.title(t("results_title"))
st.markdown("---")

session = get_db()
meeting_date = get_next_meeting_date(session)

# --- Game Scores ---
st.subheader(t("results_scores"))

scores = calculate_scores(session, meeting_date)

if scores:
    score_data = []
    for entry in scores:
        game = entry["game"]
        score_data.append({
            t("results_game"): game.title,
            t("results_score"): entry["score"],
            t("results_voters"): entry["voter_count"],
            t("results_1st"): entry["n1"],
            t("results_2nd"): entry["n2"],
            t("results_3rd"): entry["n3"],
            t("games_min_players"): game.min_players,
            t("games_max_players"): game.max_players,
            t("games_selected"): "✅" if game.is_selected else "❌",
        })

    df = pd.DataFrame(score_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info(t("results_no_data"))

# --- Table Assignments ---
st.markdown("---")
st.subheader(t("results_tables"))

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
            .filter(User.assigned_table_id == ti.id, User.meeting_date == meeting_date)
            .order_by(User.name)
            .all()
        )
        current = len(assigned_users)
        max_p = min(ti.table.capacity, ti.game.max_players)

        with st.expander(
            f"🎲 {ti.game.title} — {ti.table.name} ({current}/{max_p} " + t("results_players") + ")",
            expanded=True,
        ):
                if assigned_users:
                    for u in assigned_users:
                        st.text(f"  👤 {u.name}")
                else:
                    st.text("  " + t("results_no_players"))
else:
    st.info(t("results_no_tables"))

# --- Unassigned Players ---
st.markdown("---")
st.subheader(t("results_unassigned"))

unassigned_users = (
    session.query(User)
    .filter(
        User.meeting_date == meeting_date,
        User.assigned_table_id.is_(None),
        User.submitted_at.isnot(None),
    )
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
    st.warning(t("results_unassigned_count", count=len(unassigned_with_votes)))

    for u in unassigned_with_votes:
        st.text(f"  👤 {u.name}")

    # Fallback: let unassigned players pick a table
    st.markdown("---")
    st.subheader(t("results_manual_select"))
    st.markdown(t("results_manual_desc"))

    available = get_available_tables(session, meeting_date)

    if available:
        # When OAuth is enabled and user is logged in, auto-detect if they're unassigned
        current_user_for_assign = None
        if is_oauth_configured() and is_logged_in():
            oauth = get_oauth_user()
            if oauth:
                u = get_user_by_google_id(session, oauth["google_id"], meeting_date)
                if u and u.assigned_table_id is None:
                    pref_count = session.query(Preference).filter(Preference.user_id == u.id).count()
                    if pref_count > 0:
                        current_user_for_assign = u

        if current_user_for_assign:
            st.info(t("results_assign_self", name=current_user_for_assign.name))
        else:
            current_user_for_assign = None

        table_options = [
            f"{a['game'].title} — {a['table'].table.name} ({a['current_count']}/{min(a['table'].table.capacity, a['game'].max_players)}, {a['open_seats']} open)"
            for a in available
        ]
        selected_table_label = st.selectbox(t("results_select_table"), options=[""] + table_options)

        if not current_user_for_assign:
            unassigned_names = [u.name for u in unassigned_with_votes]
            selected_user_name = st.selectbox(t("results_select_name"), options=[""] + unassigned_names)
        else:
            selected_user_name = current_user_for_assign.name

        if st.button(t("results_assign_btn"), use_container_width=True):
            if not selected_table_label:
                st.error(t("results_err_table"))
            elif not current_user_for_assign and not selected_user_name:
                st.error(t("results_err_name"))
            else:
                user = (
                    current_user_for_assign
                    or session.query(User).filter(
                        User.name == selected_user_name,
                        User.meeting_date == meeting_date,
                    ).first()
                )
                if not user:
                    st.error(t("results_err_not_found"))
                else:
                    table_idx = table_options.index(selected_table_label)
                    table_info = available[table_idx]
                    success = manually_assign_player(session, user.id, table_info["table"].id)
                    if success:
                        st.success(t("results_success_assign", name=user.name, game=table_info["game"].title, table=table_info["table"].table.name))
                        st.rerun()
                    else:
                        st.error(t("results_err_full"))
    else:
        st.error(t("results_err_no_tables"))
else:
    st.success(t("results_all_assigned"))

session.close()
