# TODO module docstring not revised yet
"""
Domain Entities for the Accounting System.

This module provides the "Resource" layer of the domain, which extends pure
data structures with technical metadata. Using Python generics, these classes
bundle core business data (BaseData) with persistence-specific information
(Persistence) and optional associated files (Attachment).

This approach allows the domain layer to remain agnostic of specific
database implementations while providing a consistent interface for
handling identified resources throughout the application lifecycle.

Main Components:
    * BaseResource: The generic base class for all identified domain resources.
    * Accounting Entities: Transaction, JournalEntry, and Account.
    * Stakeholder Entities: TransactionRecipient and TransactionType.
"""

from dataclasses import dataclass

from .attachments import (
    AccountAttachment,
    Attachment,
    LedgerEntryAttachement,
    MemoAttachment,
    TransactionAttachment,
    TransactionRecipientAttachment,
    TransactionTypeAttachment,
)
from .data_classes import (
    AccountData,
    BaseData,
    LedgerEntryData,
    MemoData,
    TransactionData,
    TransactionRecipientData,
    TransactionTypeData,
)
from .persistence import Persistence

# ============================================================================
# Resource Classes
# ============================================================================


@dataclass
class BaseResource[D: BaseData, P: Persistence, A: Attachment]:
    """
    A generic container representing a complete domain entity with
    metadata.

    This class bridges the gap between pure domain data and system-level
    requirements. It encapsulates the core business data, its
    persistence metadata (such as primary keys and timestamps), and any
    associated external attachments.

    Attributes:
        data (BaseData):
            The core domain data entity extending BaseData.
        persistence_data (Persistence):
            Metadata object related to the storage layer, such as unique
            identifiers or record versioning.
        attachments (Attachment):
            A collection of resources linked to this entity (e.g. ledger
            movements attached to a transaction).
    """

    data: D
    persistence_data: P
    attachments: A


class Transaction[P: Persistence, A: (TransactionAttachment, None)](
    BaseResource[TransactionData, P, A]
):
    """
    A full domain representation of a financial transaction.

    Combines the transaction's business state (TransactionData) with its
    unique identity, lifecycle metadata, and optional resources
    attached.

    Attributes:
        data (TransactionData):
            The header-level financial data.
        persistence_data (Persistence):
            Identity and audit metadata from the storage layer.
        attachments (TransactionAttachment, None):
            Object containing optional data on the transaction's type,
            memo, journal entries and recipients
    """

    pass


class TransactionType[P: Persistence, A: (TransactionTypeAttachment, None)](
    BaseResource[TransactionTypeData, P, A]
):
    """
    A full domain representation of a transaction category.

    Attributes:
        data (TransactionTypeData):
            The categorization data. Includes name description and a
            reference to the parent
        persistence_data (Persistence):
            Identity and registry metadata from the storage layer.
        attachments (TransactionTypeAttachment):
            Object containing optional attachments related to the
            hierarchy of transaction types like parent types or children
            types.
    See the `TransactionTypeData` and `TransactionTypeAttachment`
    classes  documentation for more details on the data this class
    carries and what it represents.
    """

    pass


class Account[P: Persistence, A: (AccountAttachment, None)](
    BaseResource[AccountData, P, A]
):
    """
    A full domain representation of a General Ledger account.

    Attributes:
        data (AccountData):
            The core account details, including code, name, and
            currency.
        persistence_data (Persistence):
            Identity and registry metadata from the storage layer.
        attachments (AccountAttachment):
            Optional Attachments related to the hierarchy of accounts
            like parent accounts or children accounts.

    See the `AccountData` and `AccountAttachment` classes documentation
    for more details on the data this class carries and what it
    represents.
    """

    pass


class LedgerEntry[P: Persistence, A: (LedgerEntryAttachement, None)](
    BaseResource[LedgerEntryData, P, A]
):
    """
    A full domain representation of an individual ledger movement.

    Attributes:
        data (JournalEntryData):
            The financial data including account, direction (balance),
            and amount.
        persistence_data (Persistence):
            Identity and registry metadata from the storage layer.
        attachments (LedgerEntryAttachement):
            Optional Attachments related to the account and the
            transaction of the ledger movement.

    See the `LedgerEntry` and `LedgerEntryAttachement` classes
    documentation for more details on the data this class carries and
    what it represents.
    """

    pass


class TransactionRecipient[
    P: Persistence,
    A: (TransactionRecipientAttachment, None),
](BaseResource[TransactionRecipientData, P, A]):
    """
    A full domain representation of a transaction recipient entity.

    Attributes:
        data (TransactionRecipientData):
            The business data for the party involved in a transaction
            (name, description, hierarchy).
        persistence_data (P):
            Identity and registry metadata from the storage layer.
        attachments (TransactionRecipientAttachment):
            Optional Attachments related to hierarchy of recipients like
            parent recipients or children recipients.
    """

    pass


class Memo[P: Persistence, A: (MemoAttachment, None)](
    BaseResource[MemoData, P, A]
):
    """
    A full domain representation of a memorandum.

    Attributes:
        data (MemoData):
            The memo data including date, who wrote it, to whom is
            directed the memo, message etc.
        persistence_data (P):
            Identity and registry metadata from the storage layer.
        attachments (A):
            Optional Attachments. Memos don't include attachments yet

    See the `LedgerEntry` and `LedgerEntryAttachement` classes
    documentation for more details on the data this class carries and
    what it represents.
    """

    pass


# ============================================================================
# Persistence Classes
# ============================================================================
