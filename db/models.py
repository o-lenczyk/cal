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


class Table(Base):
    """Physical table in the playroom (fixed furniture)."""

    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)  # seats (e.g. 4 or 6)
    sort_order = Column(Integer, nullable=False, default=0)

    # Relationships
    table_instances = relationship("TableInstance", back_populates="table", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Table(id={self.id}, name='{self.name}', capacity={self.capacity})>"


class TableInstance(Base):
    """Links a physical table to a game (this table is playing this game)."""
    __tablename__ = "table_instances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)

    # Relationships
    table = relationship("Table", back_populates="table_instances")
    game = relationship("Game", back_populates="table_instances")
    assigned_users = relationship("User", back_populates="assigned_table")

    __table_args__ = (UniqueConstraint("table_id", name="uq_table_instance_table_id"),)

    def __repr__(self):
        return f"<TableInstance(id={self.id}, table_id={self.table_id}, game_id={self.game_id})>"

    @property
    def current_player_count(self):
        return len(self.assigned_users)

    @property
    def capacity(self):
        """Max players = min(table capacity, game max_players)."""
        return min(self.table.capacity, self.game.max_players)

    @property
    def has_open_seats(self):
        return self.current_player_count < self.capacity


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    email = Column(String(255), nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_table_id = Column(Integer, ForeignKey("table_instances.id"), nullable=True)

    # Relationships
    assigned_table = relationship("TableInstance", back_populates="assigned_users")
    preferences = relationship("Preference", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', assigned_table_id={self.assigned_table_id})>"


class AppSetting(Base):
    """Key-value app settings (e.g. language)."""

    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(String(500), nullable=False)

    def __repr__(self):
        return f"<AppSetting(key='{self.key}', value='{self.value[:20]}...')>"


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
