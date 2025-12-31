# services/portfolio.py
import pandas as pd
from services.auth import AuthService


class PortfolioService:
    def __init__(self):
        self.auth = AuthService()

    def load_data(self):
        """Returns a dict with snapshot and history dataframes."""
        s_path = self.auth.get_file_path("portfolio_snapshot.csv")
        h_path = self.auth.get_file_path("portfolio_history.csv")

        data = {"snapshot": None, "history": None}

        if s_path.exists():
            data["snapshot"] = pd.read_csv(s_path)
            # Add processing/cleaning logic here if needed

        if h_path.exists():
            data["history"] = pd.read_csv(h_path)
            data["history"]['Date'] = pd.to_datetime(data["history"]['Date'])

        return data

    def save_file(self, file_obj, type_key):
        """Saves uploaded portfolio files."""
        filename = "portfolio_snapshot.csv" if type_key == "snapshot" else "portfolio_history.csv"
        path = self.auth.get_file_path(filename)

        with open(path, "wb") as f:
            f.write(file_obj.getbuffer())