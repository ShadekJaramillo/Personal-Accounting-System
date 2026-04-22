from dataclasses import dataclass

from .utils import DateRange


class BasePersistenceDataFilter:
    """
    Base class for all persistence data filters. Currently
    PersistenceDataFilter is the only subclass.
    """

    pass


@dataclass
class PersistenceDataFilter(BasePersistenceDataFilter):
    """
    Filter for persistence metadata common to all entities.

    Allows filtering any persisted entity by its database metadata. This
    filter is used by all entity types.

    Attributes:
        id_set (Set[int] | None):
            Filter by a set of database IDs. If None, ID filtering is
            not applied.
        created_at_range (DateRange | None):
            Filter by creation date range. If None, creation date
            filtering is not applied.
        last_updated_at_range (DateRange | None):
            Filter by last update date range. If None, update date
            filtering is not applied.
        deactivated_at_range (DateRange | None):
            Filter by deactivation date range. If None, deactivation
            filtering is not applied.
    """

    id_set: set[int] | None = None
    created_at_range: DateRange | None = None
    last_updated_at_range: DateRange | None = None
    deactivated_at_range: DateRange | None = None
