# src/domain/repositories/liability_repository.py
from abc import ABC, abstractmethod
from typing import List
from uuid import UUID
from src.domain.models.MLiability import Liability

class LiabilityRepository(ABC):
    @abstractmethod
    def get_all(self, user_id: UUID) -> List[Liability]:
        pass

    @abstractmethod
    def save(self, liability: Liability) -> None:
        pass

    @abstractmethod
    def delete(self, liability_id: UUID) -> None:
        pass