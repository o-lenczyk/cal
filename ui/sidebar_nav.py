"""Custom sidebar navigation with translated page labels."""
import streamlit as st

from i18n import t
from ui.theme import get_theme


def render_sidebar_nav():
    """Render page links in the sidebar with translated labels. Preserves theme in URL."""
    theme = get_theme()
    qp = {"theme": theme} if theme else None

    def link(page: str, label: str):
        st.sidebar.page_link(page, label=label, query_params=qp)

    link("pages/01_🗳️_Vote.py", "🗳️ " + t("nav_vote"))
    link("pages/02_➕_Add_Game.py", "➕ " + t("nav_add_game"))
    link("pages/03_📋_Current_Games.py", "📋 " + t("nav_current_games"))
    link("pages/04_📊_Results.py", "📊 " + t("nav_results"))
    link("pages/05_⚙️_Admin.py", "⚙️ " + t("nav_admin"))
    link("pages/06_❓_Help.py", "❓ " + t("nav_help"))
    link("pages/07_👤_User_Settings.py", "👤 " + t("nav_user_settings"))
