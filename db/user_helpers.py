"""User lookup and creation helpers for OAuth and legacy flows."""

from datetime import date
from sqlalchemy.orm import Session

from db.models import User


def get_any_user_by_google_id(session: Session, google_id: str) -> User | None:
    """Get any user with this google_id (for display name in Settings)."""
    return session.query(User).filter(User.google_id == google_id).first()


def get_user_by_google_id(session: Session, google_id: str, meeting_date: date) -> User | None:
    """Find a user by OAuth google_id and meeting date."""
    return (
        session.query(User)
        .filter(User.google_id == google_id, User.meeting_date == meeting_date)
        .first()
    )


def get_user_by_name(session: Session, name: str, meeting_date: date) -> User | None:
    """Find a user by display name and meeting date (legacy flow)."""
    return (
        session.query(User)
        .filter(User.name == name, User.meeting_date == meeting_date)
        .first()
    )


def get_or_create_user_by_oauth(
    session: Session,
    *,
    google_id: str,
    email: str,
    name: str,
    meeting_date: date,
) -> User:
    """
    Get existing user by google_id and meeting_date, or create a new one.
    Preserves existing user's display name; only updates email.
    """
    user = get_user_by_google_id(session, google_id, meeting_date)
    if user:
        user.email = email or user.email
        return user
    # Use name from existing user with same google_id if available (display name from Settings)
    existing = get_any_user_by_google_id(session, google_id)
    display_name = existing.name if existing else name
    user = User(google_id=google_id, email=email or None, name=display_name, meeting_date=meeting_date)
    session.add(user)
    session.flush()
    return user
