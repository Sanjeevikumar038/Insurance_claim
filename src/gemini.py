import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
from src.models import FindingMetadata

class GeminiAnalysisResult(BaseModel):
    analysis_summary: str = ""
    findings: List[FindingMetadata]

def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    return genai.Client(api_key=api_key)

def analyze_claim_evidence(incident_description: str, retrieved_clauses: str, claim_documents: str) -> GeminiAnalysisResult:
    """
    Calls Gemini to analyze the claim evidence against retrieved policy clauses.
    Returns a structured list of findings.
    """
    client = get_gemini_client()
    
    prompt = f"""
    You are an expert insurance claim investigator. Analyze the following claim evidence against the provided policy clauses.
    Your task is to identify key factual findings, contradictions between documents, and map incident facts to policy clauses.
    
    IMPORTANT RULES:
    1. Base all findings ONLY on the provided evidence and policy clauses. Do not invent information.
    2. If there is a contradiction between documents (e.g. FIR vs Customer Description), explicitly output a finding with status 'CONTRADICTED', citing both sources.
    3. Every finding must strictly include the exact text snippet as 'evidence'.
    4. If the evidence is insufficient to determine a fact, output status 'UNKNOWN'.
    5. Do not make the final approve/reject decision. Only output the findings.
    
    OUTPUT FORMAT:
    Your output must be a valid JSON object matching this exact structure:
    {{
      "analysis_summary": "string",
      "findings": [
        {{
          "finding": "string",
          "source_type": "string",
          "source_id": "string",
          "source_location": "string",
          "evidence": "string",
          "policy_clause": "string or null",
          "status": "SUPPORTED | CONTRADICTED | UNKNOWN"
        }}
      ]
    }}
    
    POLICY CLAUSES:
    {retrieved_clauses}
    
    CLAIM DOCUMENTS:
    {claim_documents}
    
    INCIDENT DESCRIPTION:
    {incident_description}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0
            )
        )
        
        # Parse the structured JSON response
        try:
            result_dict = json.loads(response.text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Gemini JSON: {e}\nRaw output: {response.text}")
            
        return GeminiAnalysisResult(**result_dict)
        
    except Exception as e:
        raise RuntimeError(f"Gemini API Error: {str(e)}")

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generates embeddings for a list of texts using gemini-embedding-001.
    """
    client = get_gemini_client()
    try:
        response = client.models.embed_content(
            model='gemini-embedding-001',
            contents=texts
        )
        return [emb.values for emb in response.embeddings]
    except Exception as e:
        raise RuntimeError(f"Gemini Embedding API Error: {str(e)}")
