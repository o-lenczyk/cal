import streamlit as st

from i18n import t
from ui.theme_toggle import render_theme_toggle

st.set_page_config(page_title="Help", page_icon="❓", layout="wide")
render_theme_toggle()
st.title(t("help_title"))
st.markdown("---")

st.markdown(f"""
{t("help_welcome")}

{t("help_nav")}

- {t("help_vote")}
- {t("help_add")}
- {t("help_games")}
- {t("help_results")}
- {t("help_admin")}
""")

st.markdown("---")
st.caption(t("help_built"))
