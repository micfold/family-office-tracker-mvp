from typing import List, Dict
from uuid import UUID
from decimal import Decimal
import streamlit as st

from src.domain.models.MAsset import Asset, NetWorthSnapshot
from src.domain.enums import AssetCategory
from src.domain.repositories.asset_repository import AssetRepository


def _get_current_user_id() -> UUID:
    user = st.session_state.get("user")
    if not user:
        raise PermissionError("No user logged in")
    return UUID(user["id"])


class AssetService:
    def __init__(self, repo: AssetRepository):
        self.repo = repo

    def get_user_assets(self) -> List[Asset]:
        uid = _get_current_user_id()
        return self.repo.get_all(uid)

    def update_asset_value(self, asset: Asset, new_value: Decimal) -> None:
        asset.value = new_value
        self.repo.save(asset)

    def create_asset(self,
                     name: str,
                     category: AssetCategory,
                     value: Decimal,
                     **kwargs) -> Asset:
        """
        Universal create method that accepts extra fields via kwargs.
        """
        uid = _get_current_user_id()

        new_asset = Asset(
            name=name,
            category=category,
            value=value,
            owner=uid,
            **kwargs  # Pass all the extra fields (address, brand, etc.) to the model
        )
        self.repo.save(new_asset)
        return new_asset

    def create_simple_asset(self, name: str, category: AssetCategory, value: Decimal) -> Asset:
        uid = _get_current_user_id()

        new_asset = Asset(
            name=name,
            category=category,
            value=value,
            owner=uid
        )
        self.repo.save(new_asset)
        return new_asset

    def delete_asset(self, asset_id: UUID) -> None:
        self.repo.delete(asset_id)

    def get_net_worth_snapshot(self) -> NetWorthSnapshot:
        assets = self.get_user_assets()

        total_assets = sum((a.value for a in assets if a.value >= 0), Decimal(0))
        total_liabilities = sum((-a.value for a in assets if a.value < 0), Decimal(0))

        return NetWorthSnapshot(
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            net_worth=total_assets - total_liabilities
        )