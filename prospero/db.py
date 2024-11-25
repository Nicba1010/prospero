from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, PrimaryKeyConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import schedule

Base = declarative_base()


class ScheduleEntry(Base):
    __tablename__ = 'schedule_entries'

    start_datetime = Column(DateTime, nullable=False)
    title = Column(String, nullable=False)
    note = Column(String, nullable=True, default=None)
    location = Column(String, nullable=False)
    duration = Column(Integer, nullable=True, default=None)
    includes_break = Column(Boolean, default=False)
    buy_tickets_url = Column(String, nullable=True, default=None)

    __table_args__ = (
        PrimaryKeyConstraint('start_datetime', 'title', 'location', name='schedule_entry_pk'),
    )

    def __repr__(self):
        return (f"ScheduleEntry("
                f"start_datetime={self.start_datetime}, "
                f"title={self.title}, "
                f"note={self.note}, "
                f"location={self.location}, "
                f"duration={self.duration}, "
                f"includes_break={self.includes_break}, "
                f"buy_tickets_url={self.buy_tickets_url}"
                f")")

    def to_markdown(self):
        # Format the date and time
        date_str = self.start_datetime.strftime("%d. %B %Y (%A)")
        time_str = self.start_datetime.strftime("%H:%M")

        # Calculate end time if duration is provided
        end_time = ""
        if self.duration:
            end_datetime = self.start_datetime + timedelta(minutes=self.duration)
            end_time = f" - {end_datetime.strftime('%H:%M')}"

        # Build the markdown string
        md = f"📍 {self.location}\n\n"

        md += f"🎭*{self.title}*🎭\n"
        md += f"📅 {date_str}\n"
        md += f"⏰ {time_str}{end_time}\n"

        if self.duration:
            md += f"⏱️ {self.duration} minutes\n"

        if self.note:
            md += f"📝 {self.note}\n"

        if self.includes_break:
            md += "☕ Includes break\n"

        if self.buy_tickets_url:
            md += f"\n[🎫 Buy tickets 🎫]({self.buy_tickets_url})\n"

        return md.strip()

class SessionNotActiveError(Exception):
    """Raised when attempting to use database methods outside of context manager"""
    pass


class ScheduleDatabase:
    def __init__(self, db_uri: str = 'sqlite:///schedule.db'):
        self.engine = create_engine(db_uri)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = None

    def __enter__(self) -> 'ScheduleDatabase':
        logger.debug("Opening session...")
        self.session = self.Session()
        logger.debug("Session opened!")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.exception("Exception occurred within ScheduleDatabase context, rolling back transaction...", exc_val)
            self.session.rollback()
            logger.debug("Transaction rolled back successfully!")
        else:
            try:
                logger.debug("Committing transaction (exiting ScheduleDatabase context)...")
                self.session.commit()
                logger.debug("Transaction committed successfully!")
            except Exception as e:
                logger.exception("Exception occurred committing transaction, rolling back...", e)
                self.session.rollback()
                logger.debug("Transaction rolled back successfully!")

        logger.debug("Closing session...")
        self.session.close()
        logger.debug("Session closed!")
        self.session = None

    def _check_session(self) -> None:
        """Verify that session is active"""
        if self.session is None:
            raise SessionNotActiveError(
                "Database operation attempted outside of context manager. "
                "Use 'with ScheduleDatabase() as db:' to ensure proper session management."
            )

    def contains_entry(self, entry: ScheduleEntry) -> bool:
        """
        Check if an equivalent schedule entry already exists in the database.

        Raises:
            SessionNotActiveError: If called outside of context manager
        """
        self._check_session()
        existing = self.session.query(ScheduleEntry).filter(
            ScheduleEntry.start_datetime == entry.start_datetime,
            ScheduleEntry.title == entry.title,
            ScheduleEntry.location == entry.location
        ).first()
        return existing is not None

    def add_entry(self, entry: ScheduleEntry) -> None:
        """
        Add a new schedule entry to the database.

        Raises:
            SessionNotActiveError: If called outside of context manager
        """
        self._check_session()
        self.session.add(entry)


def main():
    # Test db path
    test_db_path: Path = Path('schedule.db')
    test_db_uri: str = f'sqlite:///{test_db_path.absolute()}'
    # Create some test entries
    now = datetime.now()

    entry1 = ScheduleEntry(
        start_datetime=now,
        title="Team Meeting",
        location="Room A"
    )

    entry2 = ScheduleEntry(
        start_datetime=now + timedelta(hours=1),
        title="Client Call",
        location="Room B",
        note="Quarterly Review",
        duration=60
    )

    # Duplicate of entry1 to test contains_entry
    entry3 = ScheduleEntry(
        start_datetime=now,
        title="Team Meeting",
        location="Room A"
    )

    # Test normal operation
    print("Testing normal operation...")
    with ScheduleDatabase(db_uri=test_db_uri) as db:
        # Try adding entry1
        if not db.contains_entry(entry1):
            db.add_entry(entry1)
            print(f"Added {entry1}")
        else:
            print(f"Entry already exists: {entry1}")

        # Try adding entry2
        if not db.contains_entry(entry2):
            db.add_entry(entry2)
            print(f"Added {entry2}")
        else:
            print(f"Entry already exists: {entry2}")

        # Try adding duplicate entry3
        if not db.contains_entry(entry3):
            db.add_entry(entry3)
            print(f"Added {entry3}")
        else:
            print(f"Entry already exists: {entry3}")
    if test_db_path.exists():
        test_db_path.unlink()

    # Test error handling for operation outside context manager
    print("\nTesting error handling...")
    try:
        db = ScheduleDatabase(db_uri=test_db_uri)
        db.contains_entry(entry1)
    except SessionNotActiveError as e:
        print(f"Caught expected error: {e}")
    if test_db_path.exists():
        test_db_path.unlink()


if __name__ == "__main__":
    main()
