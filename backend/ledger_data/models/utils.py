from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    String,
    TypeDecorator,
)

from ..domain import AccountCodeStr


def utcnow():
    """Get current time as timezone-aware UTC datetime.

    Returns:
        datetime: Current time in UTC timezone.
    """
    return datetime.now(timezone.utc)


class AccountCodeType(TypeDecorator):
    """
    Bridge between the database String and the AccountCodeStr value object.
    """

    impl = String(64)
    cache_ok = True

    # When saving to the DB
    def process_bind_param(self, value, dialect) -> str | None:
        return str(value) if value is not None else None

    # When loading from the DB
    def process_result_value(self, value, dialect) -> AccountCodeStr | None:
        return AccountCodeStr(value) if value is not None else None


class TableName(Enum):
    TRANSACTIONS = "transactions"
    TRANSACTION_TYPES = "transaction_types"
    ACCOUNTS = "accounts"
    LEDGER_ENTRIES = "ledger_entries"
    TRANSACTION_RECIPIENTS = "transaction_recipients"
    MEMOS = "memos"
