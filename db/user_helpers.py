"""User lookup and creation helpers for OAuth and legacy flows."""

from sqlalchemy.orm import Session

from db.models import User


def get_user_by_google_id(session: Session, google_id: str) -> User | None:
    """Find a user by their OAuth google_id (sub claim)."""
    return session.query(User).filter(User.google_id == google_id).first()


def get_user_by_name(session: Session, name: str) -> User | None:
    """Find a user by display name (legacy flow)."""
    return session.query(User).filter(User.name == name).first()


def get_or_create_user_by_oauth(
    session: Session,
    *,
    google_id: str,
    email: str,
    name: str,
) -> User:
    """
    Get existing user by google_id, or create a new one.
    Preserves existing user's display name (set in User Settings); only updates email.
    For new users, uses name from OAuth.
    """
    user = get_user_by_google_id(session, google_id)
    if user:
        user.email = email or user.email
        return user
    user = User(google_id=google_id, email=email or None, name=name)
    session.add(user)
    session.flush()
    return user
