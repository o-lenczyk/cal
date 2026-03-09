"""Next meeting date — stored in app_settings, default next Tuesday."""
from datetime import date, timedelta


def _next_tuesday(from_date: date | None = None) -> date:
    """Return the next Tuesday from given date (or today)."""
    d = from_date or date.today()
    # weekday: Monday=0, Tuesday=1, ...
    days_ahead = (1 - d.weekday()) % 7
    if days_ahead == 0:
        # Today is Tuesday — return next week's Tuesday
        days_ahead = 7
    return d + timedelta(days=days_ahead)


def get_next_meeting_date(session) -> date:
    """Get next meeting date from app_settings. Default: next Tuesday."""
    from db.models import AppSetting

    row = session.query(AppSetting).filter(AppSetting.key == "next_meeting_date").first()
    if row:
        try:
            return date.fromisoformat(row.value)
        except (ValueError, TypeError):
            pass
    return _next_tuesday()


def set_next_meeting_date(session, d: date) -> None:
    """Save next meeting date to app_settings."""
    from db.models import AppSetting

    row = session.query(AppSetting).filter(AppSetting.key == "next_meeting_date").first()
    if row:
        row.value = d.isoformat()
    else:
        session.add(AppSetting(key="next_meeting_date", value=d.isoformat()))
    session.commit()
