# TODO add and correct documentation for this module.
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Sequence  # noqa: F401

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
    E.g. if a transaction data is requested, the journal entries can be
    attachments in that request included through an ItemsAttachment
    object or a JournalEntryAttachment object.
    """

    pass


type Attachment = BaseAttachment | None


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
    T_Entries: (LedgerEntry, int, None),
    T_Recipients: (TransactionRecipient, int, None),
](BaseAttachment):
    transaction_type: T_Type
    memo: T_Memo
    journal_entries: Sequence[T_Entries]
    recipients: Sequence[T_Recipients]


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


# TODO add transaction attachments.
# TODO after that, correct the documentation of the Memo in entities.py
class MemoAttachment(BaseAttachment):
    pass
