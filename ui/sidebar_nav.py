"""Custom sidebar navigation with translated page labels."""
import streamlit as st

from i18n import t


def render_sidebar_nav():
    """Render page links in the sidebar with translated labels."""
    st.sidebar.page_link("pages/01_🗳️_Vote.py", label="🗳️ " + t("nav_vote"))
    st.sidebar.page_link("pages/02_➕_Add_Game.py", label="➕ " + t("nav_add_game"))
    st.sidebar.page_link("pages/03_📋_Current_Games.py", label="📋 " + t("nav_current_games"))
    st.sidebar.page_link("pages/04_📊_Results.py", label="📊 " + t("nav_results"))
    st.sidebar.page_link("pages/05_⚙️_Admin.py", label="⚙️ " + t("nav_admin"))
    st.sidebar.page_link("pages/06_❓_Help.py", label="❓ " + t("nav_help"))
    st.sidebar.page_link("pages/07_👤_User_Settings.py", label="👤 " + t("nav_user_settings"))
