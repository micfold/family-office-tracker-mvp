from abc import ABC, abstractmethod
from typing import List
from uuid import UUID
from src.domain.models.MAsset import Asset


class BaseRepository(ABC):
    """Generic repository interface."""
    pass


class AssetRepository(BaseRepository):
    @abstractmethod
    def get_all(self, user_id: UUID) -> List[Asset]:
        """Retrieve all assets for a specific user."""
        pass

    @abstractmethod
    def save(self, asset: Asset) -> None:
        """Save or update a single asset."""
        pass

    @abstractmethod
    def delete(self, asset_id: UUID) -> None:
        """Remove an asset."""
        pass

    @abstractmethod
    def save_all(self, assets: List[Asset]) -> None:
        """Bulk save (useful for the JSON rewriting)."""
        pass