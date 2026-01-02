# src/application/rule_service.py

from uuid import UUID
from sqlmodel import Session
from src.core.database import engine
from src.domain.models.MRule import CategoryRule
from src.core.vector_store import VectorRuleEngine
from src.domain.enums import TransactionType


class RuleService:
    def __init__(self):
        self.vector_engine = VectorRuleEngine()

    def add_rule(self, pattern: str, category: str, t_type: TransactionType, owner: UUID):
        # 1. Save to SQL (Source of Truth for User Editing)
        rule = CategoryRule(
            pattern=pattern,
            category=category,
            transaction_type=t_type,
            owner=owner
        )

        with Session(engine) as session:
            session.add(rule)
            session.commit()
            session.refresh(rule)

        # 2. Save to Vector Store (Source of Truth for Searching)
        self.vector_engine.add_rule(
            rule_id=str(rule.id),
            description=pattern,
            metadata={
                "category": category,
                "type": t_type.value,
                "owner_id": str(owner)
            }
        )
        return rule

    def find_category(self, description: str, user_id: UUID):
        # 1. Query Vector Store
        match = self.vector_engine.find_match(description, threshold=0.4)

        if match:
            # Optional: Verify owner match if needed, though local DB is usually single-tenant enough for MVP
            return match['category'], TransactionType(match['type'])

        return "Uncategorized", None