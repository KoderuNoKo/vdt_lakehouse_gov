from pyspark.sql import functions as F
from pyspark.sql import Column

from masking_services.base import BaseMaskingService

class PhoneMaskingService(BaseMaskingService):
    @staticmethod
    def partial_mask(col_name: str, replace_char: str = "*") -> Column:
        """Keep first 3 digits + last 2 digits, mask middle."""
        col = F.col(col_name)
        return F.when(col.isNull(), F.lit(None)).otherwise(
            F.concat(
                F.expr(f"substring(`{col_name}`, 1, 3)"),
                F.expr(f"repeat('{replace_char}', length(`{col_name}`) - 5)"),
                F.expr(f"right(`{col_name}`, 2)")
            )
        )
