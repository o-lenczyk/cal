"""
Seed script to populate the database with sample games for testing.
Run with: python -m db.seed
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.database import get_db
from db.models import Game


SAMPLE_GAMES = [
    {"title": "Catan", "min_players": 3, "max_players": 4},
    {"title": "Ticket to Ride", "min_players": 2, "max_players": 5},
    {"title": "Carcassonne", "min_players": 2, "max_players": 5},
    {"title": "Pandemic", "min_players": 2, "max_players": 4},
    {"title": "7 Wonders", "min_players": 3, "max_players": 7},
    {"title": "Azul", "min_players": 2, "max_players": 4},
    {"title": "Wingspan", "min_players": 1, "max_players": 5},
    {"title": "Splendor", "min_players": 2, "max_players": 4},
    {"title": "Codenames", "min_players": 4, "max_players": 8},
    {"title": "Dixit", "min_players": 3, "max_players": 8},
]


def seed_games():
    session = get_db()

    added = 0
    for game_data in SAMPLE_GAMES:
        existing = session.query(Game).filter(Game.title == game_data["title"]).first()
        if not existing:
            game = Game(**game_data)
            session.add(game)
            added += 1
            print(f"  ✅ Added: {game_data['title']}")
        else:
            print(f"  ⏭️  Skipped (exists): {game_data['title']}")

    session.commit()
    session.close()
    print(f"\nDone! {added} game(s) added.")


if __name__ == "__main__":
    print("🎲 Seeding database with sample games...\n")
    seed_games()
