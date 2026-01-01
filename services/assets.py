import json
from services.auth import AuthService


class AssetsService:
    def __init__(self):
        self.auth = AuthService()
        self.filename = "assets.json"
        self.defaults = {
            "Real Estate": 0,
            "Vehicles": 0,
            "Mortgage": 0,
            "Cash": {"Emergency": 0, "Wallet": 0, "Savings": 0}
        }

    def load_assets(self):
        """Loads assets from disk or returns defaults."""
        path = self.auth.get_file_path(self.filename)
        data = self.defaults.copy()

        if path.exists():
            try:
                with open(path, 'r') as f:
                    loaded = json.load(f)
                    # Merge nested Cash dictionary carefully
                    if "Cash" in loaded and isinstance(loaded["Cash"], dict):
                        # Ensure defaults exist if not overwritten, but allow user changes
                        merged_cash = data["Cash"].copy()
                        merged_cash.update(loaded["Cash"])
                        data["Cash"] = merged_cash
                        del loaded["Cash"]
                    data.update(loaded)
            except Exception as e:
                print(f"Error loading assets: {e}")

        return data

    def save_assets(self, data):
        """Saves asset dictionary to disk."""
        path = self.auth.get_file_path(self.filename)
        with open(path, 'w') as f:
            json.dump(data, f)