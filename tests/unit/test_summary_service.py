# tests/unit/test_summary_service.py
"""
Unit tests for SummaryService
Tests aggregation logic, column normalization, and executive summary calculation.
"""
import pytest
import pandas as pd
from unittest.mock import Mock
from decimal import Decimal
from datetime import datetime


@pytest.fixture
def mock_asset_service():
    """Create a mock asset service."""
    service = Mock()
    service.get_user_assets.return_value = []
    return service


@pytest.fixture
def mock_ledger_service():
    """Create a mock ledger service."""
    service = Mock()
    service.get_recent_transactions.return_value = pd.DataFrame()
    return service


@pytest.fixture
def mock_portfolio_service():
    """Create a mock portfolio service."""
    from dataclasses import dataclass
    
    @dataclass
    class MockMetrics:
        total_value: Decimal = Decimal('0')
        total_cost: Decimal = Decimal('0')
        total_gain: Decimal = Decimal('0')
        gain_percent: Decimal = Decimal('0')
    
    service = Mock()
    service.get_portfolio_overview.return_value = ([], MockMetrics())
    return service


@pytest.fixture
def mock_liability_service():
    """Create a mock liability service."""
    service = Mock()
    service.get_total_liabilities.return_value = Decimal('0')
    return service


@pytest.fixture
def summary_service(mock_asset_service, mock_ledger_service, mock_portfolio_service, mock_liability_service):
    """Create a SummaryService instance with mocked dependencies."""
    from src.application.summary_service import SummaryService
    return SummaryService(
        mock_asset_service,
        mock_ledger_service,
        mock_portfolio_service,
        mock_liability_service
    )


class TestExecutiveSummary:
    """Test executive summary calculations."""
    
    def test_empty_summary(self, summary_service):
        """Test executive summary with no data."""
        summary = summary_service.get_executive_summary()
        
        assert summary.net_worth == Decimal('0')
        assert summary.total_assets == Decimal('0')
        assert summary.total_liabilities == Decimal('0')
        assert summary.liquid_cash == Decimal('0')
        assert summary.monthly_income == Decimal('0')
        assert summary.monthly_spend == Decimal('0')
    
    def test_summary_with_assets(self, summary_service, mock_asset_service):
        """Test summary calculation with assets."""
        from dataclasses import dataclass
        
        @dataclass
        class MockAsset:
            value: Decimal
        
        mock_asset_service.get_user_assets.return_value = [
            MockAsset(value=Decimal('10000')),
            MockAsset(value=Decimal('5000'))
        ]
        
        summary = summary_service.get_executive_summary()
        
        assert summary.total_assets >= Decimal('15000')
    
    def test_summary_with_liabilities(self, summary_service, mock_liability_service):
        """Test summary calculation with liabilities."""
        mock_liability_service.get_total_liabilities.return_value = Decimal('50000')
        
        summary = summary_service.get_executive_summary()
        
        assert summary.total_liabilities == Decimal('50000')
        assert summary.net_worth == -Decimal('50000')  # No assets, only liabilities
    
    def test_summary_with_portfolio(self, summary_service, mock_portfolio_service):
        """Test summary calculation with portfolio investments."""
        from dataclasses import dataclass
        
        @dataclass
        class MockMetrics:
            total_value: Decimal = Decimal('25000')
            total_cost: Decimal = Decimal('20000')
            total_gain: Decimal = Decimal('5000')
            gain_percent: Decimal = Decimal('25')
        
        mock_portfolio_service.get_portfolio_overview.return_value = ([], MockMetrics())
        
        summary = summary_service.get_executive_summary()
        
        assert summary.invested_assets == Decimal('25000')
        assert summary.total_assets >= Decimal('25000')


class TestColumnNormalization:
    """Test column name normalization."""
    
    def test_lowercase_column_normalization(self, summary_service, mock_ledger_service):
        """Test that mixed-case columns are normalized to lowercase."""
        # Create DataFrame with mixed-case columns
        data = {
            'Date': [datetime(2024, 1, 1)],
            'Amount': [100.0],
            'Description': ['Test'],
            'CATEGORY': ['Income']
        }
        df = pd.DataFrame(data)
        mock_ledger_service.get_recent_transactions.return_value = df
        
        summary = summary_service.get_executive_summary()
        
        # Should not raise KeyError for 'amount'
        assert summary is not None
    
    def test_amount_column_access(self, summary_service, mock_ledger_service):
        """Test that 'amount' column is accessible after normalization."""
        data = {
            'Date': [datetime(2024, 1, 1), datetime(2024, 1, 2)],
            'Amount': [100.0, -50.0],  # Capital A
            'Description': ['Income', 'Expense']
        }
        df = pd.DataFrame(data)
        mock_ledger_service.get_recent_transactions.return_value = df
        
        summary = summary_service.get_executive_summary()
        
        # Should calculate correctly
        assert summary.monthly_income == 100.0
        assert summary.monthly_spend == -50.0
        assert summary.net_monthly_flow == 50.0
    
    def test_empty_dataframe_handling(self, summary_service, mock_ledger_service):
        """Test handling of empty DataFrame."""
        mock_ledger_service.get_recent_transactions.return_value = pd.DataFrame()
        
        summary = summary_service.get_executive_summary()
        
        # Should not crash, should have zero values
        assert summary.liquid_cash == Decimal('0')
        assert summary.monthly_income == Decimal('0')


class TestIncomeAndExpenseCalculation:
    """Test income and expense calculations."""
    
    def test_income_calculation(self, summary_service, mock_ledger_service):
        """Test monthly income calculation."""
        data = {
            'date': [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)],
            'amount': [1000.0, 2000.0, 500.0],
            'description': ['Salary', 'Bonus', 'Dividend']
        }
        df = pd.DataFrame(data)
        mock_ledger_service.get_recent_transactions.return_value = df
        
        summary = summary_service.get_executive_summary()
        
        assert summary.monthly_income == 3500.0
    
    def test_expense_calculation(self, summary_service, mock_ledger_service):
        """Test monthly expense calculation."""
        data = {
            'date': [datetime(2024, 1, 1), datetime(2024, 1, 2)],
            'amount': [-500.0, -300.0],
            'description': ['Rent', 'Groceries']
        }
        df = pd.DataFrame(data)
        mock_ledger_service.get_recent_transactions.return_value = df
        
        summary = summary_service.get_executive_summary()
        
        assert summary.monthly_spend == -800.0
        assert summary.net_monthly_flow == -800.0
    
    def test_mixed_income_and_expenses(self, summary_service, mock_ledger_service):
        """Test calculation with both income and expenses."""
        data = {
            'date': [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)],
            'amount': [5000.0, -2000.0, -1000.0],
            'description': ['Salary', 'Rent', 'Groceries']
        }
        df = pd.DataFrame(data)
        mock_ledger_service.get_recent_transactions.return_value = df
        
        summary = summary_service.get_executive_summary()
        
        assert summary.monthly_income == 5000.0
        assert summary.monthly_spend == -3000.0
        assert summary.net_monthly_flow == 2000.0


class TestNetWorthCalculation:
    """Test net worth calculation."""
    
    def test_positive_net_worth(self, summary_service, mock_asset_service, mock_liability_service):
        """Test net worth calculation with positive balance."""
        from dataclasses import dataclass
        
        @dataclass
        class MockAsset:
            value: Decimal
        
        mock_asset_service.get_user_assets.return_value = [
            MockAsset(value=Decimal('100000'))
        ]
        mock_liability_service.get_total_liabilities.return_value = Decimal('50000')
        
        summary = summary_service.get_executive_summary()
        
        assert summary.net_worth == Decimal('50000')
    
    def test_negative_net_worth(self, summary_service, mock_asset_service, mock_liability_service):
        """Test net worth calculation with negative balance (more debt than assets)."""
        from dataclasses import dataclass
        
        @dataclass
        class MockAsset:
            value: Decimal
        
        mock_asset_service.get_user_assets.return_value = [
            MockAsset(value=Decimal('30000'))
        ]
        mock_liability_service.get_total_liabilities.return_value = Decimal('50000')
        
        summary = summary_service.get_executive_summary()
        
        assert summary.net_worth == Decimal('-20000')
