from datetime import datetime
from typing import List, Tuple
from src.models import Policy, Claim, Document, FindingMetadata

def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")

def check_missing_documents(policy: Policy, claim: Claim, provided_docs: List[Document]) -> Tuple[List[str], List[FindingMetadata]]:
    required = policy.requirements.get(claim.incident_type, [])
    provided_types = [doc.doc_type for doc in provided_docs]
    
    missing = []
    findings = []
    for req in required:
        if req not in provided_types:
            missing.append(req)
            findings.append(FindingMetadata(
                finding=f"Required document '{req}' is missing.",
                source_type="system",
                source_id="requirements",
                source_location="N/A",
                evidence=f"Missing: {req}",
                status="UNKNOWN"
            ))
            
    return missing, findings

def run_deterministic_checks(policy: Policy, claim: Claim) -> Tuple[List[FindingMetadata], List[str]]:
    findings = []
    flags = []
    
    # 1. Registration Mismatch
    if policy.vehicle_reg != claim.vehicle_reg:
        flags.append("Vehicle registration mismatch.")
        findings.append(FindingMetadata(
            finding=f"Vehicle registration on claim ({claim.vehicle_reg}) does not match policy ({policy.vehicle_reg}).",
            source_type="structured_data",
            source_id=claim.claim_id,
            source_location="Vehicle Reg",
            evidence=f"Claim: {claim.vehicle_reg} | Policy: {policy.vehicle_reg}",
            status="CONTRADICTED"
        ))
    else:
        findings.append(FindingMetadata(
            finding=f"Vehicle registration {claim.vehicle_reg} matches policy.",
            source_type="structured_data",
            source_id=claim.claim_id,
            source_location="Vehicle Reg",
            evidence=f"Claim: {claim.vehicle_reg} | Policy: {policy.vehicle_reg}",
            status="SUPPORTED"
        ))
    
    # 2. Policy ID Mismatch
    if claim.policy_id != policy.policy_id:
        flags.append("Policy ID mismatch.")
        findings.append(FindingMetadata(
            finding=f"Claim specifies Policy ID {claim.policy_id} but retrieved {policy.policy_id}.",
            source_type="structured_data",
            source_id=claim.claim_id,
            source_location="Policy ID",
            evidence=f"Claim: {claim.policy_id} | Policy: {policy.policy_id}",
            status="CONTRADICTED"
        ))
        
    # 3. Date Validations (Policy Coverage and 30-Day Window)
    try:
        incident_date = parse_date(claim.incident_date)
        start_date = parse_date(policy.start_date)
        end_date = parse_date(policy.end_date)
        
        if incident_date < start_date or incident_date > end_date:
            flags.append("Incident date outside policy coverage window.")
            findings.append(FindingMetadata(
                finding=f"Incident date {claim.incident_date} is outside the policy active period ({policy.start_date} to {policy.end_date}).",
                source_type="structured_data",
                source_id=claim.claim_id,
                source_location="Incident Date",
                evidence=f"Incident: {claim.incident_date} | Policy: {policy.start_date} - {policy.end_date}",
                status="CONTRADICTED"
            ))
        else:
            findings.append(FindingMetadata(
                finding=f"Incident date {claim.incident_date} is within policy coverage ({policy.start_date} to {policy.end_date}).",
                source_type="structured_data",
                source_id=claim.claim_id,
                source_location="Incident Date",
                evidence=f"Incident: {claim.incident_date} | Policy: {policy.start_date} - {policy.end_date}",
                status="SUPPORTED"
            ))
            
        # 30-day reporting window check
        if claim.claim_date:
            claim_date = parse_date(claim.claim_date)
            delta_days = (claim_date - incident_date).days
            if delta_days <= 30:
                findings.append(FindingMetadata(
                    finding=f"Claim reported {delta_days} days after incident (within 30-day window).",
                    source_type="structured_data",
                    source_id=claim.claim_id,
                    source_location="Claim Date",
                    evidence=f"Incident: {claim.incident_date} | Claim: {claim.claim_date}",
                    status="SUPPORTED"
                ))
            else:
                flags.append("Claim reported outside 30-day window.")
                findings.append(FindingMetadata(
                    finding=f"Claim reported {delta_days} days after incident, exceeding the 30-day window.",
                    source_type="structured_data",
                    source_id=claim.claim_id,
                    source_location="Claim Date",
                    evidence=f"Incident: {claim.incident_date} | Claim: {claim.claim_date}",
                    status="CONTRADICTED"
                ))
        else:
            findings.append(FindingMetadata(
                finding="Claim report date is missing from structured data, cannot verify 30-day window.",
                source_type="structured_data",
                source_id=claim.claim_id,
                source_location="Claim Date",
                evidence="N/A",
                status="UNKNOWN"
            ))
    except ValueError:
        flags.append("Invalid or missing date format.")
        
    # 4. Claim Amount
    if claim.claim_amount > policy.insured_value:
        flags.append("Claim amount exceeds insured value.")
        findings.append(FindingMetadata(
            finding=f"Claim amount ({claim.claim_amount}) exceeds the maximum insured value ({policy.insured_value}).",
            source_type="structured_data",
            source_id=claim.claim_id,
            source_location="Amount fields",
            evidence=f"Claim Amount: {claim.claim_amount} | Insured Value: {policy.insured_value}",
            status="CONTRADICTED"
        ))
    else:
        findings.append(FindingMetadata(
            finding=f"Claim amount ({claim.claim_amount}) is within the maximum insured value ({policy.insured_value}).",
            source_type="structured_data",
            source_id=claim.claim_id,
            source_location="Amount fields",
            evidence=f"Claim Amount: {claim.claim_amount} | Insured Value: {policy.insured_value}",
            status="SUPPORTED"
        ))
        
    return findings, flags
