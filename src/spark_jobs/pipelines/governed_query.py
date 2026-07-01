"""Provide an interface for client to query for tables.
In the current scope, for simplicity, provide only one single method
"""

from __future__ import annotations

from pyspark.sql import SparkSession, DataFrame

from core.config import load_config
from core.enums import PolicyAction, MaskingFunction

from masking_services import get_masking_service

from metadata_store.repository import MetadataRepository

from policy_engine import PolicyEngine

def get_table(
    spark: SparkSession,
    repo: MetadataRepository,
    namespace: str,
    table_name: str,
    role: str,
    columns: list[str] | None = None,
) -> DataFrame:
    """allows querying one whole table at a time. This method will:
    1. Retrieve metadata from metadata_store,
    2. Query Policy Engine for TableAccessPlan 
    3. Query into database for data
    4. Govern the result, for each column
    """
    engine = PolicyEngine(repo)
    plan = engine.build_access_plan_for_table(namespace, table_name, role)
    
    cfg = load_config()
    full_table_name = f"{cfg.catalog_name}.{namespace}.{table_name}"
    df = spark.table(full_table_name)
    
    # check if client is querying columns they cant access
    if columns is not None:
        for col_name in columns:
            col_action = plan.get(col_name)
            if col_action is None or col_action.action == PolicyAction.DENY:
                raise ValueError(f"Column '{col_name}' does not exist or access is denied")

    for col_name in df.columns:
        col_action = plan.get(col_name)
        if col_action is not None:
            if col_action.action == PolicyAction.ALLOW:
                pass
            elif col_action.action == PolicyAction.MASK:
                service_cls = get_masking_service(col_action.pii_category)
                if col_action.masking_function == MaskingFunction.PARTIAL_MASK:
                    masked_col = service_cls.partial_mask(col_name)
                elif col_action.masking_function == MaskingFunction.HASH_MASK:
                    masked_col = service_cls.hash_mask(col_name)
                elif col_action.masking_function == MaskingFunction.REDACT:
                    masked_col = service_cls.redact(col_name)
                elif col_action.masking_function == MaskingFunction.NULLIFY:
                    masked_col = service_cls.nullify(col_name)
                else:
                    masked_col = service_cls.nullify(col_name)
                df = df.withColumn(col_name, masked_col)
            elif col_action.action == PolicyAction.DENY:
                df = df.drop(col_name)
        else:
            pass
            
    if columns is not None:
        df = df.select(columns)

    return df