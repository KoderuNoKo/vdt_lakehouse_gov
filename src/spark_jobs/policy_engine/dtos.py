from __future__ import annotations

from dataclasses import dataclass

from core.enums import PIICategory, PolicyAction, MaskingFunction, SensitivityLevel


@dataclass
class ColumnAction:
    col_name: str
    pii_category: PIICategory | None
    sensitivity: SensitivityLevel
    action: PolicyAction
    masking_function: MaskingFunction | None


@dataclass
class TableAccessPlan:
    table_name: str
    role: str
    column_actions: dict[str, ColumnAction]

    def get(self, col_name: str) -> ColumnAction | None:
        return self.column_actions.get(col_name)