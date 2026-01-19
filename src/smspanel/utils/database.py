"""Database transaction utilities."""

from contextlib import contextmanager

from .. import db


@contextmanager
def db_transaction():
    """Handle database transactions with automatic rollback on errors.

    Yields:
        db.session for database operations

    Raises:
        Exception: Any exception raised during the transaction.
                    The transaction is automatically rolled back.

    Example:
        with db_transaction() as session:
            user = User(username="test")
            session.add(user)
            # Commit happens automatically on success
            # Rollback happens automatically on exception
    """
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
