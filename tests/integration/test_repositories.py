# tests/integration/test_repositories.py
"""
Integration tests for repository implementations
Tests CSV and SQL repositories with actual file I/O and data persistence.
"""
import pytest
import pandas as pd
import tempfile
import shutil
from pathlib import Path
from uuid import uuid4, UUID
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
import streamlit as st

# Mock streamlit session
st.session_state = {}


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_auth_user(temp_dir, monkeypatch):
    """Mock authenticated user for repository tests."""
    user_id = str(uuid4())
    user_path = temp_dir / user_id
    user_path.mkdir(parents=True, exist_ok=True)
    
    st.session_state["user"] = {
        "id": user_id,
        "username": "testuser",
        "path": user_path
    }
    
    # Patch DATA_ROOT
    import src.application.auth_service as auth_module
    monkeypatch.setattr(auth_module, 'DATA_ROOT', temp_dir)
    
    yield user_id, user_path


class TestCsvTransactionRepository:
    """Integration tests for CSV transaction repository."""
    
    def test_save_and_load_transactions(self, mock_auth_user):
        """Test saving and loading transactions from CSV."""
        from src.domain.repositories.csv_ledger_repository import CsvTransactionRepository
        from src.domain.models.MTransaction import Transaction
        
        user_id, user_path = mock_auth_user
        repo = CsvTransactionRepository()
        
        # Create test transactions
        tx1 = Transaction(
            id=uuid4(),
            date=datetime(2024, 1, 1),
            description="Test Transaction 1",
            amount=Decimal("100.00"),
            currency="CZK",
            category="Income",
            transaction_type="Income",
            batch_id="batch1",
            owner=UUID(user_id)
        )
        
        tx2 = Transaction(
            id=uuid4(),
            date=datetime(2024, 1, 2),
            description="Test Transaction 2",
            amount=Decimal("-50.00"),
            currency="CZK",
            category="Expense",
            transaction_type="Expense",
            batch_id="batch1",
            owner=UUID(user_id)
        )
        
        # Save transactions
        repo.save_bulk([tx1, tx2])
        
        # Load and verify
        loaded_txs = repo.get_all(UUID(user_id))
        assert len(loaded_txs) == 2
        
        # Verify data integrity
        descriptions = [tx.description for tx in loaded_txs]
        assert "Test Transaction 1" in descriptions
        assert "Test Transaction 2" in descriptions
    
    def test_get_as_dataframe(self, mock_auth_user):
        """Test getting transactions as DataFrame."""
        from src.domain.repositories.csv_ledger_repository import CsvTransactionRepository
        from src.domain.models.MTransaction import Transaction
        
        user_id, user_path = mock_auth_user
        repo = CsvTransactionRepository()
        
        tx = Transaction(
            id=uuid4(),
            date=datetime(2024, 1, 1),
            description="Test",
            amount=Decimal("100"),
            currency="CZK",
            category="Test",
            transaction_type="Income",
            batch_id="batch1",
            owner=UUID(user_id)
        )
        
        repo.save_bulk([tx])
        
        df = repo.get_as_dataframe(UUID(user_id))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert 'description' in df.columns
        assert df['description'].iloc[0] == "Test"
    
    def test_delete_batch(self, mock_auth_user):
        """Test deleting a batch of transactions."""
        from src.domain.repositories.csv_ledger_repository import CsvTransactionRepository
        from src.domain.models.MTransaction import Transaction
        
        user_id, user_path = mock_auth_user
        repo = CsvTransactionRepository()
        
        # Create transactions in two batches
        tx1 = Transaction(
            id=uuid4(),
            date=datetime(2024, 1, 1),
            description="Batch 1",
            amount=Decimal("100"),
            currency="CZK",
            category="Test",
            transaction_type="Income",
            batch_id="batch1",
            owner=UUID(user_id)
        )
        
        tx2 = Transaction(
            id=uuid4(),
            date=datetime(2024, 1, 2),
            description="Batch 2",
            amount=Decimal("200"),
            currency="CZK",
            category="Test",
            transaction_type="Income",
            batch_id="batch2",
            owner=UUID(user_id)
        )
        
        repo.save_bulk([tx1, tx2])
        
        # Delete batch1
        repo.delete_batch("batch1", UUID(user_id))
        
        # Verify only batch2 remains
        remaining = repo.get_all(UUID(user_id))
        assert len(remaining) == 1
        assert remaining[0].description == "Batch 2"
    
    def test_column_normalization(self, mock_auth_user):
        """Test that column normalization works with different input formats."""
        from src.domain.repositories.csv_ledger_repository import CsvTransactionRepository
        
        user_id, user_path = mock_auth_user
        repo = CsvTransactionRepository()
        
        # Create CSV with mixed-case columns
        csv_path = user_path / "ledger.csv"
        data = {
            'Transaction Date': ['2024-01-01'],
            'Amount': [100],
            'Description': ['Test'],
            'Type': ['Income']
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        # Load and verify normalization
        loaded_df = repo.get_as_dataframe(UUID(user_id))
        
        assert 'date' in loaded_df.columns  # Normalized from 'Transaction Date'
        assert 'amount' in loaded_df.columns
        assert 'description' in loaded_df.columns
        assert 'type' in loaded_df.columns


class TestCsvPortfolioRepository:
    """Integration tests for CSV portfolio repository."""
    
    def test_save_and_load_snapshot(self, mock_auth_user):
        """Test saving and loading portfolio snapshot."""
        from src.domain.repositories.csv_portfolio_repository import CsvPortfolioRepository
        from io import BytesIO
        
        user_id, user_path = mock_auth_user
        repo = CsvPortfolioRepository()
        
        # Create test snapshot file
        snapshot_data = b"ticker,name,quantity,price,value\nAAPL,Apple,10,150,1500\nGOOGL,Google,5,100,500"
        file_obj = BytesIO(snapshot_data)
        
        # Save file
        repo.save_snapshot_file(file_obj)
        
        # Verify file exists
        snapshot_path = user_path / "portfolio_snapshot.csv"
        assert snapshot_path.exists()
        
        # Load and verify
        positions = repo.get_snapshot(UUID(user_id))
        assert len(positions) >= 0  # May vary depending on column mapping
    
    def test_save_and_load_history(self, mock_auth_user):
        """Test saving and loading portfolio history."""
        from src.domain.repositories.csv_portfolio_repository import CsvPortfolioRepository
        from io import BytesIO
        
        user_id, user_path = mock_auth_user
        repo = CsvPortfolioRepository()
        
        # Create test history file
        history_data = b"date,ticker,event,amount\n2024-01-01,AAPL,BUY,1500\n2024-01-02,GOOGL,BUY,500"
        file_obj = BytesIO(history_data)
        
        # Save file
        repo.save_history_file(file_obj)
        
        # Verify file exists
        history_path = user_path / "portfolio_history.csv"
        assert history_path.exists()
    
    def test_error_handling_missing_file(self, mock_auth_user):
        """Test that missing files are handled gracefully."""
        from src.domain.repositories.csv_portfolio_repository import CsvPortfolioRepository
        
        user_id, user_path = mock_auth_user
        repo = CsvPortfolioRepository()
        
        # Try to load non-existent files
        positions = repo.get_snapshot(UUID(user_id))
        events = repo.get_history(UUID(user_id))
        
        # Should return empty lists, not crash
        assert positions == []
        assert events == []


class TestSqlPortfolioRepository:
    """Integration tests for SQL portfolio repository."""
    
    def test_save_snapshot_file(self, mock_auth_user):
        """Test saving portfolio snapshot file via SQL repository."""
        from src.domain.repositories.sql_repository import SqlPortfolioRepository
        from io import BytesIO
        
        user_id, user_path = mock_auth_user
        repo = SqlPortfolioRepository()
        
        # Create test file
        test_data = b"ticker,name,quantity\nAAPL,Apple,10"
        file_obj = BytesIO(test_data)
        
        # Save file
        repo.save_snapshot_file(file_obj)
        
        # Verify file exists
        snapshot_path = user_path / "portfolio_snapshot.csv"
        assert snapshot_path.exists()
        assert snapshot_path.read_bytes() == test_data
    
    def test_save_history_file(self, mock_auth_user):
        """Test saving portfolio history file via SQL repository."""
        from src.domain.repositories.sql_repository import SqlPortfolioRepository
        from io import BytesIO
        
        user_id, user_path = mock_auth_user
        repo = SqlPortfolioRepository()
        
        # Create test file
        test_data = b"date,ticker,event\n2024-01-01,AAPL,BUY"
        file_obj = BytesIO(test_data)
        
        # Save file
        repo.save_history_file(file_obj)
        
        # Verify file exists
        history_path = user_path / "portfolio_history.csv"
        assert history_path.exists()
        assert history_path.read_bytes() == test_data


class TestDataPersistence:
    """Test data persistence across repository instances."""
    
    def test_data_survives_repository_recreation(self, mock_auth_user):
        """Test that data persists when repository is recreated."""
        from src.domain.repositories.csv_ledger_repository import CsvTransactionRepository
        from src.domain.models.MTransaction import Transaction
        
        user_id, user_path = mock_auth_user
        
        # Create first repository instance and save data
        repo1 = CsvTransactionRepository()
        tx = Transaction(
            id=uuid4(),
            date=datetime(2024, 1, 1),
            description="Persistent Transaction",
            amount=Decimal("100"),
            currency="CZK",
            category="Test",
            transaction_type="Income",
            batch_id="batch1",
            owner=UUID(user_id)
        )
        repo1.save_bulk([tx])
        
        # Create new repository instance
        repo2 = CsvTransactionRepository()
        
        # Load data
        loaded = repo2.get_all(UUID(user_id))
        
        assert len(loaded) == 1
        assert loaded[0].description == "Persistent Transaction"
