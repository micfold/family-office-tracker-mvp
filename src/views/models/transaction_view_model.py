from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TransactionViewModel:
    """
    Represents a transaction in the ledger view.
    """
    id: str
    date: datetime
    description: str
    amount: float
    category: str
    account: str
    is_internal: bool = False
    is_duplicate: bool = False
    owner: Optional[str] = None
    raw_description: Optional[str] = None
    suggested_category: Optional[str] = None
    confidence: Optional[float] = None
    notes: Optional[str] = None
    tags: list[str] = field(default_factory=list)

