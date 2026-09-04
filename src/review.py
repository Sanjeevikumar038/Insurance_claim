import json
import os
from typing import List
from src.models import Policy, Claim, Document, ReviewResult, FindingMetadata
from src.rules import check_missing_documents, run_deterministic_checks
from src.retrieval import PolicyRetriever
from src.gemini import analyze_claim_evidence

def load_policy(policy_id: str) -> Policy:
    path = f"data/policy/{policy_id}.json"
    with open(path, "r") as f:
        data = json.load(f)
        return Policy(**data)

def load_claim(claim_id: str) -> Claim:
    with open("data/claims/claims.json", "r") as f:
        claims = json.load(f)
        for c in claims:
            if c["claim_id"] == claim_id:
                return Claim(**c)
    raise ValueError(f"Claim {claim_id} not found.")

def load_documents(claim_id: str) -> List[Document]:
    docs = []
    doc_dir = "data/documents"
    if not os.path.exists(doc_dir):
        return docs
        
    for filename in os.listdir(doc_dir):
        if filename.startswith(f"{claim_id}_"):
            doc_type = filename.replace(f"{claim_id}_", "").replace(".txt", "")
            with open(os.path.join(doc_dir, filename), "r") as f:
                content = f.read()
            docs.append(Document(claim_id=claim_id, doc_type=doc_type, content=content))
    return docs

def determine_recommendation(
    missing_docs: List[str], 
    flags: List[str], 
    findings: List[FindingMetadata]
) -> tuple[str, str]:
    """
    Applies the deterministic decision hierarchy.
    """
    
    # 2. Material Contradiction -> ESCALATE
    if flags:
        return "ESCALATE", "Material contradiction detected by deterministic rules: " + "; ".join(flags)
        
    for finding in findings:
        if finding.status == "CONTRADICTED":
            # Check if this contradiction maps to an exclusion
            if finding.policy_clause and "Exclusion" in finding.finding: # Just a heuristic, but let's be safer
                pass
            return "ESCALATE", f"Material contradiction detected by AI: {finding.finding}"
            
    # 3. Clearly Established Exclusion -> REJECT
    # If the policy clause mapped is an exclusion and it's SUPPORTED by evidence
    for finding in findings:
        if finding.status == "SUPPORTED" and finding.policy_clause and ("exclusion" in finding.policy_clause.lower() or finding.policy_clause.startswith("E")):
            return "REJECT", f"Claim blocked by exclusion: {finding.finding}"
            
    # 4. Missing Required Information/Documents -> REQUEST INFORMATION
    if missing_docs:
        return "REQUEST INFORMATION", "Missing required documents: " + ", ".join(missing_docs)
        
    # 5. Insufficient/Unknown Evidence -> REQUEST INFORMATION or ESCALATE
    for finding in findings:
        if finding.status == "UNKNOWN":
            return "REQUEST INFORMATION", f"Insufficient evidence regarding: {finding.finding}"
            
    # 6. Sufficient Evidence + No Blockers -> APPROVE
    return "APPROVE", "All evidence is consistent and supports the claim."


def review_claim(claim_id: str) -> ReviewResult:
    try:
        # Load Data
        claim = load_claim(claim_id)
        policy = load_policy(claim.policy_id)
        documents = load_documents(claim_id)
        
        # 1. Deterministic Checks
        missing_docs = check_missing_documents(policy, claim, documents)
        det_findings, det_flags = run_deterministic_checks(policy, claim)
        
        # If there are already missing docs or flags, we should still run Gemini to get the full picture,
        # but the decision will be handled by the hierarchy.
        
        # 2. Retrieval
        retriever = PolicyRetriever(policy)
        query = f"Incident type: {claim.incident_type}. Description: {claim.incident_description if hasattr(claim, 'incident_description') else 'N/A'}"
        
        # We construct a query string based on the docs available
        doc_texts = []
        for d in documents:
            doc_texts.append(f"--- Document Type: {d.doc_type} ---\n{d.content}\n")
            if d.doc_type == "customer_description":
                query += " " + d.content
                
        retrieved_clauses = retriever.retrieve(query)
        claim_docs_str = "\n".join(doc_texts)
        
        # 3. Gemini Reasoning
        try:
            gemini_result = analyze_claim_evidence(
                incident_description=query,
                retrieved_clauses=retrieved_clauses,
                claim_documents=claim_docs_str
            )
            all_findings = det_findings + gemini_result.findings
        except Exception as e:
            # API Failure / Timeout / Malformed Output -> ERROR
            return ReviewResult(
                missing_documents=missing_docs,
                flags=det_flags,
                findings=det_findings,
                recommendation="ERROR",
                justification=f"Technical Error during LLM analysis: {str(e)}"
            )
            
        # 4. Decision Hierarchy
        recommendation, justification = determine_recommendation(missing_docs, det_flags, all_findings)
        
        return ReviewResult(
            missing_documents=missing_docs,
            flags=det_flags,
            findings=all_findings,
            recommendation=recommendation, # type: ignore
            justification=justification
        )
        
    except Exception as e:
        return ReviewResult(
            missing_documents=[],
            flags=[],
            findings=[],
            recommendation="ERROR",
            justification=f"System Error: {str(e)}"
        )
