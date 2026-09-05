from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

class Clause(BaseModel):
    id: str
    title: str
    text: str

class Policy(BaseModel):
    policy_id: str
    insured_name: str
    vehicle_reg: str
    start_date: str
    end_date: str
    insured_value: float
    clauses: List[Clause]
    exclusions: List[Clause]
    requirements: Dict[str, List[str]]

class Claim(BaseModel):
    claim_id: str
    policy_id: str
    incident_date: str
    claim_date: Optional[str] = None
    claim_amount: float
    incident_type: str
    vehicle_reg: str

class Document(BaseModel):
    claim_id: str
    doc_type: str
    content: str

class FindingMetadata(BaseModel):
    finding: str
    source_type: str
    source_id: str
    source_location: str
    evidence: str
    policy_clause: Optional[str] = None
    status: Literal["SUPPORTED", "CONTRADICTED", "UNKNOWN"]

class ReviewResult(BaseModel):
    missing_documents: List[str] = []
    flags: List[str] = []
    findings: List[FindingMetadata] = []
    recommendation: Literal["APPROVE", "REJECT", "REQUEST INFORMATION", "ESCALATE", "ERROR"]
    justification: str
