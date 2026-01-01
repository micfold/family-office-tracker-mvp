from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import date
import pandas as pd # Pragmatic choice: we allow returning DFs for analytics
from src.domain.models.MTransaction import Transaction

class TransactionRepository(ABC):
    @abstractmethod
    def get_all(self, user_id: UUID) -> List[Transaction]:
        """Retrieve all transactions as Domain Objects."""
        pass

    @abstractmethod
    def get_as_dataframe(self, user_id: UUID) -> pd.DataFrame:
        """Retrieve as DataFrame for heavy analytics/charting."""
        pass

    @abstractmethod
    def save_bulk(self, transactions: List[Transaction]) -> None:
        """Bulk save for uploads."""
        pass

    @abstractmethod
    def delete_batch(self, batch_id: str, user_id: UUID) -> None:
        """Delete a specific import batch."""
        pass