"""User Settings — change display name and account preferences."""
import streamlit as st

from i18n import t
from auth import (
    is_oauth_configured,
    is_logged_in,
    get_oauth_user,
    render_login_gate,
    render_logout_button,
)
from db.database import get_db
from db.user_helpers import get_user_by_google_id
from ui.theme_toggle import render_theme_toggle

st.set_page_config(
    page_title="User Settings",
    page_icon="👤",
    layout="wide",
)

render_theme_toggle()
render_logout_button()

st.title(t("settings_title"))
st.markdown("---")

if not is_oauth_configured():
    st.info(t("settings_oauth_required"))
    st.markdown(t("settings_oauth_configure"))
    st.stop()

if not render_login_gate():
    st.stop()

oauth = get_oauth_user()
if not oauth:
    st.error(t("settings_session_expired"))
    st.stop()

session = get_db()
current_user = get_user_by_google_id(session, oauth["google_id"])
google_name = oauth["name"] or oauth["email"] or "Unknown"
display_name = current_user.name if current_user else google_name

# --- Display name ---
st.subheader(t("settings_display_name"))

st.markdown(t("settings_display_desc"))

with st.form("display_name_form"):
    new_name = st.text_input(
        t("settings_display_name"),
        value=display_name,
        placeholder=t("settings_display_placeholder"),
        help=t("settings_display_help"),
    )
    submitted = st.form_submit_button(t("settings_save"))

if submitted:
    name_to_save = (new_name or google_name).strip()
    if not name_to_save:
        st.error(t("settings_name_empty"))
    else:
        try:
            if current_user:
                current_user.name = name_to_save
                session.commit()
                st.success(t("settings_updated", name=name_to_save))
            else:
                # Create user if they haven't voted yet
                from db.user_helpers import get_or_create_user_by_oauth

                get_or_create_user_by_oauth(
                    session,
                    google_id=oauth["google_id"],
                    email=oauth["email"],
                    name=name_to_save,
                )
                session.commit()
                st.success(t("settings_set", name=name_to_save))
            st.rerun()
        except Exception as e:
            session.rollback()
            st.error(t("settings_failed", error=str(e)))

st.markdown("---")
st.caption(t("settings_signed_in", email=oauth["email"]))

session.close()
