from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy.orm import Session, sessionmaker

from ..domain.filters import (
    AccountFilter,
    HierarchyIncludedFields,
    InclusionType,
    LedgerEntryDataFilter,
    LedgerEntryFilter,
    LedgerEntryIncludedFields,
    MemoDataFilter,
    MemoFilter,
    MemoIncludedFields,
    PersistenceDataFilter,
    TransactionDataFilter,
    TransactionFilter,
    TransactionIncludedFields,
    TransactionRecipientFilter,
    TransactionRecipientIncludedFields,
    TransactionTypeDataFilter,
    TransactionTypeFilter,
    TransactionTypeIncludedFields,
)
from ..domain.resources import (
    Account,
    AccountAttachment,
    AccountData,
    HierarchyAttachment,
    LedgerEntry,
    LedgerEntryAttacheable,
    LedgerEntryData,
    Memo,
    MemoAttachable,
    MemoAttachment,
    MemoData,
    Persisted,
    Transaction,
    TransactionAttachable,
    TransactionAttachment,
    TransactionRecipient,
    TransactionRecipientAttachable,
    TransactionRecipientAttachment,
    TransactionRecipientData,
    TransactionType,
    TransactionTypeAttachable,
    TransactionTypeData,
)
from .base import (
    BaseAccountRepository,
    BaseLedgerEntryRepository,
    BaseMemoRepository,
    BaseTransactionRecipientRepository,
    BaseTransactionRepository,
    BaseTransactionTypeRepository,
)
from .db_functions import (
    get_accounts_by_filter,
    get_ledger_entries_from_filter,
    get_memos_by_filter,
    get_recipient_parents_by_id,
    get_recipients_by_filter,
    get_registry,
    get_transaction_types_by_filter,
    get_transactions_from_filter,
    post_ledger_entries,
    post_resource,
    update_account,
    update_memo,
    update_recipient,
    update_transaction,
    update_transaction_entries,
)
from .model_translators import (
    account_from_domain_data,
    memo_from_domain_data,
    persistence_from_model,
    recipient_from_domain_data,
    recipient_to_domain_data,
    transaction_from_domain,
    transaction_type_from_domain_data,
    transaction_type_to_domain_data,
)
from .models.resource_models import (
    AccountModel,
    MemoModel,
    TransactionModel,
    TransactionRecipientModel,
    TransactionTypeModel,
)


@dataclass
class SQLTransactionService(BaseTransactionRepository):
    get_session: sessionmaker[Session]

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
        with self.get_session.begin() as session:
            l_e_data: tuple[LedgerEntryData, ...] = tuple(
                l_e.data for l_e in transaction.attachments.ledger_entries
            )
            t_persistence = persistence_from_model(
                post_resource(
                    session, transaction.data, transaction_from_domain
                )
            )
            l_e_persistences = post_ledger_entries(
                session,
                transaction_id=t_persistence.id,
                data=l_e_data,
            )
            ledger_entries = tuple(
                LedgerEntry(
                    data=reg, persistence_data=persistence, attachments=None
                )
                for reg, persistence in zip(
                    l_e_data, l_e_persistences, strict=True
                )
            )

        return Transaction(
            data=transaction.data,
            persistence_data=t_persistence,
            attachments=TransactionAttachment(
                transaction_type=None,
                memo=None,
                ledger_entries=ledger_entries,
                recipients=None,
            ),
        )

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
        with self.get_session.begin() as session:
            transaction_persistence = update_transaction(
                session=session, transaction_id=transaction_id, data=data.data
            )
            transaction_ledger_entries = update_transaction_entries(
                session, data.attachments.ledger_entries
            )
            return Transaction(
                data=data.data,
                persistence_data=transaction_persistence,
                attachments=TransactionAttachment(
                    transaction_type=None,
                    memo=None,
                    ledger_entries=tuple(
                        LedgerEntry(
                            data=l_e_data.data,
                            persistence_data=persistence,
                            attachments=None,
                        )
                        for l_e_data, persistence in zip(
                            data.attachments.ledger_entries,
                            transaction_ledger_entries,
                            strict=True,
                        )
                    ),
                    recipients=None,
                ),
            )

    async def query(
        self, filter_: TransactionFilter
    ) -> Sequence[Transaction[Persisted, TransactionAttachable]]:
        with self.get_session() as session:
            return get_transactions_from_filter(session, filter_)

    async def get_by_id(
        self,
        transaction_id: int,
        included_fields: TransactionIncludedFields | None = None,
    ) -> Transaction[Persisted, TransactionAttachable]:
        if not included_fields:
            included_fields = TransactionIncludedFields(
                InclusionType.NONE,
                InclusionType.NONE,
                InclusionType.NONE,
                InclusionType.NONE,
            )
        transaction_filter = TransactionFilter(
            persistence_data_filter=(
                PersistenceDataFilter(
                    id_set={transaction_id},
                    created_at_range=None,
                    last_updated_at_range=None,
                    deactivated_at_range=None,
                )
            ),
            data_filter=TransactionDataFilter(
                date_range=None,
                references=None,
                transaction_type_ids=None,
                recipient_ids=None,
                memo_ids=None,
            ),
            included_fields=included_fields,
        )
        with self.get_session() as session:
            res = get_transactions_from_filter(session, transaction_filter)
        if len(res) < 1:
            raise ValueError("The requested id does not exist")
        return res[0]

    # TODO desactivating a transaction should also desactivate its
    # ledger movements.
    # TODO define what happens with registries pointing to the deleted instance.
    async def desactivate(self, transaction_id: int) -> None:
        with self.get_session.begin() as session:
            model: TransactionModel | None = session.get(
                TransactionModel, transaction_id
            )

            if not model:
                raise ValueError(
                    f"Transaction with ID {transaction_id} not found"
                )

            if model.deactivated_at:
                raise ValueError(
                    f"Transaction with ID {transaction_id} "
                    f"already desactivated at{model.deactivated_at}"
                )

            model.deactivated_at = datetime.now(timezone.utc)


@dataclass
class SQLTransactionTypeService(BaseTransactionTypeRepository):
    get_session: sessionmaker[Session]

    async def create(
        self, data: TransactionTypeData
    ) -> TransactionType[Persisted, None]:
        with self.get_session.begin() as session:
            persistence = persistence_from_model(
                post_resource(session, data, transaction_type_from_domain_data)
            )
            return TransactionType(
                data=data,
                persistence_data=persistence,
                attachments=None,
            )

    async def update(
        self, type_id: int, data: TransactionTypeData
    ) -> TransactionType[Persisted, None]:
        with self.get_session() as session:
            model: TransactionTypeModel | None = get_registry(
                session, type_id, table_model=TransactionTypeModel
            )

            if not model:
                raise ValueError(f"TransactionType with ID {type_id} not found")

            model.name = data.name
            model.description = data.description
            model.periodicity = data.periodicity
            model.parent_type_id = data.parent_type_id

            session.commit()
            session.refresh(model)

            return TransactionType(
                data=transaction_type_to_domain_data(model),
                persistence_data=persistence_from_model(model),
                attachments=None,
            )

    async def query(
        self,
        filter_: TransactionTypeFilter,
    ) -> list[TransactionType[Persisted, TransactionTypeAttachable]]:
        with self.get_session() as session:
            return get_transaction_types_by_filter(session, filter_)

    async def get_by_id(
        self,
        type_id: int,
        included_fields: TransactionTypeIncludedFields | None = None,
    ) -> TransactionType[Persisted, TransactionTypeAttachable]:
        if not included_fields:
            included_fields = TransactionTypeIncludedFields(
                HierarchyIncludedFields(
                    InclusionType.NONE, InclusionType.NONE, InclusionType.NONE
                )
            )
        filter_ = TransactionTypeFilter(
            PersistenceDataFilter(
                id_set={type_id},
            ),
            data_filter=TransactionTypeDataFilter(None, None, None),
            included_fields=included_fields,
        )
        with self.get_session() as session:
            result = get_transaction_types_by_filter(session, filter_)
            if len(result) < 1:
                raise ValueError("The requested id does not exist")
            return result[0]

    # TODO think about what deactivating a transaction type should do
    # if the transaction type has child types.
    # TODO define what happens with registries pointing to the deactivated
    # instance.
    async def desactivate(self, type_id: int) -> None:
        with self.get_session.begin() as session:
            model: TransactionTypeModel | None = session.get(
                TransactionTypeModel, type_id
            )

            # TODO correct the error message
            if not model:
                raise ValueError(f"Transaction with ID {type_id} not found")
            # TODO correct the error message
            if model.deactivated_at:
                raise ValueError(
                    f"Transaction with ID {type_id} "
                    f"already desactivated at{model.deactivated_at}"
                )
            model.deactivated_at = datetime.now(timezone.utc)


@dataclass
class SQLAccountService(BaseAccountRepository):
    get_session: sessionmaker[Session]

    async def create(self, data: AccountData) -> Account[Persisted, None]:
        with self.get_session.begin() as session:
            persistence = persistence_from_model(
                post_resource(session, data, account_from_domain_data)
            )

        return Account(
            data=data, persistence_data=persistence, attachments=None
        )

    async def update(
        self, account_id: int, data: AccountData
    ) -> Account[Persisted, None]:
        with self.get_session.begin() as session:
            persistence = update_account(session, account_id, data)
        return Account(
            data=data,
            persistence_data=persistence,
            attachments=None,
        )

    async def query(
        self, filter_: AccountFilter
    ) -> list[Account[Persisted, AccountAttachment | None]]:
        with self.get_session() as session:
            return get_accounts_by_filter(session, filter_)

    async def desactivate(self, account_id: int):
        with self.get_session.begin() as session:
            model: AccountModel | None = session.get(AccountModel, account_id)

            # TODO correct the error message
            if not model:
                raise ValueError(f"Transaction with ID {account_id} not found")
            # TODO correct the error message
            if model.deactivated_at:
                raise ValueError(
                    f"Transaction with ID {account_id} "
                    f"already desactivated at{model.deactivated_at}"
                )
            model.deactivated_at = datetime.now(timezone.utc)


@dataclass
class SQLLedgerEntryService(BaseLedgerEntryRepository):
    get_session: sessionmaker[Session]

    async def query(
        self, filter_: LedgerEntryFilter
    ) -> list[LedgerEntry[Persisted, LedgerEntryAttacheable]]:
        with self.get_session() as session:
            return get_ledger_entries_from_filter(session, filter_)

    async def get_by_id(
        self,
        entry_id: int,
        included_fields: LedgerEntryIncludedFields | None = None,
    ) -> LedgerEntry[Persisted, LedgerEntryAttacheable]:
        if not included_fields:
            included_fields = LedgerEntryIncludedFields(
                InclusionType.NONE,
                InclusionType.NONE,
            )
        filter_ = LedgerEntryFilter(
            PersistenceDataFilter(
                id_set={entry_id},
            ),
            data_filter=LedgerEntryDataFilter(None, None, None, None),
            included_fields=included_fields,
        )
        with self.get_session() as session:
            result = get_ledger_entries_from_filter(session, filter_)
            if len(result) < 1:
                raise ValueError("The requested id does not exist")
            return result[0]


@dataclass
class SQLTransactionRecipientService(BaseTransactionRecipientRepository):
    get_session: sessionmaker[Session]

    async def create(
        self, data: TransactionRecipientData
    ) -> TransactionRecipient[Persisted, None]:
        with self.get_session.begin() as session:
            persistence = persistence_from_model(
                post_resource(session, data, recipient_from_domain_data)
            )

            return TransactionRecipient(
                data=data,
                persistence_data=persistence,
                attachments=None,
            )

    async def update(
        self, recipient_id: int, data: TransactionRecipientData
    ) -> TransactionRecipient[Persisted, None]:
        with self.get_session() as session:
            persistence = update_recipient(session, recipient_id, data)
        return TransactionRecipient(
            data=data,
            persistence_data=persistence,
            attachments=None,
        )

    async def query(
        self,
        filter_: TransactionRecipientFilter,
    ) -> list[TransactionRecipient[Persisted, TransactionRecipientAttachable]]:
        with self.get_session() as session:
            result = get_recipients_by_filter(session, filter_=filter_)
            return [
                TransactionRecipient(
                    data=recipient_to_domain_data(model),
                    persistence_data=persistence_from_model(model),
                    attachments=TransactionRecipientAttachment(
                        HierarchyAttachment(
                            parent=None,
                            parents=result[model],  # type: ignore # TODO remove and fix this ignore.
                            children=None,
                        )
                    ),
                )
                for model in result.keys()
            ]

    async def get_by_id(
        self,
        recipient_id: int,
        included_fields: TransactionRecipientIncludedFields | None = None,
    ) -> TransactionRecipient[Persisted, TransactionRecipientAttachable]:
        with self.get_session() as session:
            model: TransactionRecipientModel | None = get_registry(
                session, id=recipient_id, table_model=TransactionRecipientModel
            )

            if model is None:
                raise ValueError(f"model with id {recipient_id} not found")

            if not included_fields:
                attached_data = None

            elif (
                included_fields.hierarchy_inclusions.include_all_parents
                == InclusionType.OBJECT
            ):
                parents = get_recipient_parents_by_id(
                    session, recipient_id=recipient_id, attached_data="model"
                )
                attached_data = TransactionRecipientAttachment(
                    HierarchyAttachment(None, parents, None)  # type: ignore # TODO remove and fix this ignore.
                )
            elif (
                included_fields.hierarchy_inclusions.include_all_parents
                == InclusionType.ID
            ):
                parents = get_recipient_parents_by_id(
                    session, recipient_id=recipient_id, attached_data="ids"
                )
                attached_data = TransactionRecipientAttachment(
                    HierarchyAttachment(None, parents, None)  # type: ignore # TODO remove and fix this ignore.
                )
            return TransactionRecipient(
                data=recipient_to_domain_data(model),
                persistence_data=persistence_from_model(model),
                attachments=attached_data,
            )

    # # TODO create a method for fetching all available branches branches.
    # # TODO create a method for fetching all descendants of a recipient.

    # TODO think about what deactivating a transaction type should do
    # if the transaction type has child types.
    # TODO define what happens with registries pointing to the deactivated
    # instance.
    async def desactivate(self, recipient_id: int) -> None:
        with self.get_session() as session:
            model: TransactionRecipientModel | None = session.get(
                TransactionRecipientModel, recipient_id
            )

            if not model:
                raise ValueError(
                    f"TransactionRecipient with ID {recipient_id} not found"
                )

            # TODO correct the error message
            if model.deactivated_at:
                raise ValueError(
                    f"Transaction with ID {recipient_id} "
                    f"already desactivated at{model.deactivated_at}"
                )
            model.deactivated_at = datetime.now(timezone.utc)
            session.commit()


@dataclass
class SQLMemoService(BaseMemoRepository):
    get_session: sessionmaker[Session]

    async def create(self, data: MemoData) -> Memo[Persisted, None]:
        with self.get_session.begin() as session:
            persistence = persistence_from_model(
                post_resource(session, data, memo_from_domain_data)
            )

        return Memo(data=data, persistence_data=persistence, attachments=None)

    async def update(
        self, memo_id: int, data: MemoData
    ) -> Memo[Persisted, None]:
        with self.get_session.begin() as session:
            persistence = update_memo(session, memo_id, data)

            return Memo(
                data=data, persistence_data=persistence, attachments=None
            )

    async def query(
        self,
        filter_: MemoFilter,
    ) -> list[Memo[Persisted, MemoAttachment | None]]:
        with self.get_session() as session:
            res = get_memos_by_filter(session, filter_)
        return res

    async def get_by_id(
        self,
        memo_id: int,
        included_fields: MemoIncludedFields | None = None,
    ) -> Memo[Persisted, MemoAttachable] | None:
        if not included_fields:
            included_fields = MemoIncludedFields(InclusionType.NONE)
        filter_ = MemoFilter(
            PersistenceDataFilter(
                id_set={memo_id},
            ),
            data_filter=MemoDataFilter(None, None, None, None, None),
            included_fields=included_fields,
        )
        with self.get_session() as session:
            result = get_memos_by_filter(session, filter_)
            if len(result) < 1:
                raise ValueError("The requested id does not exist")
            return result[0]

    # TODO define what happens with registries pointing to the deactivated
    # instance.
    async def desactivate(self, memo_id: int) -> None:
        with self.get_session() as session:
            model: MemoModel | None = session.get(MemoModel, memo_id)

            if not model:
                raise ValueError(
                    f"TransactionRecipient with ID {memo_id} not found"
                )

            # TODO correct the error message
            if model.deactivated_at:
                raise ValueError(
                    f"Transaction with ID {memo_id} "
                    f"already desactivated at{model.deactivated_at}"
                )
            model.deactivated_at = datetime.now(timezone.utc)
            session.commit()
