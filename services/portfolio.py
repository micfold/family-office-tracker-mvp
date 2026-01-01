# services/portfolio.py
import pandas as pd
from services.auth import AuthService
from modules.portfolio import process_snapshot, process_history


class PortfolioService:
    def __init__(self):
        self.auth = AuthService()

    def load_data(self):
        """Returns a dict with snapshot and history dataframes."""
        s_path = self.auth.get_file_path("portfolio_snapshot.csv")
        h_path = self.auth.get_file_path("portfolio_history.csv")

        data = {"snapshot": None, "history": None}

        if s_path.exists():
            try:
                df = pd.read_csv(s_path)
                data["snapshot"] = process_snapshot(df)
            except Exception as e:
                print(f"Error loading snapshot: {e}")

        if h_path.exists():
            try:
                df = pd.read_csv(h_path)
                data["history"] = process_history(df)
            except Exception as e:
                print(f"Error processing history: {e}")
        return data

    def save_file(self, file_obj, type_key):
        """Saves uploaded portfolio files."""
        filename = "portfolio_snapshot.csv" if type_key == "snapshot" else "portfolio_history.csv"
        path = self.auth.get_file_path(filename)

        with open(path, "wb") as f:
            f.write(file_obj.getbuffer())