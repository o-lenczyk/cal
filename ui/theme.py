"""Theme persistence: query params for all users, DB for OAuth users."""
from __future__ import annotations

import streamlit as st


def _get_theme_from_db(google_id: str) -> str | None:
    """Get theme from AppSetting for OAuth user."""
    from db.database import get_db
    from db.models import AppSetting

    session = get_db()
    try:
        row = session.query(AppSetting).filter(AppSetting.key == f"theme_{google_id}").first()
        return row.value if row and row.value in ("light", "dark") else None
    finally:
        session.close()


def _save_theme_to_db(google_id: str, theme: str) -> None:
    """Save theme to AppSetting for OAuth user."""
    from db.database import get_db
    from db.models import AppSetting

    session = get_db()
    try:
        row = session.query(AppSetting).filter(AppSetting.key == f"theme_{google_id}").first()
        if row:
            row.value = theme
        else:
            session.add(AppSetting(key=f"theme_{google_id}", value=theme))
        session.commit()
    finally:
        session.close()


def get_theme() -> str:
    """
    Get persisted theme. Priority: query_params, DB (OAuth), session_state, default light.
    """
    # 1. Query params (survives refresh, works for anonymous)
    q = st.query_params.get("theme")
    if isinstance(q, list) and q:
        q = q[0]
    if q in ("light", "dark"):
        return q

    # 2. DB for OAuth users
    try:
        from auth import is_oauth_configured, is_logged_in, get_oauth_user

        if is_oauth_configured() and is_logged_in():
            oauth = get_oauth_user()
            if oauth and oauth.get("google_id"):
                t = _get_theme_from_db(oauth["google_id"])
                if t:
                    return t
    except Exception:
        pass

    # 3. Session state (ephemeral, resets on new tab)
    return st.session_state.get("theme", "light")


def set_theme(theme: str) -> None:
    """Persist theme: session_state, query_params, and DB for OAuth users."""
    st.session_state.theme = theme

    # Update URL so it survives refresh
    try:
        params = dict(st.query_params)
        params["theme"] = theme
        st.query_params.update(params)
    except Exception:
        pass

    # Save to DB for OAuth users
    try:
        from auth import is_oauth_configured, is_logged_in, get_oauth_user

        if is_oauth_configured() and is_logged_in():
            oauth = get_oauth_user()
            if oauth and oauth.get("google_id"):
                _save_theme_to_db(oauth["google_id"], theme)
    except Exception:
        pass


def apply_theme(theme: str) -> None:
    """Apply theme to Streamlit config."""
    try:
        config = getattr(st, "_config", None)
        if config and hasattr(config, "set_option"):
            config.set_option("theme.base", theme)
            if theme == "dark":
                config.set_option("theme.backgroundColor", "#0e1117")
                config.set_option("theme.secondaryBackgroundColor", "#262730")
                config.set_option("theme.textColor", "#fafafa")
            else:
                config.set_option("theme.backgroundColor", "#ffffff")
                config.set_option("theme.secondaryBackgroundColor", "#f0f2f6")
                config.set_option("theme.textColor", "#31333f")
    except Exception:
        pass
