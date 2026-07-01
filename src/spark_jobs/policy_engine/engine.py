from core.enums import PolicyAction

from metadata_store.repository import MetadataRepository

from policy_engine.dtos import TableAccessPlan, ColumnAction

class PolicyEngine:

    def __init__(self, repo: MetadataRepository) -> None:
        self.repo = repo

    def build_access_plan_for_table(
        self,
        namespace: str,
        table_name: str,
        role_name: str,
    ) -> TableAccessPlan:
        policies = self.repo.get_policies_for_role(role_name)
        policy_dict = {p.sensitivity_level_id: p for p in policies}

        columns = self.repo.get_columns_by_table_name(namespace, table_name)

        column_actions = {}
        for col in columns:
            policy = policy_dict.get(col.sensitivity_level_id)
            
            if policy is None:
                action = PolicyAction.ALLOW
                masking_function = None
            else:
                action = policy.action
                masking_function = policy.masking_function
                
            column_actions[col.column_name] = ColumnAction(
                col_name=col.column_name,
                pii_category=col.pii_category, 
                sensitivity=col.sensitivity_level_id, # Can leave as id for mock
                action=action,
                masking_function=masking_function
            )

        return TableAccessPlan(
            table_name=f"{namespace}.{table_name}",
            role=role_name,
            column_actions=column_actions
        )