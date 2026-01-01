import pandas as pd
import re
from typing import List
from uuid import UUID
from pathlib import Path
from decimal import Decimal

from src.application.auth_service import AuthService
from src.domain.repositories.portfolio_repository import PortfolioRepository
from src.domain.models.MPortfolio import InvestmentPosition, InvestmentEvent
from src.domain.enums import Currency

# Static FX Rates (Moved from legacy modules)
FX_RATES = {'USD': 23.5, 'EUR': 25.2, 'GBP': 29.5, 'CZK': 1.0}


def _clean_numeric(val) -> Decimal:
    """Helper to parse locale-specific numbers to Decimal."""
    if pd.isna(val): return Decimal(0)
    s = re.sub(r'[^\d.,-]', '', str(val))
    if not s: return Decimal(0)

    # European vs US format heuristic
    if ',' in s and '.' in s:
        if s.find('.') > s.find(','):  # 1.000,00
            s = s.replace(',', '')
        else:  # 1,000.00
            s = s.replace('.', '').replace(',', '.')
    elif ',' in s:  # 100,00 assumed decimal
        s = s.replace(',', '.')

    try:
        return Decimal(s)
    except:
        return Decimal(0)


class CsvPortfolioRepository(PortfolioRepository):
    def __init__(self):
        self.auth = AuthService()
        self.snap_file = "portfolio_snapshot.csv"
        self.hist_file = "portfolio_history.csv"

    def _get_path(self, filename: str) -> Path:
        return self.auth.get_file_path(filename)

    def get_snapshot(self, user_id: UUID) -> List[InvestmentPosition]:
        path = self._get_path(self.snap_file)
        if not path.exists(): return []

        try:
            df = pd.read_csv(path)
            positions = []

            # Legacy Column Mapping (Snowball/T212 style)
            # Adjust these keys based on your actual CSV format
            col_map = {
                'ticker': ['Symbol', 'Ticker'],
                'name': ['Name', 'Holding'],
                'qty': ['Quantity', 'Shares'],
                'price': ['Price', 'Current price'],
                'value': ['Value', 'Current value', 'Amount'],
                'cost': ['Cost basis', 'Total cost'],
                'sector': ['Sector']
            }

            def get_val(row, keys):
                for k in keys:
                    if k in row: return row[k]
                return None

            for _, row in df.iterrows():
                # Value cleaning
                qty = _clean_numeric(get_val(row, col_map['qty']))
                price = _clean_numeric(get_val(row, col_map['price']))
                val = _clean_numeric(get_val(row, col_map['value']))
                cost = _clean_numeric(get_val(row, col_map['cost']))

                # Basic calculation if missing
                if val == 0 and price > 0 and qty > 0:
                    val = price * qty

                # Calc yield
                div_yield = _clean_numeric(row.get('Dividend yield', 0))

                pos = InvestmentPosition(
                    ticker=str(get_val(row, col_map['ticker']) or "UNK"),
                    name=str(get_val(row, col_map['name']) or "Unknown"),
                    quantity=qty,
                    current_price=price,
                    cost_basis=cost,
                    market_value=val,
                    gain_loss=val - cost,
                    dividend_yield_projected=div_yield,
                    projected_annual_income=val * (div_yield / Decimal(100)),
                    sector=str(get_val(row, col_map['sector']) or "Other"),
                    owner=user_id
                )
                positions.append(pos)
            return positions
        except Exception as e:
            print(f"Error parsing snapshot: {e}")
            return []

    def get_history(self, user_id: UUID) -> List[InvestmentEvent]:
        path = self._get_path(self.hist_file)
        if not path.exists(): return []

        try:
            df = pd.read_csv(path)
            events = []

            for _, row in df.iterrows():
                # FX Conversion Logic
                curr = str(row.get('Currency', 'CZK')).upper()
                rate = Decimal(FX_RATES.get(curr, 1.0))

                raw_amt = _clean_numeric(row.get('Amount') or row.get('Total', 0))
                # Normalize to CZK
                amt_czk = raw_amt * rate

                evt = InvestmentEvent(
                    date=pd.to_datetime(row.get('Date')),
                    ticker=str(row.get('Symbol') or row.get('Ticker', 'CASH')),
                    event_type=str(row.get('Event') or row.get('Action', 'UNK')),
                    quantity=_clean_numeric(row.get('Quantity')),
                    price_per_share=_clean_numeric(row.get('Price')),
                    total_amount=amt_czk,
                    currency=Currency.CZK,
                    owner=user_id
                )
                events.append(evt)
            return events
        except Exception as e:
            print(f"Error parsing history: {e}")
            return []

    def save_snapshot_file(self, file_obj) -> None:
        path = self._get_path(self.snap_file)
        with open(path, "wb") as f:
            f.write(file_obj.getbuffer())

    def save_history_file(self, file_obj) -> None:
        path = self._get_path(self.hist_file)
        with open(path, "wb") as f:
            f.write(file_obj.getbuffer())