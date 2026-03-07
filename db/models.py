from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bgg_id = Column(Integer, nullable=True, index=True)  # BoardGameGeek ID (optional)
    title = Column(String(255), nullable=False, unique=True)
    min_players = Column(Integer, nullable=False, default=2)
    max_players = Column(Integer, nullable=False, default=6)
    is_selected = Column(Boolean, default=False)

    # Relationships
    table_instances = relationship("TableInstance", back_populates="game", cascade="all, delete-orphan")
    preferences = relationship("Preference", back_populates="game", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Game(id={self.id}, title='{self.title}', players={self.min_players}-{self.max_players})>"


class TableInstance(Base):
    __tablename__ = "table_instances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    table_number = Column(Integer, nullable=False, default=1)

    # Relationships
    game = relationship("Game", back_populates="table_instances")
    assigned_users = relationship("User", back_populates="assigned_table")

    __table_args__ = (
        UniqueConstraint("game_id", "table_number", name="uq_game_table_number"),
    )

    def __repr__(self):
        return f"<TableInstance(id={self.id}, game_id={self.game_id}, table_number={self.table_number})>"

    @property
    def current_player_count(self):
        return len(self.assigned_users)

    @property
    def has_open_seats(self):
        return self.current_player_count < self.game.max_players


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_table_id = Column(Integer, ForeignKey("table_instances.id"), nullable=True)

    # Relationships
    assigned_table = relationship("TableInstance", back_populates="assigned_users")
    preferences = relationship("Preference", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', assigned_table_id={self.assigned_table_id})>"


class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    rank = Column(Integer, nullable=False)

    # Relationships
    user = relationship("User", back_populates="preferences")
    game = relationship("Game", back_populates="preferences")

    __table_args__ = (
        CheckConstraint("rank IN (1, 2, 3)", name="ck_preference_rank"),
        UniqueConstraint("user_id", "rank", name="uq_user_rank"),
        UniqueConstraint("user_id", "game_id", name="uq_user_game"),
    )

    def __repr__(self):
        return f"<Preference(user_id={self.user_id}, game_id={self.game_id}, rank={self.rank})>"
