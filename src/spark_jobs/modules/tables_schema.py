"""
define the schema for all the raw data tables in the lakehouse
"""

from pyspark.sql import types as T

SCHEMAS = {
    "citizen_info": T.StructType([
        T.StructField("citizen_id", T.IntegerType(), False),
        T.StructField("full_name", T.StringType(), True),
        T.StructField("national_id", T.StringType(), True),
        T.StructField("phone_number", T.StringType(), True),
        T.StructField("email", T.StringType(), True),
        T.StructField("birth_date", T.DateType(), True),
        T.StructField("address", T.StringType(), True),
        T.StructField("occupation", T.StringType(), True),
    ]),

    "hr_employee": T.StructType([
        T.StructField("employee_id", T.IntegerType(), False),
        T.StructField("department", T.StringType(), True),
        T.StructField("job_title", T.StringType(), True),
        T.StructField("c01", T.StringType(), True),
        T.StructField("c02", T.DoubleType(), True),
        T.StructField("c03", T.StringType(), True),
        T.StructField("c04", T.StringType(), True),
        T.StructField("c05", T.StringType(), True),
        T.StructField("remarks", T.StringType(), True),
    ]),

    "administrative_record": T.StructType([
        T.StructField("record_id", T.IntegerType(), False),
        T.StructField("service_type", T.StringType(), True),
        T.StructField("applicant_name", T.StringType(), True),
        T.StructField("cccd_number", T.StringType(), True),
        T.StructField("submission_date", T.DateType(), True),
        T.StructField("status", T.StringType(), True),
        T.StructField("clerk_notes", T.StringType(), True),
    ]),

    "transaction_log": T.StructType([
        T.StructField("tx_id", T.IntegerType(), False),
        T.StructField("tx_timestamp", T.TimestampType(), True),
        T.StructField("tx_type", T.StringType(), True),
        T.StructField("amount", T.DoubleType(), True),
        T.StructField("source_account", T.StringType(), True),
        T.StructField("target_account", T.StringType(), True),
        T.StructField("tax_id", T.StringType(), True),
        T.StructField("customer_name", T.StringType(), True),
        T.StructField("tx_message", T.StringType(), True),
        T.StructField("fraud_notes", T.StringType(), True),
    ]),
}