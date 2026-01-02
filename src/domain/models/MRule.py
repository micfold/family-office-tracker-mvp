# src/domain/models/MRule.py

from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field
from src.domain.enums import TransactionType


class CategoryRule(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # This is the text we embed (e.g. "Tesco Express")
    pattern: str = Field(index=True)

    # The output we want
    category: str
    transaction_type: TransactionType

    owner: UUID = Field(index=True)