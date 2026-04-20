"""
Domain objects for queries with filters.

This module contains the classes that define how resurse queries can be
filtered.
"""

from dataclasses import dataclass

from utils import DateRange, DecimalRange

from ..entities import (
    AccountCodeStr,
    Currency,
    JournalEntryBalance,
    TransactionTypePeriodicity,
)


class BaseDataFilter:
    """
    Abstract base class for all data filters.
    """

    pass


@dataclass
class TransactionDataFilter(BaseDataFilter):
    """
    Filter for business data of Transaction entities.

    Allows filtering transactions by their reference numbers, associated
    transaction type, or participating recipients.

    Attributes:
        date_range ( DateRange | None):
            Filter by a range of dates (.g. from apr-1-2020 to
            oct-20-2021).
        references (set[str] | None):
            Filter by a set of reference codes (e.g., invoice numbers,
            check numbers). If None, reference filtering is not applied.
        transaction_type_ids (set[int] | None):
            Filter by a set of TransactionType IDs. If None, transaction
            type filtering is not applied.
        recipient_ids (set[int] | None):
            Filter by a set of recipient IDs. If None, recipient
            filtering is not applied.
        memo_ids (set[int] | None):
            Filter by a set of memos related to transactions using their
            ids.
    """

    date_range: DateRange | None = None
    references: set[str] | None = None
    transaction_type_ids: set[int] | None = None
    recipient_ids: set[int] | None = None
    memo_ids: set[int] | None = None


@dataclass
class TransactionTypeDataFilter(BaseDataFilter):
    """
    Filter for business data of TransactionType entities.

    Allows filtering transaction types by names, periodicity and parent
    type ids.

    Attributes:
        names (set[str] | None):
            Filter by a set of transaction type names.
        periodicities (set[TransactionTypePeriodicity] | None):
            Filter by a set of periodicities for transaction types.
        parent_type_ids (Set[int] | None):
            Filter by a set of parent TransactionType IDs. If None,
            parent type filtering is not applied.
    """

    names: set[str] | None = None
    periodicities: set[TransactionTypePeriodicity] | None = None
    parent_type_ids: set[int] | None = None


@dataclass
class AccountDataFilter(BaseDataFilter):
    """
    Filter for for business data of Account entities.

    Allows filtering accounts by codes, currencies, names and parent
    accounts.

    Attributes:
        codes (set[AccountCodeStr] | None):
            Filter by a set of Account codes. If None code filtering is
            not applied.
        currencies (set[Currency] | None):
            Filter by a set of currencies codes. If None currency
            filtering is not applied.
        names (set[str] | None):
            Filter by a set of names. If None name filtering is not
            applied.
        parent_account_ids (set[int] | None):
            Filter by a set of parent account ids. If None parent
            account filtering is not applied.
    """

    codes: set[AccountCodeStr] | None = None
    currencies: set[Currency] | None = None
    names: set[str] | None = None
    parent_account_ids: set[int] | None = None


@dataclass
class LedgerEntryDataFilter(BaseDataFilter):
    """
    Filter for business data of JournalEntry entities.

    Allows filtering journal entries by account ID, transaction ID, and
    amount range.

    Attributes:
        transaction_ids (Set[int] | None):
            Filter by a set of transaction IDs. If None, transaction
            filtering is not applied.
        account_ids (Set[int] | None):
            Filter by a set of account IDs. If None, account filtering
            is not applied.
        entry_balance (JournalEntryBalance | None):
            filter by credit or debit transactions.
        amount_range (DecimalRange | None):
            Filter by amount range (inclusive). If None, amount
            filtering is not applied.
    """

    transaction_ids: set[int] | None = None
    account_ids: set[int] | None = None
    entry_balance: JournalEntryBalance | None = None
    amount_range: DecimalRange | None = None


@dataclass
class TransactionRecipientDataFilter(BaseDataFilter):
    """
    Filter for business data of TransactionRecipient entities.

    Allows filtering recipients by names and parent recipient ids.

    Attributes:
        names (set[str] | None):
            Filter by aset of names.
        parent_recipient_ids (Set[int] | None):
            Filter by a set of parent TransactionRecipient IDs. If None,
            parent filtering is not applied.
    """

    names: set[str] | None = None
    parent_recipient_ids: set[int] | None = None


@dataclass
class MemoDataFilter(BaseDataFilter):
    """
    Filter for business data of Memo entities.

    Allows filtering by date, receivers, emmiters, subjects and
    authorizers.

    Attributes:

        date_range (DateRange | None):
            Filter by a date range.
        receivers (set[str] | None):
            Filter by receivers
        emmiters (set[str] | None):
            Filter by emmiters.
        subject (set[str] | None):
            Filter by subjects of the memos.
        authorizer (set[str] | None):
            Filter by memo authorizers.

    """

    date_range: DateRange | None
    receivers: set[str] | None
    emmiters: set[str] | None
    subject: set[str] | None
    authorizer: set[str] | None
