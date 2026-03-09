"""Light/dark theme toggle and sidebar navigation for Streamlit."""
import streamlit as st

from ui.sidebar_nav import render_sidebar_nav


def render_theme_toggle():
    """Render custom nav (translated), then theme toggle in the sidebar."""
    render_sidebar_nav()
    if "theme" not in st.session_state:
        st.session_state.theme = "light"

    def toggle():
        prev = st.session_state.theme
        st.session_state.theme = "dark" if prev == "light" else "light"
        base = st.session_state.theme
        try:
            config = getattr(st, "_config", None)
            if config and hasattr(config, "set_option"):
                config.set_option("theme.base", base)
                if base == "dark":
                    config.set_option("theme.backgroundColor", "#0e1117")
                    config.set_option("theme.secondaryBackgroundColor", "#262730")
                    config.set_option("theme.textColor", "#fafafa")
                else:
                    config.set_option("theme.backgroundColor", "#ffffff")
                    config.set_option("theme.secondaryBackgroundColor", "#f0f2f6")
                    config.set_option("theme.textColor", "#31333f")
        except Exception:
            pass

    label = "🌙 Dark" if st.session_state.theme == "light" else "☀️ Light"
    if st.sidebar.button(label, key="theme_toggle", help="Switch theme"):
        toggle()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("[GitHub](https://github.com/o-lenczyk/cal)")
