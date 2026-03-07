import streamlit as st

from db.database import get_db
from db.models import Game
from ui.theme_toggle import render_theme_toggle

st.set_page_config(page_title="Add Game", page_icon="➕", layout="wide")
render_theme_toggle()
st.title("➕ Add Game")
st.markdown("---")

session = get_db()

# Add new game
st.header("➕ Add New Game")
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

session.close()
