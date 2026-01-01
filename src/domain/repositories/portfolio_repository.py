from abc import ABC, abstractmethod
from typing import List, Tuple
from uuid import UUID
import pandas as pd  # Allowing DF for complex charts
from src.domain.models.MPortfolio import InvestmentPosition, InvestmentEvent


class PortfolioRepository(ABC):
    @abstractmethod
    def get_snapshot(self, user_id: UUID) -> List[InvestmentPosition]:
        """Get current holdings."""
        pass

    @abstractmethod
    def get_history(self, user_id: UUID) -> List[InvestmentEvent]:
        """Get transaction log."""
        pass

    @abstractmethod
    def save_snapshot_file(self, file_obj) -> None:
        """Save raw snapshot CSV."""
        pass

    @abstractmethod
    def save_history_file(self, file_obj) -> None:
        """Save raw history CSV."""
        pass