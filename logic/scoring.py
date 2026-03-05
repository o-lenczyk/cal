from sqlalchemy.orm import Session
from sqlalchemy import func

from db.models import Game, Preference, TableInstance


def calculate_scores(session: Session) -> list[dict]:
    """
    Calculate weighted scores for all games based on user preferences.
    
    Scoring: 1st choice = 3 points, 2nd choice = 2 points, 3rd choice = 1 point
    Formula: Score = 3×n1 + 2×n2 + 1×n3
    
    Returns a list of dicts: [{"game": Game, "score": int, "voter_count": int}, ...]
    """
    games = session.query(Game).all()
    results = []

    for game in games:
        preferences = session.query(Preference).filter(Preference.game_id == game.id).all()

        n1 = sum(1 for p in preferences if p.rank == 1)
        n2 = sum(1 for p in preferences if p.rank == 2)
        n3 = sum(1 for p in preferences if p.rank == 3)

        score = 3 * n1 + 2 * n2 + 1 * n3
        voter_count = n1 + n2 + n3

        results.append({
            "game": game,
            "score": score,
            "voter_count": voter_count,
            "n1": n1,
            "n2": n2,
            "n3": n3,
        })

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def select_games(session: Session, min_score: int = 1) -> list[Game]:
    """
    Select games that meet the minimum score threshold and have enough
    interested players to meet their min_players requirement.
    
    Creates initial table instances for selected games.
    
    Returns list of selected games.
    """
    scores = calculate_scores(session)
    selected = []

    for entry in scores:
        game = entry["game"]
        score = entry["score"]
        voter_count = entry["voter_count"]

        if score >= min_score and voter_count >= game.min_players:
            game.is_selected = True
            selected.append(game)

            # Create at least one table instance if none exists
            existing_tables = (
                session.query(TableInstance)
                .filter(TableInstance.game_id == game.id)
                .count()
            )
            if existing_tables == 0:
                table = TableInstance(game_id=game.id, table_number=1)
                session.add(table)
        else:
            game.is_selected = False

    session.commit()
    return selected
