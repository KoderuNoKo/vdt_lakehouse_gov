from __future__ import annotations

from core.enums import PIICategory

from masking_services.base import BaseMaskingService
from masking_services.columns.email import EmailMaskingService
from masking_services.columns.phone import PhoneMaskingService
from masking_services.columns.national_id import NationalIdMaskingService
from masking_services.columns.default import DefaultMaskingService

PII_MASKING_REGISTRY: dict[PIICategory, type[BaseMaskingService]] = {
    PIICategory.EMAIL: EmailMaskingService,
    PIICategory.PHONE: PhoneMaskingService,
    PIICategory.NATIONAL_ID: NationalIdMaskingService,
}

def get_masking_service(pii_category: PIICategory | None) -> type[BaseMaskingService]:
    return PII_MASKING_REGISTRY.get(pii_category, DefaultMaskingService)