"""Light/dark theme toggle and sidebar navigation for Streamlit."""
import streamlit as st

from ui.theme import apply_theme, get_theme, set_theme
from ui.sidebar_nav import render_sidebar_nav


def render_theme_toggle():
    """Render custom nav (translated), then theme toggle in the sidebar."""
    render_sidebar_nav()

    # Load persisted theme and apply (must run before any widgets)
    theme = get_theme()
    st.session_state.theme = theme
    apply_theme(theme)

    def toggle():
        new_theme = "dark" if st.session_state.theme == "light" else "light"
        set_theme(new_theme)
        apply_theme(new_theme)

    label = "🌙 Dark" if st.session_state.theme == "light" else "☀️ Light"
    if st.sidebar.button(label, key="theme_toggle", help="Switch theme"):
        toggle()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("[GitHub](https://github.com/o-lenczyk/cal)")
