from datetime import datetime
from typing import List, Tuple
from src.models import Policy, Claim, Document, FindingMetadata

def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")

def check_missing_documents(policy: Policy, claim: Claim, provided_docs: List[Document]) -> List[str]:
    required = policy.requirements.get(claim.incident_type, [])
    provided_types = [doc.doc_type for doc in provided_docs]
    
    missing = []
    for req in required:
        if req not in provided_types:
            missing.append(req)
            
    return missing

def run_deterministic_checks(policy: Policy, claim: Claim) -> Tuple[List[FindingMetadata], List[str]]:
    findings = []
    flags = []
    
    # 1. Registration Mismatch
    if policy.vehicle_reg != claim.vehicle_reg:
        flags.append("Vehicle registration mismatch.")
        findings.append(FindingMetadata(
            finding=f"Vehicle registration on claim ({claim.vehicle_reg}) does not match policy ({policy.vehicle_reg}).",
            source_type="Claim Form & Policy",
            source_id=claim.claim_id,
            source_location="Vehicle Reg fields",
            evidence=f"Claim: {claim.vehicle_reg} | Policy: {policy.vehicle_reg}",
            status="CONTRADICTED"
        ))
    
    # 2. Date Validations
    try:
        incident_date = parse_date(claim.incident_date)
        start_date = parse_date(policy.start_date)
        end_date = parse_date(policy.end_date)
        
        if incident_date < start_date or incident_date > end_date:
            flags.append("Incident date outside policy coverage window.")
            findings.append(FindingMetadata(
                finding=f"Incident date {claim.incident_date} is outside the policy active period ({policy.start_date} to {policy.end_date}).",
                source_type="Claim Form & Policy",
                source_id=claim.claim_id,
                source_location="Date fields",
                evidence=f"Incident: {claim.incident_date} | Policy: {policy.start_date} - {policy.end_date}",
                status="CONTRADICTED"
            ))
    except ValueError:
        flags.append("Invalid date format.")
        
    # 3. Claim Amount Mismatch / Exceeds value
    if claim.claim_amount > policy.insured_value:
        flags.append("Claim amount exceeds insured value.")
        findings.append(FindingMetadata(
            finding=f"Claim amount ({claim.claim_amount}) exceeds the maximum insured value ({policy.insured_value}).",
            source_type="Claim Form & Policy",
            source_id=claim.claim_id,
            source_location="Amount fields",
            evidence=f"Claim Amount: {claim.claim_amount} | Insured Value: {policy.insured_value}",
            status="CONTRADICTED"
        ))
        
    # 4. Policy number mismatch (Not strictly necessary if they load via ID, but good to have)
    if claim.policy_id != policy.policy_id:
        flags.append("Policy ID mismatch.")
        
    return findings, flags
