"""Internationalization — translations and language selection."""
from i18n.translations import TRANSLATIONS


def get_language() -> str:
    """Get current app language from database. Default 'en'."""
    from db.database import get_db
    from db.models import AppSetting

    session = get_db()
    try:
        row = session.query(AppSetting).filter(AppSetting.key == "language").first()
        return row.value if row else "en"
    finally:
        session.close()


def set_language(lang: str) -> None:
    """Set app language in database."""
    from db.database import get_db
    from db.models import AppSetting

    session = get_db()
    try:
        row = session.query(AppSetting).filter(AppSetting.key == "language").first()
        if row:
            row.value = lang
        else:
            session.add(AppSetting(key="language", value=lang))
        session.commit()
    finally:
        session.close()


def t(key: str, **kwargs) -> str:
    """Translate key to current language. Falls back to English."""
    lang = get_language()
    strings = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    s = strings.get(key, key)
    if kwargs:
        s = s.format(**kwargs)
    return s


LANGUAGES = {"en": "English", "pl": "Polski"}
