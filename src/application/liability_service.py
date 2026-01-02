# src/application/liability_service.py
from typing import List
from uuid import UUID
from decimal import Decimal
import streamlit as st

from src.domain.models.MLiability import Liability
from src.domain.enums import LiabilityCategory
from src.domain.repositories.liability_repository import LiabilityRepository


def _get_current_user_id() -> UUID:
    user = st.session_state.get("user")
    if not user:
        raise PermissionError("No user logged in")
    return UUID(user["id"])


class LiabilityService:
    def __init__(self, repo: LiabilityRepository):
        self.repo = repo

    def get_user_liabilities(self) -> List[Liability]:
        uid = _get_current_user_id()
        return self.repo.get_all(uid)

    def create_liability(self,
                         name: str,
                         amount: Decimal,
                         liability_type: LiabilityCategory,
                         **kwargs) -> Liability:
        uid = _get_current_user_id()

        new_liab = Liability(
            name=name,
            amount=abs(amount),  # Store as positive debt
            liability_type=liability_type,
            owner=uid,
            **kwargs
        )
        self.repo.save(new_liab)
        return new_liab

    def update_liability_details(self, liability: Liability, **kwargs) -> None:
        """
        Updates any field passed in kwargs (name, amount, interest_rate, etc.)
        """
        for key, value in kwargs.items():
            if hasattr(liability, key):
                if key == 'amount':
                    setattr(liability, key, abs(value))
                else:
                    setattr(liability, key, value)

        self.repo.save(liability)

    def delete_liability(self, liability_id: UUID) -> None:
        self.repo.delete(liability_id)

    def get_total_liabilities(self) -> Decimal:
        liabs = self.get_user_liabilities()
        return sum((l.amount for l in liabs), Decimal(0))