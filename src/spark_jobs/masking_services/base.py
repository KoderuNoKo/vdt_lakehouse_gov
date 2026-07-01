from pyspark.sql import functions as F
from pyspark.sql import Column

class BaseMaskingService:

    @staticmethod
    def partial_mask(col_name: str, replace_char: str = "*") -> Column:
        """Default partial mask: keep first char, mask the rest."""
        col = F.col(col_name)
        return F.when(col.isNull(), F.lit(None)).otherwise(
            F.concat(
                F.substring(col, 1, 1),
                F.regexp_replace(F.substring(col, 2, F.length(col)), ".", replace_char),
            )
        )

    @staticmethod
    def hash_mask(col_name: str) -> Column:
        """SHA-256 hash of the value using Spark built-in sha2()."""
        return F.sha2(F.col(col_name).cast("string"), 256)

    @staticmethod
    def redact(col_name: str, redacted_str: str = "[REDACTED]") -> Column:
        """Replace value with redacted_str; NULLs remain NULL."""
        col = F.col(col_name)
        return F.when(col.isNull(), F.lit(None)).otherwise(F.lit(redacted_str))

    @staticmethod
    def nullify(col_name: str) -> Column:
        """Replace all values with NULL."""
        return F.lit(None).cast("string")
