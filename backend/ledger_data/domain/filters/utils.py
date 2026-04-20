from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class DateRange:
    """
    Represents an interval for date filtering.

    Filters dates that fall within [start, end] inclusive.

    Attributes:
        start (datetime): The start of the date range (inclusive).
        end (datetime): The end of the date range (inclusive).
    """

    start: datetime
    end: datetime


@dataclass
class DecimalRange:
    """
    Represents an interval for decimal/amount filtering.

    Filters amounts that fall within [start, end] inclusive.

    Attributes:
        start (Decimal): The start of the amount range (inclusive).
        end (Decimal): The end of the amount range (inclusive).
    """

    start: Decimal
    end: Decimal
