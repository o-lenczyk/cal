#!/usr/bin/env python3
"""
Import games from an xlsx file into the database.

Expected columns (names are case-insensitive, flexible):
  - BGG ID: bgg_id, bgg id, id
  - Name: name, title, game
  - Players: min_players + max_players, or a single "players" column (e.g. "2-4", "4")

Usage:
  python scripts/import_games_from_xlsx.py games.xlsx
  python scripts/import_games_from_xlsx.py games.xlsx --sheet "Sheet1"
  python scripts/import_games_from_xlsx.py games.xlsx --bgg-col "BGG ID" --name-col "Name" --players-col "Players"
"""
import argparse
import re
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from db.database import get_db
from db.models import Game


def normalize_col(name: str) -> str:
    """Normalize column name for matching."""
    return str(name).strip().lower().replace(" ", "_").replace("-", "_")


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find first matching column name (case-insensitive)."""
    cols = {normalize_col(c): c for c in df.columns}
    for cand in candidates:
        n = normalize_col(cand)
        if n in cols:
            return cols[n]
    return None


def parse_players(value) -> tuple[int, int]:
    """
    Parse player count from various formats.
    Returns (min_players, max_players).
    """
    if pd.isna(value):
        return (2, 6)  # default
    s = str(value).strip()
    if not s:
        return (2, 6)

    # "2-4" or "2–4" or "2 - 4"
    match = re.match(r"(\d+)\s*[-–—]\s*(\d+)", s)
    if match:
        return (int(match.group(1)), int(match.group(2)))

    # Single number
    match = re.match(r"(\d+)", s)
    if match:
        n = int(match.group(1))
        return (n, n)

    return (2, 6)


def import_from_xlsx(
    filepath: str,
    sheet: str | int = 0,
    bgg_col: str | None = None,
    name_col: str | None = None,
    min_col: str | None = None,
    max_col: str | None = None,
    players_col: str | None = None,
    dry_run: bool = False,
) -> int:
    """Import games from xlsx. Returns number of games added."""
    df = pd.read_excel(filepath, sheet_name=sheet, engine="openpyxl")

    # Resolve column names
    bgg = bgg_col or find_column(df, ["bgg_id", "bgg id", "id", "bggid"])
    name = name_col or find_column(df, ["name", "title", "game", "gamename"])
    min_p = min_col or find_column(df, ["min_players", "min players", "min", "minplayers"])
    max_p = max_col or find_column(df, ["max_players", "max players", "max", "maxplayers"])
    players = players_col or find_column(df, ["players", "player count", "playercount"])

    if not name:
        raise ValueError(
            f"Could not find name column. Available: {list(df.columns)}. "
            "Use --name-col to specify."
        )

    session = get_db()
    added = 0

    try:
        for _, row in df.iterrows():
            title = row[name]
            if pd.isna(title) or not str(title).strip():
                continue

            title = str(title).strip()

            # Parse min/max players
            if min_p and max_p and min_p in df.columns and max_p in df.columns:
                min_players = int(row[min_p]) if not pd.isna(row[min_p]) else 2
                max_players = int(row[max_p]) if not pd.isna(row[max_p]) else 6
            elif players and players in df.columns:
                min_players, max_players = parse_players(row[players])
            else:
                min_players, max_players = 2, 6

            min_players = max(1, min(min_players, 99))
            max_players = max(min_players, min(max_players, 99))

            # BGG ID
            bgg_id = None
            if bgg and bgg in df.columns and not pd.isna(row[bgg]):
                try:
                    bgg_id = int(row[bgg])
                except (ValueError, TypeError):
                    pass

            existing = session.query(Game).filter(Game.title == title).first()
            if existing:
                print(f"  ⏭️  Skipped (exists): {title}")
                continue

            if dry_run:
                print(f"  [dry-run] Would add: {title} ({min_players}-{max_players})" + (f" [BGG:{bgg_id}]" if bgg_id else ""))
                added += 1
                continue

            game = Game(
                title=title,
                min_players=min_players,
                max_players=max_players,
                bgg_id=bgg_id,
            )
            session.add(game)
            added += 1
            print(f"  ✅ Added: {title} ({min_players}-{max_players})")

        if not dry_run:
            session.commit()
    finally:
        session.close()

    return added


def main():
    parser = argparse.ArgumentParser(description="Import games from xlsx into the database")
    parser.add_argument("file", help="Path to xlsx file")
    parser.add_argument("--sheet", default=0, help="Sheet name or index (default: 0)")
    parser.add_argument("--bgg-col", help="Column name for BGG ID")
    parser.add_argument("--name-col", help="Column name for game name")
    parser.add_argument("--min-col", help="Column name for min players")
    parser.add_argument("--max-col", help="Column name for max players")
    parser.add_argument("--players-col", help="Column name for player count (e.g. '2-4')")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be added without writing")
    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    print(f"🎲 Importing games from {args.file}...\n")
    try:
        count = import_from_xlsx(
            args.file,
            sheet=args.sheet,
            bgg_col=args.bgg_col,
            name_col=args.name_col,
            min_col=args.min_col,
            max_col=args.max_col,
            players_col=args.players_col,
            dry_run=args.dry_run,
        )
        print(f"\nDone! {count} game(s) added.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
