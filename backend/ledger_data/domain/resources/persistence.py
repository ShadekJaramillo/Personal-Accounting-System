# TODO add and correct documentation for this module.

from dataclasses import dataclass
from datetime import datetime


class BasePersistence:
    """Base class for all metadata types.

    Serves as a type anchor for the generic Entity pattern. All concrete
    metadata classes should inherit from this base class.
    """

    pass


type Persistence = BasePersistence | None


# NOTE This class or a subclass of it should include audit metadata too
# This change wwould be big but might be good to do at some point.
@dataclass
class Persisted(BasePersistence):
    """Metadata for persisted entities.

    This metadata class is used for entities that have been persisted to
    the database. It contains information that only persisted entities
    database might have.

    Attributes:
        id (int): The unique identifier assigned by the database.
        created_at (datetime): Timestamp when the entity was created.
        last_updated_at (datetime): Timestamp of the most recent update.
        deactivated_at (datetime | None): Timestamp when the entity was
        deactivated, or None if the entity is still active.
    """

    id: int
    created_at: datetime
    last_updated_at: datetime
    deactivated_at: datetime | None
