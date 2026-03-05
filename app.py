import streamlit as st

st.set_page_config(
    page_title="🎲 Board Game Night Planner",
    page_icon="🎲",
    layout="wide",
)

st.title("🎲 Board Game Night Planner")
st.markdown("---")

st.markdown("""
Welcome to the **Board Game Night Planner**! 

Use the sidebar to navigate between pages:

- **🗳️ Vote** — Submit your top 3 game preferences
- **📊 Results** — View game scores and table assignments
- **⚙️ Admin** — Manage games, tables, and run the assignment algorithm
""")

st.markdown("---")
st.caption("Built with Streamlit • PostgreSQL • Python")
