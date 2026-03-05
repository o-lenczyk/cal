from sqlalchemy.orm import Session

from db.models import User, Preference, TableInstance, Game


def assign_players(session: Session) -> dict:
    """
    Assign players to tables using First-Come, First-Served (FCFS) approach.
    
    Users are sorted by submission timestamp (earliest first).
    For each user, the system tries their 1st choice, then 2nd, then 3rd.
    If multiple table instances exist for a game, they are filled in order.
    
    Returns a dict with assignment results:
    {
        "assigned": [(user, table_instance), ...],
        "unassigned": [user, ...],
    }
    """
    # Reset all assignments first
    session.query(User).update({User.assigned_table_id: None})
    session.flush()

    # Get all users sorted by submission time (FCFS)
    users = (
        session.query(User)
        .filter(User.submitted_at.isnot(None))
        .order_by(User.submitted_at.asc())
        .all()
    )

    assigned = []
    unassigned = []

    for user in users:
        # Get user's preferences sorted by rank (1, 2, 3)
        preferences = (
            session.query(Preference)
            .filter(Preference.user_id == user.id)
            .order_by(Preference.rank.asc())
            .all()
        )

        was_assigned = False

        for pref in preferences:
            game = session.query(Game).get(pref.game_id)

            # Skip if game wasn't selected
            if not game or not game.is_selected:
                continue

            # Get table instances for this game, sorted by table number
            tables = (
                session.query(TableInstance)
                .filter(TableInstance.game_id == game.id)
                .order_by(TableInstance.table_number.asc())
                .all()
            )

            for table in tables:
                # Count current players at this table
                current_count = (
                    session.query(User)
                    .filter(User.assigned_table_id == table.id)
                    .count()
                )

                if current_count < game.max_players:
                    user.assigned_table_id = table.id
                    session.flush()
                    assigned.append((user, table))
                    was_assigned = True
                    break

            if was_assigned:
                break

        if not was_assigned:
            unassigned.append(user)

    session.commit()

    return {
        "assigned": assigned,
        "unassigned": unassigned,
    }


def get_available_tables(session: Session) -> list[dict]:
    """
    Get all tables that still have open seats.
    Used for the fallback mechanism for unassigned players.
    
    Returns list of dicts: [{"table": TableInstance, "game": Game, "open_seats": int}, ...]
    """
    tables = (
        session.query(TableInstance)
        .join(Game)
        .filter(Game.is_selected == True)
        .order_by(Game.title, TableInstance.table_number)
        .all()
    )

    available = []
    for table in tables:
        current_count = (
            session.query(User)
            .filter(User.assigned_table_id == table.id)
            .count()
        )
        open_seats = table.game.max_players - current_count

        if open_seats > 0:
            available.append({
                "table": table,
                "game": table.game,
                "open_seats": open_seats,
                "current_count": current_count,
            })

    return available


def manually_assign_player(session: Session, user_id: int, table_id: int) -> bool:
    """
    Manually assign a player to a specific table (fallback mechanism).
    
    Returns True if successful, False if table is full.
    """
    user = session.query(User).get(user_id)
    table = session.query(TableInstance).get(table_id)

    if not user or not table:
        return False

    current_count = (
        session.query(User)
        .filter(User.assigned_table_id == table.id)
        .count()
    )

    if current_count >= table.game.max_players:
        return False

    user.assigned_table_id = table.id
    session.commit()
    return True
