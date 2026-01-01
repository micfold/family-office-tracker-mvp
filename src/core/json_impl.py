import json
from typing import List
from uuid import UUID
from pathlib import Path
from decimal import Decimal

from src.domain.repositories.asset_repository import AssetRepository
from src.domain.models.MAsset import Asset
from services.auth import AuthService

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

class JsonAssetRepository(AssetRepository):
    def __init__(self):
        self.auth = AuthService()
        self.filename = "assets_v2.json"  # New filename to avoid breaking your current demo

    def _get_path(self) -> Path:
        return self.auth.get_file_path(self.filename)

    def get_all(self, user_id: UUID) -> List[Asset]:
        path = self._get_path()
        if not path.exists():
            return []

        try:
            data = json.loads(path.read_text())
            # Convert JSON list to Pydantic objects
            return [Asset(**item) for item in data]
        except Exception as e:
            print(f"Error loading assets: {e}")
            return []

    def save(self, asset: Asset) -> None:
        # Load all, replace/append, save back
        # (Inefficient for SQL, but standard for JSON)
        path = self._get_path()
        current_assets = self.get_all(asset.owner)

        # Remove existing version of this asset if it exists
        updated_list = [a for a in current_assets if a.id != asset.id]
        updated_list.append(asset)

        self.save_all(updated_list)

    def delete(self, asset_id: UUID) -> None:
        path = self._get_path()
        # We need the user context to load the file, currently derived from Auth inside _get_path
        # In a real DB, we would just delete by ID.
        # For JSON, we load the list from the current user's file.
        # Note: Ideally, get_all shouldn't need user_id if the file path is already user-specific.
        # But for interface consistency, we keep it.

        # We assume the current file belongs to the logged-in user
        # This is a limitation of the File-based system vs DB.
        existing = self.get_all(None)
        updated = [a for a in existing if a.id != asset_id]
        self.save_all(updated)

    def save_all(self, assets: List[Asset]) -> None:
        path = self._get_path()
        # Convert Pydantic objects to JSON-serializable dicts
        # mode='json' converts Decimals to strings/floats automatically
        data = [a.model_dump(mode='json') for a in assets]
        path.write_text(json.dumps(data, indent=2))