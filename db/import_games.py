"""
Import games from Excel (.xlsx) into the database.

Expected columns (case-insensitive, flexible names):
- BGG ID: bgg_id, bgg id, id
- Name: name, title, game
- Players: min_players + max_players, or "Best With" / "Recommended With" (BGG format)
"""
import re
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from db.models import Game


def _find_column(df: pd.DataFrame, *candidates: str) -> str | None:
    """Find first matching column (case-insensitive)."""
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        key = cand.lower().strip()
        if key in cols_lower:
            return cols_lower[key]
    return None


def _parse_players(value) -> tuple[int, int]:
    """
    Parse player count from various formats.
    Returns (min_players, max_players).
    Handles: "2-4", "4", "Best with 4 players", "Recommended with 2–6 players", "3–6+"
    """
    if pd.isna(value):
        return 2, 6  # default
    s = str(value).strip()
    if not s:
        return 2, 6
    # Extract any "N-M" or "N–M" or "N-M+" pattern (e.g. from "Recommended with 2–6 players")
    m = re.search(r"(\d+)\s*[-–—]\s*(\d+)\+?", s)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return (min(lo, hi), max(lo, hi))
    # Single number (e.g. "Best with 4 players")
    m = re.search(r"(\d+)\s*(?:players?)?", s, re.I)
    if m:
        n = int(m.group(1))
        return (n, n)
    return 2, 6


def _load_game_sheet(path: Path) -> pd.DataFrame:
    """Load the first sheet that has game data (Name column). Prefer BGG_Games."""
    xl = pd.ExcelFile(path, engine="openpyxl")
    # Try BGG_Games first (common export name)
    if "BGG_Games" in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name="BGG_Games")
        if not df.empty and _find_column(df, "name", "title", "game"):
            return df
    # Try first sheet with a name column
    for name in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=name)
        if not df.empty and _find_column(df, "name", "title", "game"):
            return df
    # Fallback: first sheet
    return pd.read_excel(xl, sheet_name=0)


def import_from_xlsx(session: Session, path: str | Path) -> dict:
    """
    Import games from an xlsx file.

    Returns dict with: added, skipped, errors
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    df = _load_game_sheet(path)
    if df.empty:
        return {"added": 0, "skipped": 0, "errors": []}

    # Find columns
    bgg_col = _find_column(df, "bgg_id", "bgg id", "id")
    name_col = _find_column(df, "name", "title", "game")
    min_col = _find_column(df, "min_players", "min players", "min")
    max_col = _find_column(df, "max_players", "max players", "max")
    players_col = _find_column(
        df,
        "players", "player count", "player_count",
        "recommended with", "best with", "recommended_with", "best_with",
    )

    if not name_col:
        raise ValueError(
            "No name column found. Expected one of: name, title, game"
        )

    added = 0
    skipped = 0
    errors = []
    seen_in_batch = set()  # Skip duplicate titles within the same file

    for idx, row in df.iterrows():
        try:
            title = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
            if not title:
                continue

            # Skip if already in DB or already added in this batch
            if title in seen_in_batch:
                skipped += 1
                continue
            existing = session.query(Game).filter(Game.title == title).first()
            if existing:
                skipped += 1
                continue

            # BGG ID
            bgg_id = None
            if bgg_col and pd.notna(row[bgg_col]):
                try:
                    bgg_id = int(row[bgg_col])
                except (ValueError, TypeError):
                    pass

            # Min/max players
            if min_col and max_col:
                try:
                    min_p = int(row[min_col]) if pd.notna(row[min_col]) else 2
                    max_p = int(row[max_col]) if pd.notna(row[max_col]) else 6
                except (ValueError, TypeError):
                    min_p, max_p = 2, 6
            elif players_col:
                min_p, max_p = _parse_players(row[players_col])
            else:
                min_p, max_p = 2, 6

            min_p = max(1, min(min_p, max_p))
            max_p = max(min_p, max_p)

            game = Game(
                title=title,
                min_players=min_p,
                max_players=max_p,
                bgg_id=bgg_id,
            )
            session.add(game)
            seen_in_batch.add(title)
            added += 1

        except Exception as e:
            errors.append(f"Row {idx + 2}: {e}")

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    return {"added": added, "skipped": skipped, "errors": errors}
