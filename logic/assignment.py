from datetime import date
from sqlalchemy.orm import Session

from db.models import User, Preference, TableInstance, Game, Table


def assign_players(session: Session, meeting_date: date) -> dict:
    """
    Assign players to tables using First-Come, First-Served (FCFS) approach.
    Only processes users for the given meeting_date.
    """
    # Reset assignments for users of this meeting only
    session.query(User).filter(User.meeting_date == meeting_date).update(
        {User.assigned_table_id: None}
    )
    session.flush()

    users = (
        session.query(User)
        .filter(User.meeting_date == meeting_date, User.submitted_at.isnot(None))
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

            # Get table instances for this game, sorted by physical table order
            tables = (
                session.query(TableInstance)
                .filter(TableInstance.game_id == game.id)
                .join(TableInstance.table)
                .order_by(Table.sort_order.asc())
                .all()
            )

            for table in tables:
                current_count = (
                    session.query(User)
                    .filter(
                        User.assigned_table_id == table.id,
                        User.meeting_date == meeting_date,
                    )
                    .count()
                )

                effective_capacity = min(table.table.capacity, game.max_players)
                if current_count < effective_capacity:
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


def get_available_tables(session: Session, meeting_date: date) -> list[dict]:
    """
    Get all tables that still have open seats.
    Used for the fallback mechanism for unassigned players.
    
    Returns list of dicts: [{"table": TableInstance, "game": Game, "open_seats": int}, ...]
    """
    tables = (
        session.query(TableInstance)
        .join(TableInstance.game)
        .join(TableInstance.table)
        .filter(Game.is_selected == True)
        .order_by(Table.sort_order)
        .all()
    )

    available = []
    for table in tables:
        current_count = (
            session.query(User)
            .filter(
                User.assigned_table_id == table.id,
                User.meeting_date == meeting_date,
            )
            .count()
        )
        capacity = min(table.table.capacity, table.game.max_players)
        open_seats = capacity - current_count

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

    effective_capacity = min(table.table.capacity, table.game.max_players)
    if current_count >= effective_capacity:
        return False

    user.assigned_table_id = table.id
    session.commit()
    return True
