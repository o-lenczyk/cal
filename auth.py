"""OAuth authentication for Streamlit.

Uses Streamlit's built-in st.login() / st.user when [auth] is configured
in .streamlit/secrets.toml. Falls back to legacy name-based voting when not configured.
"""

from __future__ import annotations

import streamlit as st


def is_oauth_configured() -> bool:
    """Check if OAuth credentials are properly configured in secrets."""
    try:
        secrets = st.secrets
        auth = getattr(secrets, "auth", None)
        if auth is None:
            return False
        required = ["redirect_uri", "cookie_secret", "client_id", "client_secret", "server_metadata_url"]
        return all(getattr(auth, k, None) for k in required)
    except (FileNotFoundError, KeyError, AttributeError):
        return False


def is_logged_in() -> bool:
    """True if the user is logged in via OAuth."""
    if not is_oauth_configured():
        return False
    return getattr(st.user, "is_logged_in", False)


def get_oauth_user() -> dict | None:
    """Get current OAuth user info: name, email, sub (google_id). Returns None if not logged in."""
    if not is_logged_in():
        return None
    u = st.user
    return {
        "name": getattr(u, "name", None) or getattr(u, "email", "") or "Unknown",
        "email": getattr(u, "email", None) or "",
        "google_id": getattr(u, "sub", None) or "",
    }


def render_login_gate() -> bool:
    """
    If OAuth is configured and user is not logged in, show login button and return False.
    Otherwise return True (user can proceed).
    """
    if not is_oauth_configured():
        return True
    if is_logged_in():
        return True
    st.header("Log in to vote")
    st.markdown("Sign in with your Google account to submit and edit your votes.")
    st.button("Log in with Google", on_click=st.login, type="primary")
    return False


def render_logout_button():
    """Show a logout button in the sidebar when OAuth is enabled and user is logged in."""
    if is_oauth_configured() and is_logged_in():
        if st.sidebar.button("Log out", help="Sign out of your Google account"):
            st.logout()
