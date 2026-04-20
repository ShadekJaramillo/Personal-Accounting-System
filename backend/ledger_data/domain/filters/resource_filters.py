from dataclasses import dataclass

from .data_filters import (
    AccountDataFilter,
    BaseDataFilter,
    LedgerEntryDataFilter,
    MemoDataFilter,
    TransactionDataFilter,
    TransactionRecipientDataFilter,
    TransactionTypeDataFilter,
)
from .included_fields import (
    AccountIncludedFields,
    BaseIncludedFields,
    LedgerEntryIncludedFields,
    MemoIncludedFields,
    TransactionIncludedFields,
    TransactionRecipientIncludedFields,
    TransactionTypeIncludedFields,
)
from .registry_data_filters import (
    BasePersistenceDataFilter,
    PersistenceDataFilter,
)


@dataclass
class BaseRosurceFilter[
    P: BasePersistenceDataFilter,
    D: BaseDataFilter,
    I: BaseIncludedFields,
]:
    """
    Base filter class for resource entities.

    This base filter class combines the persistence metadata
    filtering (database id, update timestamps, etc.) and Data-specific filtering
    (varies by entity type)

    Attributes:
        persistence_data_filter (PersistenceDataFilter):
            Filters by database metadata (id, timestamps, deactivation
            status).
        data_filter (BaseDataFilter):
            Filters by entity-specific business data.
        included_fields (BaseIncludedFields):
            Included fields fields to attach to the response.

    """

    persistence_data_filter: P
    data_filter: D
    included_fields: I


class TransactionFilter(
    BaseRosurceFilter[
        PersistenceDataFilter, TransactionDataFilter, TransactionIncludedFields
    ]
):
    """

    Filter for querying Transaction registries.

    See the documentation for BasePersistenceDataFilter,
    TransactionDataFilter and TransactionIncludedFields for more
    information on the data this class carries.

    Attributes:
        persistence_data_filter (PersistenceDataFilter):
            Filters by database metadata.
        data_filter (TransactionDataFilter):
            Filters by transaction data.
        included_fields(TransactionIncludedFields):
            Determines what extra data will be attached to the result.
    """

    pass


class TransactionTypeFilter(
    BaseRosurceFilter[
        PersistenceDataFilter,
        TransactionTypeDataFilter,
        TransactionTypeIncludedFields,
    ]
):
    """
    Filter for querying TransactionType registries.

    See the documentation for BasePersistenceDataFilter,
    TransactionTypeDataFilter and TransactionTypeIncludedFields for more
    information on the data this class carries.

    Attributes:
        persistence_data_filter (PersistenceDataFilter):
            Filters by database metadata.
        data_filter (TransactionTypeDataFilter):
            Filters by transaction type data.
        included_fields(TransactionTypeIncludedFields):
            Determines what extra data will be attached to the result.
    """

    pass


class AccountFilter(
    BaseRosurceFilter[
        PersistenceDataFilter, AccountDataFilter, AccountIncludedFields
    ]
):
    """
    Filter for querying Account registries.

    See the documentation for BasePersistenceDataFilter,
    AccountDataFilter and AccountIncludedFields for more information on
    the data this class carries.

    Attributes:
        persistence_data_filter (PersistenceDataFilter):
            Filters by database metadata.
        data_filter (AccountDataFilter):
            Filters by account data.
        included_fields(AccountIncludedFields):
            Determines what extra data will be attached to the result.
    """

    pass


class LedgerEntryFilter(
    BaseRosurceFilter[
        PersistenceDataFilter, LedgerEntryDataFilter, LedgerEntryIncludedFields
    ]
):
    """
    Filter for querying LedgerEntry registries.

    See the documentation for BasePersistenceDataFilter,
    LedgerEntryDataFilter and LedgerEntryIncludedFields for more
    information on the data this class carries.

    Attributes:
        persistence_data_filter (PersistenceDataFilter):
            Filters by database metadata.
        data_filter (LedgerEntryDataFilter):
            Filters by ledger entry data.
        included_fields(LedgerEntryIncludedFields):
            Determines what extra data will be attached to the result.
    """

    pass


class TransactionRecipientFilter(
    BaseRosurceFilter[
        PersistenceDataFilter,
        TransactionRecipientDataFilter,
        TransactionRecipientIncludedFields,
    ]
):
    """
    Filter for querying TransactionRecipient registries.

    See the documentation for BasePersistenceDataFilter,
    TransactionRecipientDataFilter and
    TransactionRecipientIncludedFields for more information on the data
    this class carries.

    Attributes:
        persistence_data_filter (PersistenceDataFilter):
            Filters by database metadata.
        data_filter (TransactionRecipientDataFilter):
            Filters by transaction recipient data.
        included_fields(TransactionRecipientIncludedFields):
            Determines what extra data will be attached to the result.
    """

    pass


class MemoFilter(
    BaseRosurceFilter[PersistenceDataFilter, MemoDataFilter, MemoIncludedFields]
):
    """
    Filter for querying Memo registries.

    See the documentation for BasePersistenceDataFilter, MemoDataFilter
    and MemoIncludedFields for more information on the data this class
    carries.

    Attributes:
        persistence_data_filter (PersistenceDataFilter):
            Filters by database metadata.
        data_filter (BaseDataFilter):
            Filters by memo data.
        included_fields(MemoIncludedFields):
            Determines what extra data will be attached to the result.
    """

    pass
