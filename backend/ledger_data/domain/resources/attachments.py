# TODO add and correct documentation for this module.
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Sequence, TypeGuard  # noqa: F401

from .data_classes import JournalEntryBalance
from .persistence import Persisted

if TYPE_CHECKING:
    from .resource_classes import (
        Account,
        BaseResource,
        LedgerEntry,
        Memo,
        Transaction,
        TransactionRecipient,
        TransactionType,
    )


# TODO should include a description of how do attachments behave and why
# attachments should not have attachments.
class BaseAttachment:
    """Base class for attachment classes.

    An attachment is a data structure that is related to another one.
    E.g. if a transaction data is requested, the ledger entries can be
    attachments in that request included through an ItemsAttachment
    object or a JournalEntryAttachment object.
    """

    pass


@dataclass
class HierarchyAttachment[T: BaseResource[Any, Any, None]](BaseAttachment):
    """
    This attachment class includes data about the hierarchy of an object
    as in adjacency list structures.
    E.g. A 'Cost' account can have children like 'Office cost' and
    'Operational costs'.
    """

    parent: T | None
    parents: Sequence[T]
    children: Sequence[T]


@dataclass
class TransactionAttachment[
    T_Type: (TransactionType, None),
    T_Memo: (Memo, None),
    T_Entries: (Sequence[LedgerEntry[Persisted, None]], Sequence[int], None),
    T_Recipients: (
        Sequence[TransactionRecipient[Persisted, None]],
        Sequence[int],
        None,
    ),
](BaseAttachment):
    transaction_type: T_Type
    memo: T_Memo
    ledger_entries: T_Entries
    recipients: T_Recipients

    def __post__init__(self):
        if self._is_entries_seq(self.ledger_entries):
            debit = Decimal()
            credit = Decimal()

            for entry in self.ledger_entries:
                if entry.data.entry_balance == JournalEntryBalance.CREDIT:
                    credit += entry.data.amount
                elif entry.data.entry_balance == JournalEntryBalance.DEBIT:
                    debit += entry.data.amount

            if credit != debit:
                raise ValueError("Transaction is not balanced.")

    @staticmethod
    def _is_entries_seq(val: Any) -> TypeGuard[Sequence[LedgerEntry]]:
        return isinstance(val, Sequence) and isinstance(val[0], LedgerEntry)


@dataclass
class TransactionTypeAttachment(BaseAttachment):
    hierarchy: HierarchyAttachment[TransactionType[Persisted, None]]


@dataclass
class AccountAttachment(BaseAttachment):
    hierarchy: HierarchyAttachment[Account[Persisted, None]]


@dataclass
class LedgerEntryAttachement(BaseAttachment):
    transaction: Transaction
    account: Account


@dataclass
class TransactionRecipientAttachment(BaseAttachment):
    hierarchy: HierarchyAttachment[TransactionRecipient[Persisted, None]]


@dataclass
class MemoAttachment(BaseAttachment):
    transactions: Sequence[Transaction]


type Attachment = BaseAttachment | None

type TransactionAttachable = TransactionAttachment | None

type TransactionTypeAttachable = TransactionTypeAttachment | None

type AccountAttachable = AccountAttachment | None

type LedgerEntryAttacheable = LedgerEntryAttachement | None

type TransactionRecipientAttachable = TransactionRecipientAttachment | None

type MemoAttachable = MemoAttachment | None
