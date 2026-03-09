import streamlit as st

from i18n import t
from db.database import get_db
from db.models import Game
from ui.theme_toggle import render_theme_toggle

st.set_page_config(page_title="Add Game", page_icon="➕", layout="wide")
render_theme_toggle()
st.title(t("add_title"))
st.markdown("---")

session = get_db()

# Add new game
st.header(t("add_header"))
with st.form("add_game_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        new_title = st.text_input(t("add_game_title"), placeholder=t("add_game_placeholder"))
    with col2:
        new_min = st.number_input(t("add_min_players"), min_value=1, max_value=20, value=2)
    with col3:
        new_max = st.number_input(t("add_max_players"), min_value=1, max_value=20, value=6)

    add_submitted = st.form_submit_button(t("add_button"), use_container_width=True)

if add_submitted:
    if not new_title.strip():
        st.error(t("add_err_title"))
    elif new_min > new_max:
        st.error(t("add_err_min_max"))
    else:
        existing = session.query(Game).filter(Game.title == new_title.strip()).first()
        if existing:
            st.error(t("add_err_exists", title=new_title.strip()))
        else:
            game = Game(title=new_title.strip(), min_players=new_min, max_players=new_max)
            session.add(game)
            session.commit()
            st.success(t("add_success", title=new_title.strip(), min=new_min, max=new_max))
            st.rerun()

session.close()
