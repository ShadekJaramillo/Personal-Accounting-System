from abc import ABC, abstractmethod
from typing import Sequence

from .domain import (
    Account,
    AccountAttachment,
    AccountData,
    AccountFilter,
    LedgerEntry,
    LedgerEntryAttacheable,
    LedgerEntryFilter,
    LedgerEntryIncludedFields,
    Memo,
    MemoAttachable,
    MemoAttachment,
    MemoData,
    MemoFilter,
    MemoIncludedFields,
    Persisted,
    Transaction,
    TransactionAttachable,
    TransactionAttachment,
    TransactionFilter,
    TransactionIncludedFields,
    TransactionRecipient,
    TransactionRecipientAttachable,
    TransactionRecipientData,
    TransactionRecipientFilter,
    TransactionRecipientIncludedFields,
    TransactionType,
    TransactionTypeAttachable,
    TransactionTypeData,
    TransactionTypeFilter,
    TransactionTypeIncludedFields,
)


class BaseTransactionRepository(ABC):
    @abstractmethod
    async def create(
        self,
        transaction: Transaction[
            None,
            TransactionAttachment[
                None, None, Sequence[LedgerEntry[None, None]], None
            ],
        ],
    ) -> Transaction[
        Persisted,
        TransactionAttachment[
            None, None, Sequence[LedgerEntry[Persisted, None]], None
        ],
    ]:
        """
        Transactions can Include a sequence of ledger entries as
        attachments. This is done so this method can also create those
        ledger entries in a single function call.
        """
        pass

    @abstractmethod
    async def update(
        self,
        transaction_id: int,
        data: Transaction[
            Persisted,
            TransactionAttachment[None, None, Sequence[LedgerEntry], None],
        ],
    ) -> Transaction[
        Persisted,
        TransactionAttachment[
            None, None, Sequence[LedgerEntry[Persisted, None]], None
        ],
    ]:
        pass

    @abstractmethod
    async def query(
        self, filter_: TransactionFilter
    ) -> Sequence[Transaction[Persisted, TransactionAttachable]]:
        pass

    @abstractmethod
    async def get_by_id(
        self,
        transaction_id: int,
        included_fields: TransactionIncludedFields | None = None,
    ) -> Transaction[Persisted, TransactionAttachable]:
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
    ) -> list[TransactionType[Persisted, TransactionTypeAttachable]]:
        pass

    @abstractmethod
    async def get_by_id(
        self,
        type_id: int,
        included_fields: TransactionTypeIncludedFields | None = None,
    ) -> TransactionType[Persisted, TransactionTypeAttachable]:
        pass

    @abstractmethod
    async def delete(self, type_id: int) -> None:
        pass


class BaseAccountRepository(ABC):
    @abstractmethod
    async def create(self, data: AccountData) -> Account[Persisted, None]:
        pass

    @abstractmethod
    async def update(
        self, account_id: int, data: AccountData
    ) -> Account[Persisted, None]:
        pass

    @abstractmethod
    async def query(
        self, filter_: AccountFilter
    ) -> list[Account[Persisted, AccountAttachment | None]]:
        pass

    @abstractmethod
    async def delete(self, type_id: int) -> None:
        pass


class BaseLedgerEntryRepository(ABC):
    @abstractmethod
    async def query(
        self, filter_: LedgerEntryFilter
    ) -> list[LedgerEntry[Persisted, LedgerEntryAttacheable]]:
        pass

    @abstractmethod
    async def get_by_id(
        self,
        entry_id: int,
        included_fields: LedgerEntryIncludedFields | None = None,
    ) -> LedgerEntry[Persisted, LedgerEntryAttacheable]:
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
    ) -> list[TransactionRecipient[Persisted, TransactionRecipientAttachable]]:
        pass

    @abstractmethod
    async def get_by_id(
        self,
        recipient_id: int,
        included_fields: TransactionRecipientIncludedFields | None = None,
    ) -> TransactionRecipient[Persisted, TransactionRecipientAttachable]:
        pass

    @abstractmethod
    async def delete(self, recipient_id: int) -> None:
        pass


class BaseMemoRepository(ABC):
    @abstractmethod
    async def create(self, data: MemoData) -> Memo[Persisted, None]:
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
    ) -> list[Memo[Persisted, MemoAttachment | None]]:
        pass

    @abstractmethod
    async def get_by_id(
        self,
        memo_id: int,
        included_fields: MemoIncludedFields | None = None,
    ) -> Memo[Persisted, MemoAttachable] | None:
        pass

    @abstractmethod
    async def delete(self, memo_id: int) -> None:
        pass
