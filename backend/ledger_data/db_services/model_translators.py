from typing import Iterable

from ..domain.resources import (
    Account,
    AccountAttachable,
    AccountData,
    LedgerEntry,
    LedgerEntryAttacheable,
    LedgerEntryData,
    Memo,
    MemoAttachable,
    MemoData,
    Persisted,
    Transaction,
    TransactionAttachable,
    TransactionData,
    TransactionRecipient,
    TransactionRecipientAttachable,
    TransactionRecipientData,
    TransactionType,
    TransactionTypeAttachable,
    TransactionTypeData,
    TransactionTypePeriodicity,
)
from .models.resource_models import (
    AccountModel,
    LedgerEntryModel,
    MemoModel,
    RegistryMetadataMixin,
    TransactionModel,
    TransactionRecipientModel,
    TransactionTypeModel,
)


def persistence_from_model(model: RegistryMetadataMixin):
    return Persisted(
        id=model.id,
        created_at=model.created_at,
        last_updated_at=model.last_updated_at,
        deactivated_at=model.last_updated_at,
    )


# TODO add the attributes post object creation
# (this avoids issues)
def transaction_from_domain(transaction: TransactionData):
    return TransactionModel(
        transaction_date=transaction.transaction_date,
        reference=transaction.reference,
        transaction_type_id=transaction.transaction_type_id,
        description=transaction.description,
        memo_id=transaction.memo_id,
    )


def transaction_to_domain_data(transaction_model: TransactionModel):
    return TransactionData(
        transaction_date=transaction_model.transaction_date,
        reference=transaction_model.reference,
        transaction_type_id=transaction_model.transaction_type_id,
        description=transaction_model.description,
        memo_id=transaction_model.memo_id,
    )


def transaction_to_domain[T: TransactionAttachable](
    transaction_model: TransactionModel,
    attachments: T = None,
) -> Transaction[Persisted, T]:
    return Transaction(
        data=transaction_to_domain_data(transaction_model),
        persistence_data=persistence_from_model(transaction_model),
        attachments=attachments,
    )


def transaction_type_to_domain_data(
    model: TransactionTypeModel,
) -> TransactionTypeData:
    return TransactionTypeData(
        name=model.name,
        description=model.description,
        periodicity=TransactionTypePeriodicity(model.periodicity.value),
        parent_type_id=model.parent_type_id,
    )


def transaction_type_to_domain[T: TransactionTypeAttachable](
    transaction_type_model: TransactionTypeModel,
    attachments: T = None,
) -> TransactionType[Persisted, T]:
    return TransactionType(
        data=transaction_type_to_domain_data(transaction_type_model),
        persistence_data=persistence_from_model(transaction_type_model),
        attachments=attachments,
    )


def transaction_type_from_domain_data(data: TransactionTypeData):
    model = TransactionTypeModel()
    model.name = data.name
    model.description = data.description
    model.periodicity = data.periodicity
    model.parent_type_id = data.parent_type_id

    return model


def account_to_domain_data(account_model: AccountModel):
    return AccountData(
        code=account_model.code,
        currency=account_model.currency,
        name=account_model.name,
        description=account_model.description,
        parent_account_id=account_model.parent_account_id,
    )


def account_to_domain[T: AccountAttachable](
    account_model: AccountModel, attachments: T = None
) -> Account[Persisted, T]:
    return Account(
        data=account_to_domain_data(account_model),
        persistence_data=persistence_from_model(account_model),
        attachments=attachments,
    )


def account_from_domain_data(data: AccountData):
    model = AccountModel()
    model.code = data.code
    model.currency = data.currency
    model.name = data.name
    model.description = data.description
    return model


def ledger_entry_to_domain_data(ledger_entry_model: LedgerEntryModel):
    return LedgerEntryData(
        transaction_id=ledger_entry_model.transaction_id,
        account_id=ledger_entry_model.account_id,
        entry_balance=ledger_entry_model.entry_balance,
        amount=ledger_entry_model.amount,
    )


def ledger_entry_to_domain[T: LedgerEntryAttacheable](
    ledger_entry_model: LedgerEntryModel,
    attachments: T = None,
) -> LedgerEntry[Persisted, T]:
    return LedgerEntry(
        data=ledger_entry_to_domain_data(ledger_entry_model),
        persistence_data=persistence_from_model(ledger_entry_model),
        attachments=attachments,
    )


# TODO use a for loop to add the attributes post object creation
# (this avoids issues)
def ledger_entries_from_domain(
    ledger_entries: Iterable[LedgerEntryData], transaction_id: int
) -> tuple[LedgerEntryModel, ...]:
    return tuple(
        LedgerEntryModel(
            transaction_id=transaction_id,
            account_id=ledger_entry.account_id,
            entry_balance=ledger_entry.entry_balance,
            amount=ledger_entry.amount,
        )
        for ledger_entry in ledger_entries
    )


def ledger_entries_to_domain(
    ledger_entries: Iterable[LedgerEntryModel],
) -> tuple[LedgerEntry[Persisted, None], ...]:
    return tuple(
        LedgerEntry(
            data=ledger_entry_to_domain_data(ledger_entry),
            persistence_data=persistence_from_model(ledger_entry),
            attachments=None,
        )
        for ledger_entry in ledger_entries
    )


def recipient_from_domain_data(data: TransactionRecipientData):
    model = TransactionRecipientModel()
    model.name = data.name
    model.description = data.description
    model.parent_recipient_id = data.parent_recipient_id
    return model


def recipient_to_domain_data(recipient_model: TransactionRecipientModel):
    return TransactionRecipientData(
        name=recipient_model.name,
        description=recipient_model.description,
        parent_recipient_id=recipient_model.parent_recipient_id,
    )


def recipient_to_domain[T: TransactionRecipientAttachable](
    recipient: TransactionRecipientModel,
    attachments: T = None,
) -> TransactionRecipient[Persisted, T]:
    return TransactionRecipient(
        data=recipient_to_domain_data(recipient),
        persistence_data=persistence_from_model(recipient),
        attachments=attachments,
    )


def recipients_to_domain(
    recipients: Iterable[TransactionRecipientModel],
) -> tuple[TransactionRecipient[Persisted, None], ...]:
    return tuple(
        recipient_to_domain(recipient, None) for recipient in recipients
    )


def memo_to_domain_data(memo_model: MemoModel):
    return MemoData(
        date=memo_model.date,
        receiver=memo_model.receiver,
        emitter=memo_model.emitter,
        subject=memo_model.subject,
        message=memo_model.message,
        authorized_by=memo_model.authorized_by,
    )


def memo_to_domain(memo_model: MemoModel, attachments: MemoAttachable = None):
    return Memo(
        data=memo_to_domain_data(memo_model),
        persistence_data=persistence_from_model(memo_model),
        attachments=attachments,
    )


def memo_from_domain_data(memo_data: MemoData) -> MemoModel:
    model = MemoModel()
    model.date = memo_data.date
    model.receiver = memo_data.receiver
    model.emitter = memo_data.emitter
    model.subject = memo_data.subject
    model.message = memo_data.message
    model.authorized_by = memo_data.authorized_by
    return model
