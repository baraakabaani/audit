from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class EngagementCreate(BaseModel):
    name: str
    entity_name: Optional[str] = None
    period: Optional[str] = None
    currency: str = "AED"
    overall_materiality: Optional[float] = None
    performance_materiality: Optional[float] = None
    trivial_threshold: Optional[float] = None


class EngagementUpdate(BaseModel):
    entity_name: Optional[str] = None
    period: Optional[str] = None
    currency: Optional[str] = None
    overall_materiality: Optional[float] = None
    performance_materiality: Optional[float] = None
    trivial_threshold: Optional[float] = None
    status: Optional[str] = None


class MappingUpdate(BaseModel):
    fs_category: Optional[str] = None
    fs_line_item: Optional[str] = None
    fs_statement: Optional[str] = None
    lead_line: Optional[str] = None
    user_approved: Optional[int] = None
    user_note: Optional[str] = None


class BulkApprove(BaseModel):
    account_codes: List[str]


class TBAccount(BaseModel):
    account_code: str
    account_name: str
    sub_account: Optional[str]
    account_type_raw: str
    beginning_balance: float
    period_activity: float
    ending_balance: float
    source_row: int
    is_zero: bool
    is_unusual: bool
    unusual_reason: Optional[str]


class AccountMapping(BaseModel):
    account_code: str
    account_name: str
    ending_balance: float
    fs_category: str
    fs_line_item: str
    fs_statement: str
    lead_line: Optional[str]
    confidence: float
    confidence_level: str
    reason: str
    ifrs_reference: Optional[str]
    source: str
    user_approved: bool
    user_modified: bool
    user_note: Optional[str]


class ValidationResult(BaseModel):
    check_name: str
    result: str
    expected: Optional[str]
    actual: Optional[str]
    difference: Optional[str]
    severity: str
    explanation: str


class GenerateRequest(BaseModel):
    engagement_id: int
    generate_audit_file: bool = True
    generate_fs_draft: bool = True
