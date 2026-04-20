# Domain

The domain module contains the data structures that the application parts will use to comunicate among themselves. 


## Domain Entities Module overview

Located at `backend/ledger_data/domain/entities/`, this module contains the foundational data structures of the accounting system. 

### Module design

The domain of this application revolves around a type of entities that refered to as `Resource` objects. These carry all the data representing the registry of an accounting construct. For instance, the `Transaction` entity not only contains the information that defines the transaction (e.g. date the transaction ocurred, the transaction refference code or the transaction description), it also contains the database registry data (e.g. date added to database, date updated, deleted status or db identifier) and also attached data objects (e.g. LedgerEntry objects representing the ledger movements of the transaction).

Since objects like these can get fairly complex, the choice was to use composition. This means that each resource object is made out of three other objects with different responsabilities. To implement this, there was created a BaseResource dataclass that has three attributes, namely, `data`, `persistance_data` and `attachments`. The `data` attribute stores the core data of the accounting construct. Keeping with our `Transaction` object analogy, this is the attribute that stores the transaction date, reference, description, etc. The `persistance_data` object stores the database identifier, when the registry was added and soft-deletion info. Finally, the `attachments` attribute is an optional attribute that stores aditional registries that related to the original one. In our analogy the object would contain other resource objects representing ledger movements, the `Memo`, `TransactionType` and a list of `TransactionRecipient` objects representing the parties involved in the transaction.

### Aditional notes on design

- The `attachments` attribute must be optional since the aditional registries are not always needed.

- The attached objects must not have attachments themselves. This can lead to self referential issues and deeply, or even infinitely nested objects.

- In this module, Generics are almost neccesary. They allow to convey information on what a class is allowed to be to the type checkers, preventing misuse before it occurs.


## Domain Entities Module documentation.

### 1. Data Classes (`data_classes.py`)

Data classes represent pure domain data without persistence metadata. They form the core business logic layer.

#### Base Abstraction

**`BaseData`**
- Abstract base class for all domain data entities
- Serves as a type anchor for type checking and validation

#### Core Accounting Entities

**`TransactionData`**
- Represents a financial transaction
- **Attributes**:
  - `transaction_date` (datetime): When the transaction occurred
  - `reference` (str): Unique identifier or source document number (e.g., invoice #)
  - `transaction_type_id` (int): FK to transaction category
  - `description` (str): Commentary on the transaction's purpose
  - `memo_id` (int | None): Optional reference to a memorandum

**`LedgerEntryData`**
- Represents a single line item in a double-entry transaction
- Records the movement of monetary value between accounts
- **Attributes**:
  - `transaction_id` (int): FK to parent transaction
  - `account_id` (int): FK to General Ledger account
  - `entry_balance` (JournalEntryBalance): DEBIT or CREDIT
  - `amount` (Decimal): Precise monetary value

**`AccountData`**
- Represents a General Ledger account
- Defines the destination for ledger movements
- **Attributes**:
  - `code` (AccountCodeStr): Unique hierarchical identifier (e.g., "101-2-003")
  - `currency` (Currency): Functional currency (COP, USD)
  - `name` (str): Descriptive account title
  - `description` (str): Usage guidelines and purpose
  - `parent_account_id` (int | None): FK for hierarchical organization

#### Metadata & Classification Entities

**`TransactionTypeData`**
- Categorizes transactions and manages behavioral classifications
- Supports hierarchical organization
- **Attributes**:
  - `name` (str): Unique display name
  - `description` (str): Detailed explanation
  - `periodicity` (TransactionTypePeriodicity): Expected frequency (MONTHLY, YEARLY)
  - `parent_type_id` (int | None): FK for hierarchical relationships

**`TransactionRecipientData`**
- Represents entities involved in transactions (Vendors, Customers, Employees, Subsidiaries)
- Enables sub-ledger tracking and hierarchical reporting
- **Attributes**:
  - `name` (str): Legal or display name
  - `description` (str): Internal notes and context
  - `parent_recipient_id` (int | None): FK for mapping subsidiary relationships

**`MemoData`**
- Represents formal internal documentation or authorization notes
- Captures communication context and approval trail
- **Attributes**:
  - `date` (datetime): When memo was issued
  - `to` (str): Intended recipient or department
  - `by` (str): Author of the memo
  - `subject` (str): Brief heading
  - `message` (str): Full detailed body
  - `authorized_by` (str): Person granting formal approval
  - `transaction_id` (int | None): FK to associated transaction

> **⚠️ Note**: MemoData is not yet suitable for formal accounting systems as authorization enforcement is pending implementation.

#### Enums & Value Objects

**`JournalEntryBalance` (Enum)**
- Defines double-entry bookkeeping directions
- **Values**:
  - `DEBIT`: Generally increases assets/expenses, decreases liabilities/equity
  - `CREDIT`: Generally increases liabilities/equity, decreases assets

**`TransactionTypePeriodicity` (Enum)**
- Defines expected transaction frequency
- **Values**:
  - `MONTHLY`: Once per calendar month
  - `YEARLY`: Once per fiscal/calendar year

**`Currency` (Enum)**
- Supported currencies
- **Values**: `COP`, `USD`

**`AccountCodeStr` (Value Object)**
- Validated string for hierarchical account codes
- Enforces format: digits separated by single dashes (e.g., "1-10-100")
- **Methods**:
  - `segments`: Returns code split into numerical components
  - `get_code_suffix()`: Returns final numerical segment
  - `get_parent_code()`: Returns all segments except the last

### 2. Persistence Metadata (`persistence.py`)

Persistence classes encapsulate database-related metadata, keeping the domain layer independent of storage implementation details.

**`BasePersistence`**
- Base class for all persistence metadata types
- Serves as a type anchor for the generic Entity pattern

**`Persisted` (dataclass)**
- Metadata for entities that have been persisted to the database
- **Attributes**:
  - `id` (int): Unique identifier assigned by database
  - `created_at` (datetime): Creation timestamp
  - `last_updated_at` (datetime): Most recent update timestamp
  - `deactivated_at` (datetime | None): Deactivation timestamp (None if active)

**`Persistence` (Type Alias)**
- `BasePersistence | None`
- Allows entities to be optional regarding persistence metadata

### 3. Domain Resources (`resources.py`)

Resources extend pure data structures with persistence metadata and optional attachments. They represent complete domain entities with all necessary context.

**`BaseResource[D: BaseData, P: Persistence, A: Attachment]` (Generic)**
- Generic container representing a complete domain entity
- Bridges pure domain data with system-level requirements
- **Type Parameters**:
  - `D`: Core domain data (extends BaseData)
  - `P`: Persistence metadata
  - `A`: Associated attachments
- **Attributes**:
  - `data`: The core business data
  - `persistence_data`: Storage layer metadata (IDs, timestamps)
  - `attachments`: Optional external resources

**Concrete Resource Classes**

All of the following extend `BaseResource` with specific data types:

**`Transaction[P: Persistence, A: (TransactionAttachment, None)]`**
- Full domain representation of a financial transaction
- Combines business state with identity and lifecycle metadata

**`Account[P: Persistence, A: (AccountAttachment, None)]`**
- Full domain representation of a General Ledger account
- Includes hierarchical organization via attachments

**`LedgerEntry[P: Persistence, A: (LedgerEntryAttachement, None)]`**
- Full domain representation of an individual ledger movement
- Connects transaction to account with double-entry details

**`TransactionType[P: Persistence, A: (TransactionTypeAttachment, None)]`**
- Full domain representation of a transaction category
- Manages behavioral classification and hierarchy

**`TransactionRecipient[P: Persistence, A: (TransactionRecipientAttachment, None)]`**
- Full domain representation of a transaction stakeholder
- Supports hierarchical reporting and sub-ledger tracking

**`Memo[P: Persistence, A: (MemoAttachment, None)]`**
- Full domain representation of a formal memo
- Associates documentation with transactions

### 4. Attachments (`attachments.py`)

Attachments represent related data that can be optionally included with resources, enabling flexible data composition without forcing eager loading.

**`BaseAttachment`**
- Base class for all attachment types
- Allows type-checking and validation of related data structures

**`HierarchyAttachment[T: BaseResource]` (Generic)**
- Represents hierarchical relationships in an adjacency-list structure
- **Attributes**:
  - `parent`: The immediate parent entity
  - `parents`: Sequence of all ancestor entities
  - `children`: Sequence of immediate children

**Specific Attachment Classes**

**`TransactionAttachment`**
- Groups optional transaction-related data
- **Attributes**:
  - `transaction_type`: Associated TransactionType
  - `memo`: Associated Memo
  - `journal_entries`: Sequence of LedgerEntry records
  - `recipients`: Sequence of TransactionRecipient records

**`AccountAttachment`**
- Groups account hierarchy information
- **Attributes**:
  - `hierarchy`: HierarchyAttachment containing parent and children accounts

**`TransactionTypeAttachment`**
- Groups transaction type hierarchy
- **Attributes**:
  - `hierarchy`: HierarchyAttachment for parent/child type relationships

**`LedgerEntryAttachement`**
- Groups related ledger entry data
- **Attributes**:
  - `transaction`: Associated Transaction
  - `account`: Associated Account

**`TransactionRecipientAttachment`**
- Groups recipient hierarchy information
- **Attributes**:
  - `hierarchy`: HierarchyAttachment for organizational relationships

**`MemoAttachment`**
- Placeholder for future memo-related attachments

---
