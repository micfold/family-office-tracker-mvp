# src/application/ingestion_service.py
from typing import List, Tuple
from uuid import UUID
from src.core.ingestion.csv_strategy import CsvBankStrategy
from src.domain.models.MTransaction import Transaction
from src.domain.enums import TransactionType
from src.application.rule_service import RuleService


class IngestionService:
    def __init__(self, rule_service: RuleService):
        self.strategies = [CsvBankStrategy()]
        self.rule_svc = rule_service

    def process_file(self, filename: str, content: bytes, user_id: UUID, batch_id: str) -> Tuple[
        List[Transaction], List[str]]:
        """Returns (Transactions, LogMessages)"""
        handler = next((s for s in self.strategies if s.can_handle(filename, content)), None)
        if not handler:
            return [], [f"No parser found for file: {filename}"]

        normalized_txs, error_msg = handler.parse(filename, content)

        if error_msg:
            return [], [f"File {filename}: {error_msg}"]

        if not normalized_txs:
            return [], [f"File {filename}: Parsed 0 transactions."]

        domain_txs = []
        for n_tx in normalized_txs:
            # AI / Rule Lookup
            cat, t_type = self.rule_svc.find_category(n_tx.description, user_id)

            if not t_type:
                t_type = TransactionType.EXPENSE if n_tx.amount < 0 else TransactionType.INCOME

            tx = Transaction(
                date=n_tx.date,
                description=n_tx.description,
                amount=n_tx.amount,
                currency=n_tx.currency,
                category=cat,
                transaction_type=t_type,
                batch_id=batch_id,
                owner=user_id
            )
            domain_txs.append(tx)

        return domain_txs, []