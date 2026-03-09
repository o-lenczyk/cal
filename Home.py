import streamlit as st

st.set_page_config(page_title="Board Game Night", page_icon="🎲", layout="wide")

# Redirect to Vote as the entry page, preserve query params (e.g. theme)
qp = dict(st.query_params) if hasattr(st, "query_params") else None
st.switch_page("pages/01_🗳️_Vote.py", query_params=qp)
