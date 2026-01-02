# src/core/ingestion/base.py
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

@dataclass
class NormalizedTransaction:
    date: date
    description: str
    amount: Decimal
    currency: str = "CZK"
    source_account: Optional[str] = None
    target_account: Optional[str] = None
    raw_source: str = ""

class IngestionStrategy(ABC):
    @abstractmethod
    def can_handle(self, filename: str, content: bytes) -> bool:
        pass

    @abstractmethod
    def parse(self, filename: str, content: bytes) -> Tuple[List[NormalizedTransaction], Optional[str]]:
        """
        Returns: (List of Transactions, Error Message if any)
        If list is empty and Error Message is set, it failed.
        """
        pass