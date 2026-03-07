import streamlit as st

from ui.theme_toggle import render_theme_toggle

st.set_page_config(page_title="Help", page_icon="❓", layout="wide")
render_theme_toggle()
st.title("❓ Help")
st.markdown("---")

st.markdown("""
Welcome to the **Board Game Night Planner**!

Use the sidebar to navigate:

- **🗳️ Vote** — Submit your top 1–3 game preferences
- **➕ Add Game** — Add new games manually
- **📋 Current Games** — View and edit game catalog
- **📊 Results** — View game scores and table assignments
- **⚙️ Admin** — Run algorithms, manage tables, import from XLSX
""")

st.markdown("---")
st.caption("Built with Streamlit • PostgreSQL • Python")
