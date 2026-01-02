# src/application/ingestion_service.py
from decimal import Decimal
from typing import List, Tuple, Set
from uuid import UUID
from src.core.ingestion.csv_strategy import CsvBankStrategy
from src.domain.models.MTransaction import Transaction
from src.domain.enums import TransactionType
from src.application.rule_service import RuleService
from src.application.asset_service import AssetService


class IngestionService:
    def __init__(self, rule_service: RuleService, asset_service: AssetService):
        self.strategies = [CsvBankStrategy()]
        self.rule_svc = rule_service
        self.asset_svc = asset_service

    def process_file(self, filename: str, content: bytes, user_id: UUID, batch_id: str) -> Tuple[
        List[Transaction], List[str]]:
        handler = next((s for s in self.strategies if s.can_handle(filename, content)), None)
        if not handler:
            return [], [f"No parser found for file: {filename}"]

        normalized_txs, error_msg = handler.parse(filename, content)
        if error_msg:
            return [], [f"File {filename}: {error_msg}"]

        if not normalized_txs:
            return [], [f"File {filename}: Parsed 0 transactions."]

        # 1. Fetch User Accounts for "Internal Transfer" detection
        user_assets = self.asset_svc.get_user_assets()
        my_accounts: Set[str] = set()
        for a in user_assets:
            if a.account_number: my_accounts.add(a.account_number.replace(" ", ""))
            if a.iban: my_accounts.add(a.iban.replace(" ", ""))

        domain_txs = []
        for n_tx in normalized_txs:
            # 2. Check for Internal Transfer
            # If the target account is in my_accounts, it's a transfer!
            target_clean = (n_tx.target_account or "").replace(" ", "")
            is_internal = target_clean in my_accounts and target_clean != ""

            if is_internal:
                cat = "Internal Transfer"
                t_type = TransactionType.TRANSFER
            else:
                # 3. AI / Rule Lookup
                cat, t_type = self.rule_svc.find_category(n_tx.description, user_id)

                # 4. Default / Fallback Rules (The "KFC" Fix)
                if not t_type or cat == "Uncategorized":
                    cat, t_type = self._apply_fallback_rules(n_tx.description, n_tx.amount)

            tx = Transaction(
                date=n_tx.date,
                description=n_tx.description,
                amount=n_tx.amount,
                currency=n_tx.currency,
                category=cat,
                transaction_type=t_type,
                source_account=n_tx.source_account,  # We keep this for audit, even if View hides it
                target_account=n_tx.target_account,
                batch_id=batch_id,
                owner=user_id
            )
            domain_txs.append(tx)

        return domain_txs, []

    def _apply_fallback_rules(self, desc: str, amount: Decimal) -> Tuple[str, TransactionType]:
        """Hardcoded defaults if AI/Vector DB misses."""
        d = desc.lower()

        # Fast Food / Dining
        if any(x in d for x in ['kfc', 'mcdonald', 'burger king', 'starbucks', 'costa coffee']):
            return "Dining Out", TransactionType.EXPENSE

        # Groceries
        if any(x in d for x in ['tesco', 'lidl', 'kaufland', 'albert', 'billa', 'rohlik', 'kosik']):
            return "Groceries", TransactionType.EXPENSE

        # Transport
        if any(x in d for x in ['shell', 'omv', 'mol', 'benzina', 'uber', 'bolt']):
            return "Transport", TransactionType.EXPENSE

        # Default
        t_type = TransactionType.EXPENSE if amount < 0 else TransactionType.INCOME
        return "Uncategorized", t_type