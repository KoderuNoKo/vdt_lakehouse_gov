"""Custom masking services for specific pii categories"""
from masking_services.columns.email import EmailMaskingService
from masking_services.columns.phone import PhoneMaskingService
from masking_services.columns.national_id import NationalIdMaskingService
from masking_services.columns.default import DefaultMaskingService