# tests/unit/test_ledger_service.py
"""
Unit tests for LedgerService
Tests deduplication logic, batch management, and transaction processing.
"""
import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock, patch
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal

import streamlit as st


@pytest.fixture(autouse=True)
def setup_session():
    """Setup streamlit session state before each test."""
    st.session_state = {"user": {"id": str(uuid4())}}
    yield
    st.session_state.clear()


@pytest.fixture
def mock_repository():
    """Create a mock transaction repository."""
    repo = Mock()
    repo.get_all.return_value = []
    repo.get_as_dataframe.return_value = pd.DataFrame()
    repo.save_bulk.return_value = None
    repo.delete_batch.return_value = None
    return repo


@pytest.fixture
def mock_ingestion_service():
    """Create a mock ingestion service."""
    service = Mock()
    service.process_file.return_value = ([], [])
    return service


@pytest.fixture
def ledger_service(mock_repository, mock_ingestion_service):
    """Create a LedgerService instance with mocked dependencies."""
    from src.application.ledger_service import LedgerService
    return LedgerService(mock_repository, mock_ingestion_service)


@pytest.fixture
def sample_transaction():
    """Create a sample transaction."""
    from src.domain.models.MTransaction import Transaction
    return Transaction(
        id=uuid4(),
        date=datetime(2024, 1, 1),
        description="Test Transaction",
        amount=Decimal("100.00"),
        currency="CZK",
        category="Test",
        transaction_type="Income",
        batch_id="batch1",
        owner=UUID(st.session_state["user"]["id"])
    )


class TestDeduplication:
    """Test deduplication logic in service layer."""
    
    def test_duplicate_detection_by_signature(self, ledger_service, mock_repository, sample_transaction):
        """Test that duplicates are detected by (date, amount, description) signature."""
        from src.domain.models.MTransaction import Transaction
        
        # Setup existing transaction
        existing_tx = sample_transaction
        mock_repository.get_all.return_value = [existing_tx]
        
        # Create duplicate with different ID and batch
        duplicate_tx = Transaction(
            id=uuid4(),  # Different ID
            date=existing_tx.date,
            description=existing_tx.description,
            amount=existing_tx.amount,
            currency="CZK",
            category="Test",
            transaction_type="Income",
            batch_id="batch2",  # Different batch
            owner=existing_tx.owner
        )
        
        # Mock file processing to return the duplicate
        mock_file = Mock()
        mock_file.name = "test.csv"
        mock_file.getvalue.return_value = b"test data"
        
        ledger_service.ingestion_svc.process_file.return_value = ([duplicate_tx], [])
        
        # Process upload - duplicate should be filtered out
        count, errors = ledger_service.process_uploads([mock_file])
        
        assert count == 0  # No transactions saved
        assert any("duplicate" in err.lower() for err in errors)
        mock_repository.save_bulk.assert_not_called()
    
    def test_non_duplicate_is_saved(self, ledger_service, mock_repository, sample_transaction):
        """Test that non-duplicate transactions are saved."""
        from src.domain.models.MTransaction import Transaction
        
        # Setup existing transaction
        mock_repository.get_all.return_value = [sample_transaction]
        
        # Create different transaction
        new_tx = Transaction(
            id=uuid4(),
            date=datetime(2024, 1, 2),  # Different date
            description="Different Transaction",
            amount=Decimal("200.00"),
            currency="CZK",
            category="Test",
            transaction_type="Income",
            batch_id="batch2",
            owner=sample_transaction.owner
        )
        
        # Mock file processing
        mock_file = Mock()
        mock_file.name = "test.csv"
        mock_file.getvalue.return_value = b"test data"
        
        ledger_service.ingestion_svc.process_file.return_value = ([new_tx], [])
        
        # Process upload
        count, errors = ledger_service.process_uploads([mock_file])
        
        assert count == 1
        mock_repository.save_bulk.assert_called_once()
        saved_txs = mock_repository.save_bulk.call_args[0][0]
        assert len(saved_txs) == 1
        assert saved_txs[0].description == "Different Transaction"
    
    def test_within_batch_deduplication(self, ledger_service, mock_repository):
        """Test that duplicates within the same upload batch are prevented."""
        from src.domain.models.MTransaction import Transaction
        
        mock_repository.get_all.return_value = []
        
        # Create two identical transactions in same upload
        tx1 = Transaction(
            id=uuid4(),
            date=datetime(2024, 1, 1),
            description="Same Transaction",
            amount=Decimal("100.00"),
            currency="CZK",
            category="Test",
            transaction_type="Income",
            batch_id="batch1",
            owner=UUID(st.session_state["user"]["id"])
        )
        
        tx2 = Transaction(
            id=uuid4(),
            date=datetime(2024, 1, 1),
            description="Same Transaction",
            amount=Decimal("100.00"),
            currency="CZK",
            category="Test",
            transaction_type="Income",
            batch_id="batch1",
            owner=UUID(st.session_state["user"]["id"])
        )
        
        mock_file = Mock()
        mock_file.name = "test.csv"
        mock_file.getvalue.return_value = b"test data"
        
        ledger_service.ingestion_svc.process_file.return_value = ([tx1, tx2], [])
        
        # Process upload
        count, errors = ledger_service.process_uploads([mock_file])
        
        # Only one should be saved
        assert count == 1
        assert any("duplicate" in err.lower() for err in errors)


class TestBatchManagement:
    """Test batch management functionality."""
    
    def test_get_batch_history_empty(self, ledger_service, mock_repository):
        """Test batch history with no data."""
        mock_repository.get_as_dataframe.return_value = pd.DataFrame()
        
        history = ledger_service.get_batch_history()
        
        assert history.empty
    
    def test_get_batch_history_with_data(self, ledger_service, mock_repository):
        """Test batch history aggregation."""
        # Create sample data
        data = {
            'batch_id': ['batch1', 'batch1', 'batch2'],
            'date': [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)],
            'amount': [100, -50, 200]
        }
        df = pd.DataFrame(data)
        mock_repository.get_as_dataframe.return_value = df
        
        history = ledger_service.get_batch_history()
        
        assert not history.empty
        assert 'Batch_ID' in history.columns
        assert 'Tx_Count' in history.columns
        assert len(history) == 2  # Two batches
    
    def test_delete_batch(self, ledger_service, mock_repository):
        """Test batch deletion."""
        batch_id = "batch_to_delete"
        
        ledger_service.delete_batch(batch_id)
        
        mock_repository.delete_batch.assert_called_once()
        call_args = mock_repository.delete_batch.call_args[0]
        assert call_args[0] == batch_id


class TestTransactionProcessing:
    """Test transaction processing and file uploads."""
    
    def test_process_single_file(self, ledger_service, mock_repository, mock_ingestion_service):
        """Test processing a single file."""
        from src.domain.models.MTransaction import Transaction
        
        mock_repository.get_all.return_value = []
        
        tx = Transaction(
            id=uuid4(),
            date=datetime(2024, 1, 1),
            description="Test",
            amount=Decimal("100"),
            currency="CZK",
            category="Test",
            transaction_type="Income",
            batch_id="batch1",
            owner=UUID(st.session_state["user"]["id"])
        )
        
        mock_file = Mock()
        mock_file.name = "test.csv"
        mock_file.getvalue.return_value = b"test data"
        
        mock_ingestion_service.process_file.return_value = ([tx], [])
        
        count, errors = ledger_service.process_uploads([mock_file])
        
        assert count == 1
        assert len(errors) == 0
        mock_repository.save_bulk.assert_called_once()
    
    def test_process_multiple_files(self, ledger_service, mock_repository, mock_ingestion_service):
        """Test processing multiple files."""
        from src.domain.models.MTransaction import Transaction
        
        mock_repository.get_all.return_value = []
        
        # Create transactions for two files
        def process_file_side_effect(name, content, user_id, batch_id):
            tx = Transaction(
                id=uuid4(),
                date=datetime(2024, 1, 1),
                description=f"Tx from {name}",
                amount=Decimal("100"),
                currency="CZK",
                category="Test",
                transaction_type="Income",
                batch_id=batch_id,
                owner=user_id
            )
            return ([tx], [])
        
        mock_ingestion_service.process_file.side_effect = process_file_side_effect
        
        mock_file1 = Mock()
        mock_file1.name = "file1.csv"
        mock_file1.getvalue.return_value = b"data1"
        
        mock_file2 = Mock()
        mock_file2.name = "file2.csv"
        mock_file2.getvalue.return_value = b"data2"
        
        count, errors = ledger_service.process_uploads([mock_file1, mock_file2])
        
        assert count == 2
        assert len(errors) == 0
    
    def test_process_file_with_errors(self, ledger_service, mock_repository, mock_ingestion_service):
        """Test handling of processing errors."""
        mock_repository.get_all.return_value = []
        
        mock_file = Mock()
        mock_file.name = "bad_file.csv"
        mock_file.getvalue.return_value = b"bad data"
        
        # Mock ingestion service returns errors
        mock_ingestion_service.process_file.return_value = ([], ["Parse error line 5"])
        
        count, errors = ledger_service.process_uploads([mock_file])
        
        assert count == 0
        assert len(errors) > 0
        assert "Parse error line 5" in errors


class TestGetRecentTransactions:
    """Test retrieving recent transactions."""
    
    def test_get_recent_transactions(self, ledger_service, mock_repository):
        """Test getting recent transactions as DataFrame."""
        sample_df = pd.DataFrame({
            'date': [datetime(2024, 1, 1)],
            'description': ['Test'],
            'amount': [100.0]
        })
        mock_repository.get_as_dataframe.return_value = sample_df
        
        result = ledger_service.get_recent_transactions()
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        mock_repository.get_as_dataframe.assert_called_once()
