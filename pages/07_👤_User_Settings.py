"""User Settings — change display name and account preferences."""
import streamlit as st

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

st.title("👤 User Settings")
st.markdown("---")

if not is_oauth_configured():
    st.info("User settings are available when you log in with Google.")
    st.markdown(
        "Configure OAuth in `.streamlit/secrets.toml` to enable account features. "
        "Without OAuth, your name is entered when voting."
    )
    st.stop()

if not render_login_gate():
    st.stop()

oauth = get_oauth_user()
if not oauth:
    st.error("Session expired. Please log in again.")
    st.stop()

session = get_db()
current_user = get_user_by_google_id(session, oauth["google_id"])
google_name = oauth["name"] or oauth["email"] or "Unknown"
display_name = current_user.name if current_user else google_name

# --- Display name ---
st.subheader("Display name")

st.markdown(
    "This name is shown when you vote and in the \"Who has voted\" list. "
    "By default it uses your Google account name."
)

with st.form("display_name_form"):
    new_name = st.text_input(
        "Display name",
        value=display_name,
        placeholder="Enter your preferred display name...",
        help="Leave blank to use your Google account name.",
    )
    submitted = st.form_submit_button("Save")

if submitted:
    name_to_save = (new_name or google_name).strip()
    if not name_to_save:
        st.error("Display name cannot be empty.")
    else:
        try:
            if current_user:
                current_user.name = name_to_save
                session.commit()
                st.success(f"Display name updated to **{name_to_save}**.")
            else:
                # Create user if they haven't voted yet
                from db.user_helpers import get_or_create_user_by_oauth

                user = get_or_create_user_by_oauth(
                    session,
                    google_id=oauth["google_id"],
                    email=oauth["email"],
                    name=name_to_save,
                )
                session.commit()
                st.success(f"Display name set to **{name_to_save}**.")
            st.rerun()
        except Exception as e:
            session.rollback()
            st.error(f"Failed to save: {e}")

st.markdown("---")
st.caption(f"Signed in as **{oauth['email']}** (Google)")

session.close()
