import streamlit as st
import pandas as pd

from i18n import t
from db.database import get_db
from db.models import Game, TableInstance
from ui.theme_toggle import render_theme_toggle

st.set_page_config(page_title="Current Games", page_icon="📋", layout="wide")
render_theme_toggle()
st.title(t("games_title"))
st.markdown("---")

session = get_db()

games = session.query(Game).order_by(Game.title).all()

if games:
    game_data = []
    for g in games:
        table_count = session.query(TableInstance).filter(TableInstance.game_id == g.id).count()
        game_data.append({
            t("games_id"): g.id,
            t("games_title_col"): g.title,
            t("games_min_players"): g.min_players,
            t("games_max_players"): g.max_players,
            t("games_tables"): table_count,
            t("games_selected"): "✅" if g.is_selected else "❌",
        })

    df = pd.DataFrame(game_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Edit / Delete game
    with st.expander(t("games_edit_expander"), expanded=False):
        game_titles = [g.title for g in games]
        selected_game_title = st.selectbox(t("games_select_to_edit"), options=[""] + game_titles)

        if selected_game_title:
            game_to_edit = session.query(Game).filter(Game.title == selected_game_title).first()

            if game_to_edit:
                with st.form("edit_game_form"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        edit_title = st.text_input(t("games_title_col"), value=game_to_edit.title)
                    with col2:
                        edit_min = st.number_input(t("games_min_players"), min_value=1, max_value=20, value=game_to_edit.min_players)
                    with col3:
                        edit_max = st.number_input(t("games_max_players"), min_value=1, max_value=20, value=game_to_edit.max_players)

                    col_save, col_delete = st.columns(2)
                    with col_save:
                        save_btn = st.form_submit_button(t("games_save"), use_container_width=True)
                    with col_delete:
                        delete_btn = st.form_submit_button(t("games_delete"), use_container_width=True)

                if save_btn:
                    if edit_min > edit_max:
                        st.error(t("games_err_min_max"))
                    else:
                        game_to_edit.title = edit_title.strip()
                        game_to_edit.min_players = edit_min
                        game_to_edit.max_players = edit_max
                        session.commit()
                        st.success(t("games_success_updated", title=edit_title.strip()))
                        st.rerun()

                if delete_btn:
                    session.delete(game_to_edit)
                    session.commit()
                    st.success(t("games_success_deleted", title=selected_game_title))
                    st.rerun()
else:
    st.info(t("games_no_games"))

session.close()
