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

    def create_simple_asset(self, name: str, category: AssetCategory, value: Decimal) -> Asset:
        # Owner is handled by the default_factory in the Model,
        # but relying on that during Service calls is risky if context is missing.
        # Ideally, we pass it explicitly:
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

        total_a = Decimal(0)
        total_l = Decimal(0)

        return NetWorthSnapshot(
            total_assets=total_a,
            total_liabilities=total_l,
            net_worth=total_a - total_l
        )

    def migrate_legacy_data(self, legacy_file_path):
        """One-time migration helper."""
        if not legacy_file_path.exists():
            return False

        try:
            old_data = st.json.loads(legacy_file_path.read_text())

            # 1. Real Estate
            re = old_data.get("Real Estate", {})
            if isinstance(re, dict):
                for k, v in re.items():
                    self.create_simple_asset(k, AssetCategory.REAL_ESTATE, Decimal(v))
            else:
                self.create_simple_asset("Property", AssetCategory.REAL_ESTATE, Decimal(re))

            # 2. Vehicles
            if "Vehicles" in old_data:
                self.create_simple_asset("Main Vehicle", AssetCategory.VEHICLE, Decimal(old_data["Vehicles"]))

            # 3. Cash
            cash = old_data.get("Cash", {})
            if isinstance(cash, dict):
                for k, v in cash.items():
                    self.create_simple_asset(k, AssetCategory.CASH, Decimal(v))

            # 4. Mortgage
            if "Mortgage" in old_data:
                self.create_simple_asset("Primary Mortgage", AssetCategory.LIABILITY, Decimal(old_data["Mortgage"]))

            return True
        except Exception as e:
            print(f"Migration failed: {e}")
            return False