from datetime import date
from sqlalchemy.orm import Session

from db.models import Game, Preference, TableInstance, Table, User


def calculate_scores(session: Session, meeting_date: date) -> list[dict]:
    """
    Calculate weighted scores for all games based on user preferences for the given meeting.
    Scoring: 1st choice = 3 points, 2nd choice = 2 points, 3rd choice = 1 point
    Returns a list of dicts: [{"game": Game, "score": int, "voter_count": int}, ...]
    """
    games = session.query(Game).all()
    results = []

    for game in games:
        preferences = (
            session.query(Preference)
            .join(Preference.user)
            .filter(Preference.game_id == game.id, User.meeting_date == meeting_date)
            .all()
        )

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


def select_games(session: Session, meeting_date: date, min_score: int = 1) -> list[Game]:
    """
    Select games that meet the minimum score threshold and have enough
    interested players to meet their min_players requirement.
    
    Automatically assigns selected games to physical tables (top games to first tables).
    
    Returns list of selected games.
    """
    scores = calculate_scores(session, meeting_date)
    selected = []

    for entry in scores:
        game = entry["game"]
        score = entry["score"]
        voter_count = entry["voter_count"]

        if score >= min_score and voter_count >= game.min_players:
            game.is_selected = True
            selected.append(game)
        else:
            game.is_selected = False

    # Assign selected games to physical tables (1st game → 1st table, etc.)
    physical_tables = session.query(Table).order_by(Table.sort_order).all()
    existing = {ti.table_id: ti for ti in session.query(TableInstance).all()}

    for i in range(min(len(selected), len(physical_tables))):
        tbl = physical_tables[i]
        game = selected[i]
        ti = existing.get(tbl.id)
        if ti:
            ti.game_id = game.id
        else:
            session.add(TableInstance(table_id=tbl.id, game_id=game.id))

    # Clear tables that no longer have a game (fewer selected games than tables)
    for i in range(len(selected), len(physical_tables)):
        tbl = physical_tables[i]
        ti = existing.get(tbl.id)
        if ti:
            session.delete(ti)

    session.commit()
    return selected
