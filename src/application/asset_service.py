from typing import List
from uuid import UUID
from decimal import Decimal
import streamlit as st

from src.domain.models.MAsset import Asset, NetWorthSnapshot
from src.domain.enums import AssetCategory
from src.domain.repositories.asset_repository import AssetRepository
from src.views.utils import calculate_vehicle_amortization


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

    def update_asset_value(self, asset_id: UUID, new_value: Decimal = None, **kwargs) -> None:
        """
        Update an asset by id. The view should pass the asset id and updated fields;
        the service mutates the domain model and persists it via the repository.
        """
        uid = _get_current_user_id()
        assets = self.repo.get_all(uid)
        # Find the asset by id
        target = None
        for a in assets:
            if str(a.id) == str(asset_id):
                target = a
                break
        if not target:
            raise ValueError(f"Asset not found: {asset_id}")

        # Apply updates
        if new_value is not None:
            target.value = new_value

        for key, val in kwargs.items():
            if hasattr(target, key):
                setattr(target, key, val)

        self.repo.save(target)

    def create_asset(self, category: AssetCategory, value: Decimal, **kwargs):
        uid = _get_current_user_id()

        # For vehicles, the initial 'value' is the acquisition price.
        if category == AssetCategory.VEHICLE:
            kwargs['acquisition_price'] = value

        asset = Asset(
            category=category,
            value=value,
            owner=uid,
            **kwargs
        )
        self.repo.save(asset)

    def delete_asset(self, asset_id: UUID):
        self.repo.delete(asset_id)

    def run_vehicle_amortization_update(self, vehicle_id: UUID, current_kilometers: int):
        """
        Updates the market value of a specific vehicle based on new mileage.
        """
        uid = _get_current_user_id()
        vehicle = next((a for a in self.get_user_assets() if a.id == vehicle_id and a.category == AssetCategory.VEHICLE), None)

        if vehicle and vehicle.acquisition_price and vehicle.year_made:
            estimated_value = calculate_vehicle_amortization(
                acquisition_price=vehicle.acquisition_price,
                year_made=vehicle.year_made,
                kilometers_driven=current_kilometers
            )
            self.update_asset_value(vehicle.id, new_value=estimated_value, kilometers_driven=current_kilometers)

    def get_net_worth_snapshot(self) -> NetWorthSnapshot:
        assets = self.get_user_assets()

        total_assets = sum((a.value for a in assets if a.value >= 0), Decimal(0))
        total_liabilities = sum((-a.value for a in assets if a.value < 0), Decimal(0))

        return NetWorthSnapshot(
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            net_worth=total_assets - total_liabilities
        )