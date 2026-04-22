# TODO module docstring not revised yet
"""
Domain Data Entities for the Accounting System.

This module contains the foundational data structures used throughout
the application's core. It defines the schema for financial
transactions, ledger entries, account hierarchies, and classification
metadata.

The entities are designed as immutable-first (via dataclasses) to ensure
consistency across the hexagonal boundary, providing a type-safe
interface for domain services and repositories.

Main Components:
    * Base Abstractions: BaseData and AccountCodeStr value object.
    * Accounting Core: TransactionData, JournalEntryData, and
      AccountData.
    * Metadata & Classification: TransactionTypeData and
      TransactionRecipientData.
    * Enums: JournalEntryBalance for double-entry direction.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum

# ============================================================================
# Data Classes
# ============================================================================


class BaseData:
    """
    Base abstraction for all domain data entities.

    Serves as the foundational type for all data-centered entities
    within the domain layer. Useful for type-checking at runtime or
    static.
    """

    pass


@dataclass
class TransactionData(BaseData):
    """
    Represents a financial transaction.

    This entity encapsulates the information required to record a
    transaction within the accounting ledger.

    Attributes:
        transaction_date(datetime):
            The official date the transaction occurred.
        reference(str):
            A unique identifier or source document number (e.g., invoice
            #).
        transaction_type_id(int):
            Foreign key mapping to the specific category of transaction.
        description(str):
            A commentary on the transaction's purpose.
        memo_id(int | None):
            Optional reference to a memorandum.
    """

    transaction_date: datetime
    reference: str
    transaction_type_id: int
    description: str
    memo_id: int | None


@dataclass
class TransactionTypeData(BaseData):
    """
    Defines a behavioral classification for transactions.

    This entity categorizes transactions (e.g., Accounts Payable,
    Payroll) and manages hierarchical relationships between types to
    support custom account structures.

    Attributes:
        name (str):
            The unique display name of the transaction type.
        description (str):
            A detailed explanation of what defines transactions of this
            kind.
        periodicity (TransactionTypePeriodicity):
            Enum object defining the expected frequency (e.g., Monthly,
            Quarterly, Ad-hoc). Currently only
            `TransactionTypePeriodicity.monthly` and
            `TransactionTypePeriodicity.yearly` are supported.
        parent_type_id (int | None):
            Reference to a parent transaction type, enabling a tree
            structure for better transaction classification.
    """

    name: str
    description: str
    periodicity: "TransactionTypePeriodicity"
    parent_type_id: int | None


@dataclass
class AccountData(BaseData):
    """
    Represents a specific account within the Chart of Accounts of the
    General Ledger.

    This entity defines the destination for ledger movemets, providing
    the structure for tracking balances for any specific asset,
    liability, equity, revenue, or expense.

    Attributes:
        code (AccountCodeStr):
            A unique numeric identifier (e.g., "101-2-003") used for
            indexing and classification within the Chart of Accounts.
        currency (Currency):
            The functional currency in which the account denominates its
            balance.
        name (str):
            The descriptive title of the account (e.g., "Cash at Bank").
        description (str):
            A detailed explanation of the account's purpose and usage
            guidelines.
        parent_account_id (int | None):
            Reference to a parent account to enable hierarchical
            organization.
    """

    code: "AccountCodeStr"
    currency: "Currency"
    name: str
    description: str
    parent_account_id: int | None


@dataclass
class LedgerEntryData(BaseData):
    """
    Represents a single line item within a double-entry accounting
    transaction.

    In every transaction there is a movement of something with monetary
    value from one place to another (e.g. a bank transfer moving funds
    from our account, receiving merchandise from a provider or getting
    into debt). This entity links a specific monetary value to a General
    Ledger account and registers if the account balance is being
    increased or decreased (or more precisely, being credited or
    debited).

    Attributes:
        transaction_id (int):
            Reference to the parent TransactionData record.
        account_id (int):
            Reference to the specific General Ledger account affected.
        entry_balance (JournalEntryBalance):
            Enum object indicating the side of the entry (e.g., DEBIT or
            CREDIT).
        amount (Decimal):
            The precise monetary value of the entry, stored as a Decimal
            to prevent floating-point rounding errors.
    """

    transaction_id: int
    account_id: int
    entry_balance: "JournalEntryBalance"
    amount: Decimal


@dataclass
class TransactionRecipientData(BaseData):
    """
    Represents an entity or individual involved in a financial
    transaction.

    This entity identifies the parties (e.g., Vendor, Customer, Employee
    or an own company subsidiary) associated with a transaction,
    allowing for detailed sub-ledger tracking and hierarchical reporting
    of recipient relationships.

    Attributes:
        name (str):
            The legal or display name of the recipient.
        description (str):
            Additional context or internal notes regarding the
            recipient.
        parent_recipient_id (int | None):
            Reference to a parent entity, used for mapping subsidiaries
            to a corporate head office or grouping related parties.
    """

    name: str
    description: str
    parent_recipient_id: int | None


# NOTE This class is not suitable for formal accounting systems yet
# since authorization and identification of the parts involved in the
# memo is not actually enforced yet in the API.
class MemoData(BaseData):
    """
    Represents formal internal documentation or authorization notes for
    a transaction.

    This entity stores supplementary textual records and audit trail
    information linked to a specific transaction, capturing the
    communication context and the individuals responsible for its
    initiation and approval.

    This class is not suitable for formal accounting systems yet since
    authorization and identification of the parts involved in the memo
    is not actually enforced yet in the API.

    Attributes:
        date (datetime):
            The timestamp when the memo was issued.
        receiver (str):
            The intended recipient or department of the memo.
        emitter (str):
            The individual who authored or issued the memo.
        subject (str):
            A brief heading summarizing the memo's content.
        message (str):
            The full detailed body of the memo.
        authorized_by (str):
            The name of the person who granted formal approval for the
            action described.
    """

    date: datetime
    receiver: str
    emitter: str
    subject: str
    message: str
    authorized_by: str


# ============================================================================
# Enum classes
# ============================================================================


class TransactionTypePeriodicity(Enum):
    """
    Enumeration of transaction type periodicity patterns.

    Defines how frequently a transaction type is expected to occur. Used
    to categorize and validate transactions and to support recurring
    transaction patterns in accounting.

    Attributes:
        MONTHLY (str):
            Indicates the transaction occurs once per calendar month.
        YEARLY (str):
            Indicates the transaction occurs once per fiscal or calendar
            year.
    """

    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class JournalEntryBalance(Enum):
    """
    Defines the standard balance types for double-entry bookkeeping.

    This enumeration specifies the direction of a financial entry,
    determining whether an amount increases or decreases an account
    balance based on the account's classification (Asset, Liability,
    Equity, Revenue, or Expense).

    Attributes:
        CREDIT (str):
            Represents a credit entry. Generally increases
            liabilities/equity and decreases assets.
        DEBIT (str):
            Represents a debit entry. Generally increases
            assets/expenses and decreases liabilities.
    """

    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class Currency(Enum):
    COP = "COP"
    USD = "USD"


# ============================================================================
# Utility classes
# ============================================================================


class AccountCodeStr(str):
    """
    A validated string representation of a hierarchical account code.

    This value object ensures that account codes adhere to a strict
    numerical segmentation format (e.g., '1-10-100'), facilitating
    consistent parsing of the Account codes and preventing malformed
    identifiers from entering the domain layer.

    Attributes:
        same attributes as built-in strings.
    """

    def __new__(cls, content):
        # Pattern ensures the string is only digits and dashes,
        # and doesn't start/end with a dash or have double dashes.
        pattern = r"^\d+(-\d+)*$"

        if not re.match(pattern, content):
            raise ValueError(
                f"Invalid code format: '{content}'. "
                "Code must contain only numbers and single dashes."
            )

        # 2. Return the new string instance
        return super().__new__(cls, content)

    @property
    def segments(self):
        """Helper to split the code into its numerical components."""
        return self.split("-")

    def get_code_suffix(self):
        """Returns the final numerical segment of the code."""
        return self.segments[-1]

    def get_parent_code(self):
        """Returns all segments except the last one, joined by dashes."""
        parts = self.segments
        if len(parts) == 1:
            return ""  # Or return None/self depending on your preference
        return "-".join(parts[:-1])
