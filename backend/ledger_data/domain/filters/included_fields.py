"""
Domain objects for queing objects with attachments.

This module contains the classes that define which data will be attached
in the query and in which format.
"""

from dataclasses import dataclass
from enum import Enum


class BaseIncludedFields:
    """
    Abstract base class for all 'included field' classes.
    """

    pass


@dataclass
class HierarchyIncludedFields(BaseIncludedFields):
    """
    Specifies which related fields to load for hierarchical entities.

    Attributes:
        include_adjacent_parent (InclusionType):
            Whether to load the parent entity
        include_all_parents (InclusionType):
            Whether to load the parent entity
        include_descendants (InclusionType):
    """

    include_adjacent_parent: "InclusionType"
    include_all_parents: "InclusionType"
    include_descendants: "InclusionType"


@dataclass
class TransactionIncludedFields(BaseIncludedFields):
    """
    Specifies which related fields to load for Transaction entities.

    Used to optimize queries by specifying which relationships should be
    eagerly loaded when querying for transactions.

    Attributes:
        include_transaction_type (InclusionType):
            Whether to load the associated TransactionType object.
        include_journal_entries (InclusionType):
            Whether to load the list of associated JournalEntry objects.
        include_recipients (InclusionType):
            Whether to load the list of associated TransactionRecipient
            objects.
        include_memo (InclusionType):
            Whether to load the associated Memo object.
    """

    include_transaction_type: "InclusionType"
    include_journal_entries: "InclusionType"
    include_recipients: "InclusionType"
    include_memo: "InclusionType"


@dataclass
class TransactionTypeIncludedFields(BaseIncludedFields):
    """
    Specifies which related fields to load for TransactionType entities.

    Attributes:
        hierarchy_inclusions (HierarchyIncludedFields):
            Object with information on what hierarchy related
            transaction types to load.
    """

    hierarchy_inclusions: HierarchyIncludedFields


@dataclass
class AccountIncludedFields(BaseIncludedFields):
    """
    Specifies which related fields to load for Account entities.

    Attributes:
        hierarchy_inclusions (HierarchyIncludedFields):
            Object with information on what hierarchy related
            accounts to load.
    """

    hierarchy_inclusions: HierarchyIncludedFields


@dataclass
class LedgerEntryIncludedFields(BaseIncludedFields):
    """
    Specifies which related fields to load for JournalEntry entities.

    Attributes:
        include_transaction (InclusionType):
            Whether to load the associated transaction object.
        include_account (InclusionType):
            Whether to load the associated Account object.
    """

    include_transaction: "InclusionType"
    include_account: "InclusionType"


@dataclass
class TransactionRecipientIncludedFields(BaseIncludedFields):
    """
    Specifies which related fields to load for TransactionType entities.

    Attributes:
        hierarchy_inclusions (HierarchyIncludedFields):
            Object with information on what hierarchy related
            transaction recipients to load.
    """

    hierarchy_inclusions: HierarchyIncludedFields


@dataclass
class MemoIncludedFields(BaseIncludedFields):
    """
    Specifies which related fields to load for Memo entities.

    Attributes:
        include_transaction (InclusionType):
            Whether to load the associated transaction object.
    """

    include_transaction: "InclusionType"


class InclusionType(Enum):
    """
    Enumeration of the types of inclusion that queried objects can have.
    """

    NONE = "none"
    OBJECT = "object"
    ID = "id"
