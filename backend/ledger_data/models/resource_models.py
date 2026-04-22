"""
Database models for transaction domain.

Implements transaction management with support for journal entries,
transaction types, recipients, and memos using SQLAlchemy 2.0 style.
All timestamps are stored as timezone-aware UTC datetimes.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ..domain import (
    AccountCodeStr,
    Currency,
    JournalEntryBalance,
    TransactionTypePeriodicity,
)
from .utils import (
    AccountCodeType,
    TableName,
    utcnow,
)


# TODO look for errors in the relationships.
class RegistryMetadataMixin:
    """Mixin providing common registry metadata fields for all models.

    Adds ID, timestamps for creation/update, and soft-delete support.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )


class Base(DeclarativeBase):
    """Base class for all transaction models."""

    pass


transaction_recipient_association = Table(
    "transaction_recipient_associations",
    Base.metadata,
    Column(
        "transaction_id",
        ForeignKey(f"{TableName.TRANSACTIONS}.id"),
        primary_key=True,
    ),
    Column(
        "recipient_id",
        ForeignKey(f"{TableName.TRANSACTION_RECIPIENTS}.id"),
        primary_key=True,
    ),
)


class TransactionModel(Base, RegistryMetadataMixin):
    """
    Model representing a financial transaction registry.

    Attributes:
        id (int):
            Primary key - unique identifier.
        created_at (datetime):
            Timestamp when created (UTC).
        last_updated_at (datetime):
            Timestamp of last update (UTC).
        deactivated_at (datetime | None):
            Timestamp when soft-deleted (UTC), None if active.

        transaction_date (datetime):
            Date when the transaction occurred (UTC).
        description (str):
            Brief description of the transaction.
        reference (str):
            Unique reference code (invoice number, check number, etc).
        transaction_type_id (int):
            Foreign key to TransactionTypeModel.
        memo_id (int | None):
            Foreign key to Memo, nullable.

    """

    __tablename__ = TableName.TRANSACTIONS

    transaction_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reference: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    transaction_type_id: Mapped[int] = mapped_column(
        ForeignKey(f"{TableName.TRANSACTION_TYPES}.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    memo_id: Mapped[int | None] = mapped_column(
        ForeignKey(f"{TableName.MEMOS}.id"), nullable=True
    )

    # Relationships
    transaction_type: Mapped["TransactionTypeModel"] = relationship(
        lambda: TransactionTypeModel, back_populates="transactions"
    )
    ledger_entries: Mapped[list["LedgerEntryModel"]] = relationship(
        lambda: LedgerEntryModel, back_populates="transaction"
    )
    recipients: Mapped[list["TransactionRecipientModel"]] = relationship(
        lambda: TransactionRecipientModel,
        secondary=transaction_recipient_association,
        back_populates="transactions",
    )
    memo: Mapped["MemoModel | None"] = relationship(
        lambda: MemoModel, back_populates="transactions"
    )

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.reference}>"


class TransactionTypeModel(Base, RegistryMetadataMixin):
    """
    Model representing a transaction type or category.

    Defines classifications for transactions with support for
    hierarchical organization through the adjacency list pattern. Used
    to categorize and validate accounting transactions.

    Attributes:
        id (int):
            Primary key - unique identifier.
        created_at (datetime):
            Timestamp when created (UTC).
        last_updated_at (datetime):
            Timestamp of last update (UTC).
        deactivated_at (datetime | None):
            Timestamp when soft-deleted (UTC), None if active.

        name (str):
            The name of the transaction type.
        description (str):
            Detailed description of the transaction type.
        periodicity (TransactionTypePeriodicity):
            Expected frequency (MONTHLY, YEARLY), stored as enum.
        parent_type_id (int | None):
            Foreign key to parent TransactionTypeModel for hierarchical
            categorization.
    """

    __tablename__ = TableName.TRANSACTION_TYPES

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    periodicity: Mapped[TransactionTypePeriodicity] = mapped_column(
        Enum(TransactionTypePeriodicity), nullable=False
    )
    parent_type_id: Mapped[int | None] = mapped_column(
        ForeignKey(f"{__tablename__}.id"), nullable=True
    )

    # Relationships
    parent_type: Mapped["TransactionTypeModel | None"] = relationship(
        lambda: TransactionTypeModel,
        remote_side=lambda: [TransactionTypeModel.id],
        back_populates="child_types",
        foreign_keys=lambda: [TransactionTypeModel.parent_type_id],
    )
    child_types: Mapped[list["TransactionTypeModel"]] = relationship(
        lambda: TransactionTypeModel,
        back_populates="parent_type",
        foreign_keys=lambda: [TransactionTypeModel.parent_type_id],
    )
    transactions: Mapped[list["TransactionModel"]] = relationship(
        lambda: TransactionModel, back_populates="transaction_type"
    )

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}>"


class AccountModel(Base, RegistryMetadataMixin):
    """
    Model representing a financial account in the chart of accounts.

    Implements the fundamental accounting entity for tracking debits and
    credits. Accounts support hierarchical organization through
    parent-child relationships, allowing for account grouping and
    categorization (e.g., Assets > Current Assets > Cash). All accounts
    maintain an associated currency for multi-currency support.

    Attributes:
        id (int):
            Primary key - unique identifier.
        created_at (datetime):
            Timestamp when created (UTC).
        last_updated_at (datetime):
            Timestamp of last update (UTC).
        deactivated_at (datetime | None):
            Timestamp when soft-deleted (UTC), None if active.

        code (AccountCodeStr):
            Unique account code (e.g., "1000", "2100-A"). Enforced
            unique constraint at database level. Uses custom
            AccountCodeType to convert between string and AccountCodeStr
            domain type.
        currency (Currency):
            The currency denomination for this account (e.g., USD, EUR).
            Stored as enum to restrict to valid currency types.
        name (str):
            Human-readable account name (e.g., "Cash", "Accounts
            Payable").
        description (str):
            Extended description providing context and usage guidelines.
        parent_account_id (int | None):
            Foreign key to parent AccountModel for hierarchical
            categorization. Nullable to support top-level accounts
            without parents.

    Relationships:
        parent_account (AccountModel | None):
            Reference to the parent account if this account is a
            sub-account. None if this is a top-level account.
        child_accounts (list[AccountModel]):
            List of accounts that report to this account as their
            parent. Empty list if no sub-accounts exist.

    Database Table:
        accounts - Indexed on `code` (unique) and `parent_account_id`
                   for efficient lookups and hierarchy traversal.
    """

    __tablename__ = TableName.ACCOUNTS

    code: Mapped[AccountCodeStr] = mapped_column(
        AccountCodeType, unique=True, nullable=False, index=True
    )
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_account_id: Mapped[int | None] = mapped_column(
        ForeignKey(f"{__tablename__}.id"), nullable=True, index=True
    )

    # Relationships
    parent_account: Mapped["AccountModel | None"] = relationship(
        lambda: AccountModel,
        remote_side=lambda: [AccountModel.id],
        back_populates="child_accounts",
        foreign_keys=lambda: [AccountModel.parent_account_id],
    )
    child_accounts: Mapped[list["AccountModel"]] = relationship(
        lambda: AccountModel,
        back_populates="parent_account",
        foreign_keys=lambda: [AccountModel.parent_account_id],
    )
    ledger_entries: Mapped[list["LedgerEntryModel"]] = relationship(
        lambda: LedgerEntryModel, back_populates="account"
    )


class LedgerEntryModel(Base, RegistryMetadataMixin):
    """
    Model representing a single journal entry.

    Implements the double-entry bookkeeping principle. Each journal entry
    is one side of an accounting transaction, affecting a specific account
    by a specific amount (either as a debit or credit).

    Attributes:
        id (int):
            Primary key - unique identifier.
        created_at (datetime):
            Timestamp when created (UTC).
        last_updated_at (datetime):
            Timestamp of last update (UTC).
        deactivated_at (datetime | None):
            Timestamp when soft-deleted (UTC), None if active.

        transaction_id (int):
            Foreign key to Transaction.
        account_id (int):
            Foreign key to AccountModel (from account module).
        entry_balance (str):
            Type of entry (DEBIT or CREDIT), stored as enum.
        amount (Decimal):
            Monetary amount with precision for financial
            calculations.
    """

    __tablename__ = TableName.LEDGER_ENTRIES

    transaction_id: Mapped[int] = mapped_column(
        ForeignKey(f"{TableName.TRANSACTIONS}.id"), nullable=False
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey(f"{TableName.ACCOUNTS}.id"), nullable=False
    )
    entry_balance: Mapped[JournalEntryBalance] = mapped_column(
        Enum(JournalEntryBalance), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=2), nullable=False
    )

    # Relationships
    transaction: Mapped[TransactionModel] = relationship(
        TransactionModel, back_populates="ledger_entries"
    )
    account: Mapped[AccountModel] = relationship(
        AccountModel, back_populates="ledger_entries"
    )

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} {self.id}: "
            f"{self.entry_balance.value} {self.amount}>"
        )


class TransactionRecipientModel(Base, RegistryMetadataMixin):
    """
    Model representing a transaction recipient or counterparty.

    Represents individuals, organizations, or entities that participate
    in transactions. Supports hierarchical organization for complex
    structures.

    Attributes:
        id (int):
            Primary key - unique identifier.
        created_at (datetime):
            Timestamp when created (UTC).
        last_updated_at (datetime):
            Timestamp of last update (UTC).
        deactivated_at (datetime | None):
            Timestamp when soft-deleted (UTC), None if active.


        name (str):
            Name of the recipient or counterparty.
        description (str):
            Detailed description including identification info.
        parent_recipient_id (int | None):
            Foreign key to parent TransactionRecipientModel for
            hierarchical categorization.

    """

    __tablename__ = TableName.TRANSACTION_RECIPIENTS

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    parent_recipient_id: Mapped[int | None] = mapped_column(
        ForeignKey(f"{__tablename__}.id"), nullable=True, index=True
    )

    # Relationships
    parent_recipient: Mapped["TransactionRecipientModel | None"] = relationship(
        lambda: TransactionRecipientModel,
        remote_side=lambda: [TransactionRecipientModel.id],
        back_populates="child_recipients",
        foreign_keys=lambda: [TransactionRecipientModel.parent_recipient_id],
    )
    child_recipients: Mapped[list["TransactionRecipientModel"]] = relationship(
        lambda: TransactionRecipientModel,
        back_populates="parent_recipient",
        foreign_keys=lambda: [TransactionRecipientModel.parent_recipient_id],
    )
    transactions: Mapped[list["TransactionModel"]] = relationship(
        TransactionModel,
        secondary=transaction_recipient_association,
        back_populates="recipients",
    )

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}>"


class MemoModel(Base, RegistryMetadataMixin):
    """
    Model representing a formal memorandum document.

    Memos provide documentation, context, and authorization trails for
    transactions. Each memo contains communication and approval
    information.

    Attributes:
        id (int):
            Primary key - unique identifier.
        created_at (datetime):
            Timestamp when created (UTC).
        last_updated_at (datetime):
            Timestamp of last update (UTC).
        deactivated_at (datetime | None):
            Timestamp when soft-deleted (UTC), None if active.

        date (datetime):
            Date when the memo was created (UTC).
        receiver (str):
            Recipient name or title the memo is addressed to.
        emitter (str):
            Name or identifier of the memo author.
        subject (str):
            Subject line of the memo.
        message (str):
            Body content of the memo.
        authorized_by (str):
            Name or identifier of authorizing person.

    """

    __tablename__ = TableName.MEMOS

    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    receiver: Mapped[str] = mapped_column(String(255), nullable=False)
    emitter: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    authorized_by: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    transactions: Mapped[list["TransactionModel"]] = relationship(
        TransactionModel, back_populates="memo"
    )

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.subject}>"
