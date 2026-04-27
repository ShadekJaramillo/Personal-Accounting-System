from abc import ABC, abstractmethod
from typing import Any

from .domain import (
    LedgerEntry,
    LedgerEntryData,
    LedgerEntryFilter,
    LedgerEntryIncludedFields,
    Memo,
    MemoData,
    MemoFilter,
    MemoIncludedFields,
    Persisted,
    Transaction,
    TransactionAttachment,
    TransactionData,
    TransactionFilter,
    TransactionIncludedFields,
    TransactionRecipient,
    TransactionRecipientData,
    TransactionRecipientFilter,
    TransactionRecipientIncludedFields,
    TransactionType,
    TransactionTypeData,
    TransactionTypeFilter,
    TransactionTypeIncludedFields,
)


class BaseTransactionRepository(ABC):
    @abstractmethod
    async def create(
        self, data: Transaction[None, Any]
    ) -> Transaction[
        Persisted,
        TransactionAttachment[None, None, LedgerEntry, None],
    ]:
        """
        Transactions can Include a sequence of ledger entries as
        attachments. This is done so this method can also create those
        ledger entries in a single function call.
        """
        pass

    @abstractmethod
    async def update(
        self, transaction_id: int, data: TransactionData
    ) -> Transaction[Persisted, Any]:
        pass

    @abstractmethod
    async def query(
        self,
        filter_: TransactionFilter,
        included_fields: TransactionIncludedFields | None = None,
    ) -> list[Transaction[Persisted, Any]]:
        pass

    @abstractmethod
    async def get_by_id(
        self,
        transaction_id: int,
        included_fields: TransactionIncludedFields | None = None,
    ) -> Transaction[Persisted, Any] | None:
        pass

    @abstractmethod
    async def delete(self, transaction_id: int) -> None:
        pass


class BaseTransactionTypeRepository(ABC):
    @abstractmethod
    async def create(
        self, data: TransactionTypeData
    ) -> TransactionType[Persisted, None]:
        pass

    @abstractmethod
    async def update(
        self, type_id: int, data: TransactionTypeData
    ) -> TransactionType[Persisted, None]:
        pass

    @abstractmethod
    async def query(
        self,
        filter_: TransactionTypeFilter,
        included_fields: TransactionTypeIncludedFields | None = None,
    ) -> list[TransactionType[Persisted, Any]]:
        pass

    @abstractmethod
    async def get_by_id(
        self,
        type_id: int,
        included_fields: TransactionTypeIncludedFields | None = None,
    ) -> TransactionType[Persisted, Any] | None:
        pass

    @abstractmethod
    async def delete(self, type_id: int) -> None:
        pass


class BaseAccountRepository(ABC):
    @abstractmethod
    async def create(
        self, data: TransactionRecipientData
    ) -> TransactionRecipient[Persisted, None]:
        pass

    @abstractmethod
    async def update(
        self, type_id: int, data: TransactionTypeData
    ) -> TransactionType[Persisted, None]:
        pass

    @abstractmethod
    async def query(
        self,
        filter_: TransactionTypeFilter,
        included_fields: TransactionTypeIncludedFields | None = None,
    ) -> list[TransactionType[Persisted, Any]]:
        pass

    @abstractmethod
    async def get_by_id(
        self,
        type_id: int,
        included_fields: TransactionTypeIncludedFields | None = None,
    ) -> TransactionType[Persisted, Any] | None:
        pass

    @abstractmethod
    async def delete(self, type_id: int) -> None:
        pass


class BaseLedgerEntryRepository(ABC):
    @abstractmethod
    async def update(
        self, entry_id: int, data: LedgerEntryData
    ) -> LedgerEntry[Persisted, Any]:
        pass

    @abstractmethod
    async def query(
        self,
        filter_: LedgerEntryFilter,
        included_fields: LedgerEntryIncludedFields | None = None,
    ) -> list[LedgerEntry[Persisted, Any]]:
        pass

    @abstractmethod
    async def delete(self, entry_id: int) -> None:
        pass


class BaseTransactionRecipientRepository(ABC):
    @abstractmethod
    async def create(
        self, data: TransactionRecipientData
    ) -> TransactionRecipient[Persisted, None]:
        pass

    @abstractmethod
    async def update(
        self, recipient_id: int, data: TransactionRecipientData
    ) -> TransactionRecipient[Persisted, None]:
        pass

    @abstractmethod
    async def query(
        self,
        filter_: TransactionRecipientFilter,
        included_fields: TransactionRecipientIncludedFields | None = None,
    ) -> list[TransactionRecipient[Persisted, Any]]:
        pass

    @abstractmethod
    async def delete(self, recipient_id: int) -> None:
        pass


class BaseMemoRepository(ABC):
    @abstractmethod
    async def create(self, data: Memo[None, Any]) -> Memo[Persisted, None]:
        """
        Memos can Include a sequence of transactions as attachments.
        This is done so this method can also create those transactions
        in a single function call.
        """
        pass

    @abstractmethod
    async def update(
        self, memo_id: int, data: MemoData
    ) -> Memo[Persisted, None]:
        pass

    @abstractmethod
    async def query(
        self,
        filter_: MemoFilter,
        included_fields: MemoIncludedFields | None = None,
    ) -> list[Memo[Persisted, Any]]:
        pass

    @abstractmethod
    async def get_by_id(
        self,
        memo_id: int,
        included_fields: MemoIncludedFields | None = None,
    ) -> Memo[Persisted, Any] | None:
        pass

    @abstractmethod
    async def delete(self, memo_id: int) -> None:
        pass
