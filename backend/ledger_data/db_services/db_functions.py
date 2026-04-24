from collections import defaultdict
from typing import Any, Callable, Generator, Iterable, Literal, Sequence, Tuple

from sqlalchemy import (
    CTE,
    BinaryExpression,
    ColumnElement,
    Select,
    select,
    update,
)
from sqlalchemy.orm import (
    Session,
    aliased,
    joinedload,
    selectinload,
)

from ..domain.filters import (
    AccountFilter,
    InclusionType,
    LedgerEntryFilter,
    MemoDataFilter,
    MemoFilter,
    MemoIncludedFields,
    PersistenceDataFilter,
    TransactionFilter,
    TransactionRecipientFilter,
    TransactionTypeDataFilter,
    TransactionTypeFilter,
)
from ..domain.resources import (
    Account,
    AccountAttachable,
    AccountAttachment,
    AccountData,
    BaseData,
    HierarchyAttachment,
    LedgerEntry,
    LedgerEntryAttacheable,
    LedgerEntryAttachement,
    LedgerEntryData,
    Memo,
    MemoAttachable,
    MemoAttachment,
    MemoData,
    Persisted,
    Transaction,
    TransactionAttachable,
    TransactionAttachment,
    TransactionData,
    TransactionRecipient,
    TransactionRecipientAttachable,
    TransactionRecipientData,
    TransactionType,
    TransactionTypeAttachable,
    TransactionTypeAttachment,
)
from ..models.resource_models import (
    AccountModel,
    LedgerEntryModel,
    MemoModel,
    RegistryMetadataMixin,
    TransactionModel,
    TransactionRecipientModel,
    TransactionTypeModel,
    utcnow,
)
from .model_translators import (
    account_to_domain,
    account_to_domain_data,
    ledger_entries_from_domain,
    ledger_entries_to_domain,
    ledger_entry_to_domain,
    memo_to_domain,
    persistence_from_model,
    recipient_to_domain,
    recipients_to_domain,
    transaction_to_domain,
    transaction_to_domain_data,
    transaction_type_to_domain,
    transaction_type_to_domain_data,
)


def get_registry[T: RegistryMetadataMixin](
    session: Session, id: int, table_model: type[T]
) -> T | None:
    return session.scalar(
        select(table_model).where(
            table_model.id == id,
            table_model.deactivated_at.is_(None),
        )
    )


def post_resource[D: BaseData, R: RegistryMetadataMixin](
    session: Session,
    data: D,
    translator_from_domain: Callable[[D], R],
):
    model = translator_from_domain(data)
    session.add(model)
    session.flush()
    return model


def update_transaction(
    session: Session, transaction_id: int, data: TransactionData
):
    model = get_registry(session, transaction_id, TransactionModel)
    if not model:
        raise ValueError(f"Transaction with ID {transaction_id} not found")

    model.transaction_date = data.transaction_date
    model.description = data.description
    model.reference = data.reference
    model.transaction_type_id = data.transaction_type_id
    model.memo_id = data.memo_id

    model.last_updated_at = utcnow()

    return persistence_from_model(model)


def update_transaction_entries(session: Session, data: Sequence[LedgerEntry]):
    # Identify the keeped, the added and the removed registries
    t_ids: set[int] = set()
    keeped: list[LedgerEntry[Persisted, None]] = []
    added: list[LedgerEntryData] = []
    for l_e in data:
        if isinstance(l_e.persistence_data, Persisted):
            t_ids.add(l_e.persistence_data.id)
            keeped.append(l_e)
        else:
            added.append(l_e.data)
    if len(t_ids) != 1:
        raise ValueError("Entries correspond to more than one transaction")
    t_id: int = t_ids.pop()
    transaction = get_registry(session, t_id, TransactionModel)
    if transaction is None:
        raise ValueError("transaction does not exist")

    ledger_entries = transaction.ledger_entries
    removed = {l_e_model.id for l_e_model in ledger_entries}
    for l_e in keeped:
        removed.remove(l_e.persistence_data.id)

    keeped_data = list(update_ledger_entries(session, keeped))
    added_data = list(post_ledger_entries(session, t_id, added))

    remove_ledger_entries(session, removed)

    # we join added_data and keeped_data so the order keeps preserved.
    reordered: list[Persisted] = []
    for l_e in data:
        if isinstance(l_e.persistence_data, Persisted):
            reordered.append(keeped_data.pop(0))
        else:
            reordered.append(added_data.pop(0))

    return reordered


def get_transactions_from_filter(
    session: Session, filter_: TransactionFilter
) -> list[Transaction[Persisted, TransactionAttachable]]:
    where_clauses = get_persistance_filter_statement(
        filter_.persistence_data_filter, TransactionModel
    )
    # transaction data filters
    data_filter = filter_.data_filter
    if data_filter.date_range:
        date_range = data_filter.date_range
        where_clauses.append(
            TransactionModel.transaction_date.between(
                date_range.start, date_range.end
            )
        )
    if data_filter.references:
        where_clauses.append(
            TransactionModel.reference.in_(data_filter.references)
        )
    if data_filter.transaction_type_ids:
        where_clauses.append(
            TransactionModel.transaction_type_id.in_(
                data_filter.transaction_type_ids
            )
        )
    if data_filter.recipient_ids:
        where_clauses.append(
            TransactionModel.recipients.any(
                TransactionRecipientModel.id.in_(data_filter.recipient_ids)
            )
        )
    if data_filter.memo_ids:
        where_clauses.append(TransactionModel.memo_id.in_(data_filter.memo_ids))

    options = []
    included_fields = filter_.included_fields
    if included_fields.include_transaction_type:
        match included_fields.include_transaction_type:
            case InclusionType.ID:
                options.append(
                    joinedload(TransactionModel.transaction_type).load_only(
                        TransactionTypeModel.id
                    )
                )
            case InclusionType.OBJECT:
                options.append(joinedload(TransactionModel.transaction_type))
            case InclusionType.NONE:
                pass
    if included_fields.include_ledger_entries:
        match included_fields.include_ledger_entries:
            case InclusionType.ID:
                options.append(
                    selectinload(TransactionModel.ledger_entries).load_only(
                        LedgerEntryModel.id
                    )
                )
            case InclusionType.OBJECT:
                options.append(selectinload(TransactionModel.ledger_entries))
            case InclusionType.NONE:
                pass
    if included_fields.include_recipients:
        match included_fields.include_recipients:
            case InclusionType.ID:
                options.append(
                    selectinload(TransactionModel.recipients).load_only(
                        TransactionRecipientModel.id
                    )
                )
            case InclusionType.OBJECT:
                options.append(selectinload(TransactionModel.recipients))
            case InclusionType.NONE:
                pass
    if included_fields.include_memo:
        match included_fields.include_memo:
            case InclusionType.ID:
                options.append(
                    joinedload(TransactionModel.memo).load_only(MemoModel.id)
                )
            case InclusionType.OBJECT:
                options.append(joinedload(TransactionModel.memo))
            case InclusionType.NONE:
                pass

    stmt = select(TransactionModel).where(*where_clauses).options(*options)
    results = session.execute(stmt).scalars().all()

    ret: list[Transaction[Persisted, TransactionAttachable]] = []
    for result in results:
        match included_fields.include_transaction_type:
            case InclusionType.ID:
                transaction_type = result.transaction_type_id
            case InclusionType.OBJECT:
                transaction_type = transaction_type_to_domain(
                    result.transaction_type
                )
            case InclusionType.NONE | None:
                transaction_type = None
        match included_fields.include_ledger_entries:
            case InclusionType.ID:
                ledger_entries = [l_e.id for l_e in result.ledger_entries]
            case InclusionType.OBJECT:
                ledger_entries = ledger_entries_to_domain(result.ledger_entries)
            case InclusionType.NONE | None:
                ledger_entries = None
        match included_fields.include_recipients:
            case InclusionType.ID:
                recipients = [r.id for r in result.recipients]
            case InclusionType.OBJECT:
                recipients = recipients_to_domain(result.recipients)
            case InclusionType.NONE | None:
                recipients = None
        match included_fields.include_memo:
            case InclusionType.ID:
                memo = result.memo_id
            case InclusionType.OBJECT:
                memo = memo_to_domain(result.memo) if result.memo else None
            case InclusionType.NONE | None:
                memo = None

        ret.append(
            Transaction(
                data=transaction_to_domain_data(result),
                persistence_data=persistence_from_model(result),
                attachments=TransactionAttachment[Any, Any, Any, Any](
                    transaction_type=transaction_type,
                    ledger_entries=ledger_entries,
                    recipients=recipients,
                    memo=memo,
                ),
            )
        )
    return ret


# TODO Study how this complex SQL query works.
def get_transaction_types_by_filter(
    session: Session, filter_: TransactionTypeFilter
) -> list[TransactionType[Persisted, TransactionTypeAttachable]]:
    where_clauses = get_persistance_filter_statement(
        filter_.persistence_data_filter, TransactionTypeModel
    )

    # Data filters
    data_filters: TransactionTypeDataFilter = filter_.data_filter
    if data_filters.names:
        where_clauses.append(TransactionTypeModel.name.in_(data_filters.names))
    if data_filters.periodicities:
        where_clauses.append(
            TransactionTypeModel.periodicity.in_(data_filters.periodicities)
        )
    if data_filters.parent_type_ids:
        # TODO hfs, this is not going to be fun.
        pass

    # 1. Base statement: Select the model AND track the origin with `root_id`
    base_stmt = select(
        TransactionTypeModel, TransactionTypeModel.id.label("root_id")
    ).where(*where_clauses)

    # 2. Define the root CTE
    root_cte: CTE = base_stmt.cte(name="recipient_tree", recursive=True)

    # 3. Define the recursive part
    parent_alias = aliased(TransactionTypeModel)
    recursive_query = root_cte.union_all(
        select(
            parent_alias,
            root_cte.c.root_id,  # Pass the root_id up the tree
        ).where(parent_alias.id == root_cte.c.parent_type)
    )

    # TODO the only included field that works is the include_all_parents.
    # 4. Final selection and dictionary grouping
    included_fields = filter_.included_fields.hierarchy_inclusions
    root_model_alias = aliased(TransactionTypeModel)

    ret: list[TransactionType] = []

    if included_fields.include_all_parents == InclusionType.ID:
        # Join CTE back to the root model to get the dict keys
        stmt = (
            select(root_model_alias, recursive_query.c.parent_type)
            .select_from(recursive_query)
            .join(
                root_model_alias,
                root_model_alias.id == recursive_query.c.root_id,
            )
            .where(recursive_query.c.parent_type.is_not(None))
        )

        for root_model, parent_id in session.execute(stmt):
            ret.append(
                TransactionType(
                    data=transaction_type_to_domain_data(root_model),
                    persistence_data=persistence_from_model(root_model),
                    attachments=TransactionTypeAttachment(
                        hierarchy=HierarchyAttachment(
                            parent=None, parents=parent_id, children=None
                        )
                    ),
                )
            )

    elif included_fields.include_all_parents == InclusionType.OBJECT:
        # Map the CTE output back to ORM entities
        ancestor_alias = aliased(TransactionTypeModel, recursive_query)
        stmt = (
            select(root_model_alias, ancestor_alias)
            .select_from(recursive_query)
            .join(
                root_model_alias,
                root_model_alias.id == recursive_query.c.root_id,
            )
        )

        for root_model, ancestor_model in session.execute(stmt):
            ret.append(
                TransactionType(
                    data=transaction_type_to_domain_data(root_model),
                    persistence_data=persistence_from_model(root_model),
                    attachments=TransactionTypeAttachment(
                        hierarchy=HierarchyAttachment(
                            parent=None,
                            parents=[
                                transaction_type_to_domain(parent, None)
                                for parent in ancestor_model
                            ],
                            children=None,
                        )
                    ),
                )
            )

    return ret


def update_account(session: Session, account_id: int, data: AccountData):
    model: AccountModel | None = get_registry(
        session, id=account_id, table_model=AccountModel
    )

    if not model:
        raise ValueError(
            f"TransactionRecipient with ID {account_id} not found."
        )

    model.code = data.code
    model.currency = data.currency
    model.name = data.name
    model.description = data.description
    if data.parent_account_id:
        model.parent_account_id = data.parent_account_id

    model.last_updated_at = utcnow()

    return persistence_from_model(model)


def get_accounts_by_filter(session: Session, filter_: AccountFilter):
    where_clauses = get_persistance_filter_statement(
        filter_.persistence_data_filter, AccountModel
    )

    data_filters = filter_.data_filter
    if data_filters.codes:
        where_clauses.append(AccountModel.code.in_(data_filters.codes))
    if data_filters.currencies:
        where_clauses.append(AccountModel.name.in_(data_filters.currencies))
    if data_filters.names:
        where_clauses.append(AccountModel.name.in_(data_filters.names))
    if data_filters.parent_account_ids:
        pass  # TODO hfs, this is not going to be fun.

    # 1. Base statement: Select the model AND track the origin with `root_id`
    base_stmt: Select[Tuple[AccountModel, int]] = select(
        AccountModel, AccountModel.id.label("root_id")
    ).where(*where_clauses)

    # 2. Define the root CTE
    root_cte = base_stmt.cte(name="account_tree", recursive=True)

    # 3. Define the recursive part
    parent_alias = aliased(AccountModel)
    recursive_query = root_cte.union_all(
        select(
            parent_alias,
            root_cte.c.root_id,  # Pass the root_id up the tree
        ).where(parent_alias.id == root_cte.c.parent_type)
    )

    # TODO the only included field that works is the include_all_parents.
    # 4. Final selection and dictionary grouping
    included_fields = filter_.included_fields.hierarchy_inclusions
    root_model_alias = aliased(AccountModel)

    ret: list[Account[Persisted, AccountAttachable]] = []

    if included_fields.include_all_parents == InclusionType.ID:
        # Join CTE back to the root model to get the dict keys
        stmt = (
            select(root_model_alias, recursive_query.c.parent_type)
            .select_from(recursive_query)
            .join(
                root_model_alias,
                root_model_alias.id == recursive_query.c.root_id,
            )
            .where(recursive_query.c.parent_type.is_not(None))
        )

        for root_model, parent_id in session.execute(stmt):
            ret.append(
                Account(
                    data=account_to_domain_data(root_model),
                    persistence_data=persistence_from_model(root_model),
                    attachments=AccountAttachment(
                        hierarchy=HierarchyAttachment(
                            parent=None, parents=parent_id, children=None
                        )
                    ),
                )
            )

    elif included_fields.include_all_parents == InclusionType.OBJECT:
        # Map the CTE output back to ORM entities
        ancestor_alias = aliased(AccountModel, recursive_query)
        stmt = (
            select(root_model_alias, ancestor_alias)
            .select_from(recursive_query)
            .join(
                root_model_alias,
                root_model_alias.id == recursive_query.c.root_id,
            )
        )

        for root_model, ancestor_model in session.execute(stmt):
            ret.append(
                Account(
                    data=account_to_domain_data(root_model),
                    persistence_data=persistence_from_model(root_model),
                    attachments=AccountAttachment(
                        hierarchy=HierarchyAttachment(
                            parent=None,
                            parents=[
                                account_to_domain(parent, None)
                                for parent in ancestor_model
                            ],
                            children=None,
                        )
                    ),
                )
            )

    return ret


def post_ledger_entries(
    session: Session, transaction_id: int, data: Sequence[LedgerEntryData]
):
    l_e_models = ledger_entries_from_domain(
        transaction_id=transaction_id, ledger_entries=data
    )
    session.add_all(l_e_models)
    session.flush()
    return (persistence_from_model(l_e_model) for l_e_model in l_e_models)


def get_ledger_entries_from_filter(
    session: Session, filter_: LedgerEntryFilter
):
    where_clauses = get_persistance_filter_statement(
        filter_.persistence_data_filter, LedgerEntryModel
    )

    # Apply data filters
    data_filter = filter_.data_filter
    if data_filter.transaction_ids:
        stmt = where_clauses.append(
            LedgerEntryModel.transaction_id.in_(data_filter.transaction_ids)
        )
    if data_filter.account_ids:
        stmt = where_clauses.append(
            LedgerEntryModel.account_id.in_(data_filter.account_ids)
        )
    if data_filter.entry_balance:
        stmt = where_clauses.append(
            LedgerEntryModel.entry_balance == data_filter.entry_balance
        )
    if data_filter.amount_range:
        amount_range = data_filter.amount_range
        stmt = where_clauses.append(
            (
                LedgerEntryModel.amount.between(
                    amount_range.start, amount_range.end
                )
            )
        )

    options = []
    included_fields = filter_.included_fields
    if included_fields.include_transaction:
        match included_fields.include_transaction:
            case InclusionType.ID:
                options.append(
                    joinedload(LedgerEntryModel.transaction).load_only(
                        TransactionModel.id
                    )
                )
            case InclusionType.OBJECT:
                options.append(joinedload(LedgerEntryModel.transaction))
            case InclusionType.NONE:
                pass
    if included_fields.include_account:
        match included_fields.include_account:
            case InclusionType.ID:
                options.append(
                    joinedload(LedgerEntryModel.account).load_only(
                        AccountModel.id
                    )
                )
            case InclusionType.OBJECT:
                options.append(selectinload(LedgerEntryModel.account))
            case InclusionType.NONE:
                pass

    stmt = select(LedgerEntryModel).where(*where_clauses).options(*options)
    results = session.execute(stmt).scalars().all()

    ret: list[LedgerEntry[Persisted, LedgerEntryAttacheable]] = []
    for result in results:
        match included_fields.include_transaction:
            case InclusionType.ID:
                transaction = result.transaction_id
            case InclusionType.OBJECT:
                transaction = transaction_to_domain(result.transaction)
            case InclusionType.NONE:
                transaction = None
        match included_fields.include_account:
            case InclusionType.ID:
                account = result.account_id
            case InclusionType.OBJECT:
                account = account_to_domain(result.account)
            case InclusionType.NONE:
                account = None
        attachments = LedgerEntryAttachement(
            transaction=transaction,  # type: ignore
            account=account,  # type: ignore
        )
        ret.append(ledger_entry_to_domain(result, attachments))
    return ret


def update_ledger_entries(
    session: Session, ledger_entries: Sequence[LedgerEntry[Persisted, Any]]
) -> Generator[Persisted, None, None]:
    for l_e in ledger_entries:
        l_e_id = l_e.persistence_data.id
        data: LedgerEntryData = l_e.data
        l_e_model = get_registry(session, l_e_id, LedgerEntryModel)
        if not l_e_model:
            raise ValueError(f"Transaction with ID {l_e_id} not found")

        l_e_model.transaction_id = data.transaction_id
        l_e_model.account_id = data.account_id
        l_e_model.entry_balance = data.entry_balance
        l_e_model.amount = data.amount

        l_e_model.last_updated_at = utcnow()

        yield persistence_from_model(l_e_model)


def remove_ledger_entries(session: Session, entry_ids_to_remove: Iterable[int]):
    for id in entry_ids_to_remove:
        session.execute(
            update(LedgerEntryModel)
            .where(LedgerEntryModel.id == id)
            .values(deactivated_at=utcnow())
        )


def update_recipient(
    session: Session, recipient_id: int, data: TransactionRecipientData
):
    model: TransactionRecipientModel | None = get_registry(
        session, id=recipient_id, table_model=TransactionRecipientModel
    )

    if not model:
        raise ValueError(
            f"TransactionRecipient with ID {recipient_id} not found."
        )

    model.name = data.name
    model.description = data.description
    if data.parent_recipient_id:
        model.parent_recipient_id = data.parent_recipient_id

    model.last_updated_at = utcnow()

    return persistence_from_model(model)


# TODO Study how this complex SQL query works.
def get_recipients_by_filter(
    session: Session,
    filter_: TransactionRecipientFilter,
) -> dict[
    TransactionRecipientModel,
    Sequence[TransactionRecipient[Persisted, TransactionRecipientAttachable]]
    | Sequence[int],
]:
    """This function also returns the recipients,
    not like get_recipient_parents_by_id."""

    where_clauses = get_persistance_filter_statement(
        filter_.persistence_data_filter, TransactionRecipientModel
    )

    # 1. Base statement: Select the model AND track the origin with `root_id`

    # Apply data filters
    if filter_.data_filter.parent_recipient_ids:
        where_clauses.append(
            TransactionRecipientModel.parent_recipient_id.in_(
                filter_.data_filter.parent_recipient_ids
            )
        )
    if filter_.data_filter.names:
        where_clauses.append(
            TransactionRecipientModel.name.in_(filter_.data_filter.names)
        )

    base_stmt = select(
        TransactionRecipientModel, TransactionRecipientModel.id.label("root_id")
    ).where(*where_clauses)

    # 2. Define the root CTE
    root_cte = base_stmt.cte(name="recipient_tree", recursive=True)

    # 3. Define the recursive part
    parent_alias = aliased(TransactionRecipientModel)
    recursive_query = root_cte.union_all(
        select(
            parent_alias,
            root_cte.c.root_id,  # Pass the root_id up the tree
        ).where(parent_alias.id == root_cte.c.parent_recipient_id)
    )

    # 4. Final selection and dictionary grouping
    root_model_alias = aliased(TransactionRecipientModel)
    result_dict = defaultdict(list)

    included_fields = filter_.included_fields
    if (
        included_fields.hierarchy_inclusions.include_all_parents
        == InclusionType.ID
    ):
        # Join CTE back to the root model to get the dict keys
        stmt = (
            select(root_model_alias, recursive_query.c.parent_recipient_id)
            .select_from(recursive_query)
            .join(
                root_model_alias,
                root_model_alias.id == recursive_query.c.root_id,
            )
            .where(recursive_query.c.parent_recipient_id.is_not(None))
        )

        for root_model, parent_id in session.execute(stmt):
            result_dict[root_model].append(parent_id)

    elif (
        included_fields.hierarchy_inclusions.include_all_parents
        == InclusionType.OBJECT
    ):
        # Map the CTE output back to ORM entities
        ancestor_alias = aliased(TransactionRecipientModel, recursive_query)
        stmt = (
            select(root_model_alias, ancestor_alias)
            .select_from(recursive_query)
            .join(
                root_model_alias,
                root_model_alias.id == recursive_query.c.root_id,
            )
        )

        for root_model, ancestor_model in session.execute(stmt):
            result_dict[root_model].append(
                recipient_to_domain(ancestor_model, None)
            )

    return dict(result_dict)


def get_recipient_by_id(
    session: Session, recipient_id: int
) -> TransactionRecipientModel | None:
    return session.scalar(
        select(TransactionRecipientModel).where(
            TransactionRecipientModel.id == recipient_id,
            TransactionRecipientModel.deactivated_at.is_(None),
        )
    )


def get_recipient_parents_by_id(
    session: Session,
    recipient_id: int,
    attached_data: Literal["ids", "model"] = "ids",
) -> Sequence[TransactionRecipientModel] | Sequence[int]:
    # 1. Define the base anchor (always use the model for the CTE to
    #    keep data available)
    root_cte = (
        select(TransactionRecipientModel)
        .where(
            TransactionRecipientModel.id == recipient_id,
            TransactionRecipientModel.deactivated_at.is_(None),
        )
        .cte(name="recipient_tree", recursive=True)
    )

    # 2. Define the recursive part
    parent_alias = aliased(TransactionRecipientModel)
    recursive_query = root_cte.union_all(
        select(parent_alias).where(
            parent_alias.id == root_cte.c.parent_recipient_id
        )
    )

    # 3. Final selection based on requested type
    if attached_data == "ids":
        # Extract just the parent column from the CTE results
        stmt = select(recursive_query.c.parent_recipient_id).where(
            recursive_query.c.parent_recipient_id.is_not(None)
        )
    else:
        # Map the CTE results back to the Model
        stmt = select(TransactionRecipientModel).from_statement(
            select(recursive_query)
        )

    return session.scalars(stmt).all()


def update_memo(session: Session, memo_id: int, data: MemoData):
    model: MemoModel | None = get_registry(
        session, id=memo_id, table_model=MemoModel
    )

    if not model:
        raise ValueError(f"TransactionRecipient with ID {memo_id} not found.")

    model.date = data.date
    model.receiver = data.receiver
    model.emitter = data.emitter
    model.subject = data.subject
    model.message = data.message
    model.authorized_by = data.authorized_by

    model.last_updated_at = utcnow()

    return persistence_from_model(model)


def get_memo_filter_clauses(memo_data_filter: MemoDataFilter):
    where_clauses: list[BinaryExpression | ColumnElement] = []
    if memo_data_filter.date_range:
        date_range = memo_data_filter.date_range
        where_clauses.append(
            MemoModel.date.between(date_range.start, date_range.end)
        )
    if memo_data_filter.receivers:
        where_clauses.append(MemoModel.date.in_(memo_data_filter.receivers))
    if memo_data_filter.emitters:
        where_clauses.append(MemoModel.emitter.in_(memo_data_filter.emitters))
    if memo_data_filter.subject:
        where_clauses.append(MemoModel.subject.in_(memo_data_filter.subject))
    if memo_data_filter.authorizer:
        where_clauses.append(
            MemoModel.authorized_by.in_(memo_data_filter.authorizer)
        )

    return where_clauses


def get_memo_option_clauses(included_fields: MemoIncludedFields):
    options = []
    match included_fields.include_transaction:
        case InclusionType.ID:
            options.append(
                joinedload(MemoModel.transactions).load_only(
                    TransactionModel.id
                )
            )
        case InclusionType.OBJECT:
            options.append(joinedload(MemoModel.transactions))
        case InclusionType.NONE:
            pass
    return options


def get_memos_by_filter(session: Session, filter_: MemoFilter):
    where_clauses = get_persistance_filter_statement(
        filter_.persistence_data_filter, MemoModel
    )
    where_clauses.extend(get_memo_filter_clauses(filter_.data_filter))
    options = get_memo_option_clauses(filter_.included_fields)

    stmt: Select[Tuple[MemoModel]] = (
        select(MemoModel).where(*where_clauses).options(*options)
    )
    results = session.execute(stmt).scalars().all()

    match filter_.included_fields.include_transaction:
        case InclusionType.ID:

            def fn1(memo_model: MemoModel) -> list[int]:
                return [y.id for y in memo_model.transactions]

            include_transaction = fn1
        case InclusionType.OBJECT:

            def fn2(
                memo_model: MemoModel,
            ) -> list[Transaction[Persisted, None]]:
                return [
                    transaction_to_domain(y) for y in memo_model.transactions
                ]

            include_transaction = fn2
        case InclusionType.NONE:
            include_transaction = None

    ret: list[Memo[Persisted, MemoAttachable]] = []
    for result in results:
        if include_transaction:
            attachments = MemoAttachment(include_transaction(result))
        else:
            attachments = None
        ret.append(memo_to_domain(result, attachments))

    return ret


def get_persistance_filter_statement[T: RegistryMetadataMixin](
    persistence_data_filter: PersistenceDataFilter, table_model: type[T]
):
    where_clauses: list[BinaryExpression | ColumnElement] = []

    if persistence_data_filter.id_set:
        where_clauses.append(table_model.id.in_(persistence_data_filter.id_set))
    if persistence_data_filter.created_at_range:
        date_range = persistence_data_filter.created_at_range
        where_clauses.append(
            table_model.created_at.between(date_range.start, date_range.end)
        )
    if persistence_data_filter.last_updated_at_range:
        date_range = persistence_data_filter.last_updated_at_range
        where_clauses.append(
            table_model.last_updated_at.between(
                date_range.start, date_range.end
            )
        )
    if persistence_data_filter.deactivated_at_range:
        date_range = persistence_data_filter.deactivated_at_range
        where_clauses.append(
            table_model.deactivated_at.between(date_range.start, date_range.end)
        )
    else:  # unless deactivation date filter is explicit, results not included.
        where_clauses.append(table_model.deactivated_at.is_(None))

    return where_clauses
