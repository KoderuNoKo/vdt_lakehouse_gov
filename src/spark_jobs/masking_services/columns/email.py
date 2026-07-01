from pyspark.sql import functions as F
from pyspark.sql import Column

from masking_services.base import BaseMaskingService

class EmailMaskingService(BaseMaskingService):
    @staticmethod
    def partial_mask(col_name: str, replace_char: str = "*") -> Column:
        """replace all char from the second character until before the @ character"""
        col = F.col(col_name)
        return F.when(col.isNull(), F.lit(None)).otherwise(
            F.concat(
                F.substring_index(col, "@", 1).substr(1, 1),
                F.lit("***@"),
                F.substring_index(col, "@", -1)
            )
        )