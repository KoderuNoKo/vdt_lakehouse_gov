from core.config import load_config
from core.connection import create_engine_from_config, create_session
from core.enums import RoleName
from core.spark_session import build_spark_session

from metadata_store.repository import MetadataRepository

from pipelines.governed_query import get_table

def main():
    print("=" * 60)
    print("Testing Governed Query Pipeline (Integration Test)")
    print("=" * 60)

    # 1. Load config and build Spark session
    cfg = load_config()
    spark = build_spark_session("test_governed_query", cfg)
    spark.sparkContext.setLogLevel("WARN")

    # 2. Connect to the real Metadata Store
    engine = create_engine_from_config(cfg)
    session = create_session(engine)
    repo = MetadataRepository(session)

    namespace = cfg.namespace
    table_name = "citizen_info"

    print(f"[INFO] Using catalog: {cfg.catalog_name}, namespace: {namespace}, table: {table_name}")

    roles_to_test = [RoleName.ADMIN.value, RoleName.ANALYST.value, RoleName.AUDITOR.value]

    for role in roles_to_test:
        print("\n" + "=" * 40)
        print(f"--- Testing Role: {role} ---")
        print("=" * 40)
        try:
            df = get_table(spark, repo, namespace, table_name, role)
            print("\nSchema:")
            df.printSchema()
            print(f"\nData for {role} (first 5 rows):")
            df.show(5, truncate=False)
        except Exception as e:
            print(f"Error querying for role {role}: {e}")
            
    print("\n" + "=" * 40)
    print("--- Testing Explicit Columns (ANALYST) ---")
    print("=" * 40)
    try:
        # Requesting specific columns
        df = get_table(spark, repo, namespace, table_name, "ANALYST", columns=["email", "phone", "address"])
        print("\nSchema:")
        df.printSchema()
        print("\nData (first 5 rows):")
        df.show(5, truncate=False)
    except Exception as e:
        print(f"Error with explicit columns: {e}")

    print("\n" + "=" * 60)
    print("Test Completed")
    print("=" * 60)

    spark.stop()

if __name__ == "__main__":
    main()
