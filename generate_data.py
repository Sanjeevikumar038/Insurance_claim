import json
import os

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

ensure_dir("data/policy")
ensure_dir("data/claims")
ensure_dir("data/documents")

# 1. Generate Policy
policy = {
    "policy_id": "POL-2026",
    "insured_name": "Sanjeev Kumar",
    "vehicle_reg": "KA-01-AB-1234",
    "start_date": "2026-01-01",
    "end_date": "2026-12-31",
    "insured_value": 500000,
    "clauses": [
        {"id": "C1", "title": "Accidental Damage", "text": "The Company will indemnify the insured against loss or damage to the vehicle by accidental external means."},
        {"id": "C2", "title": "Theft", "text": "The Company will indemnify the insured against loss of the vehicle due to burglary, housebreaking, or theft."},
        {"id": "C3", "title": "Claim Window", "text": "All claims must be reported within 30 days of the incident date."}
    ],
    "exclusions": [
        {"id": "E1", "title": "Drunk Driving", "text": "The Company shall not be liable for any accidental loss or damage suffered whilst the insured or any person driving with the knowledge and consent of the insured is under the influence of intoxicating liquor or drugs."},
        {"id": "E2", "title": "Keys Left in Vehicle", "text": "The Company shall not be liable for theft of the vehicle if the keys were left in or on the unattended vehicle."},
        {"id": "E3", "title": "Unlicensed Driver", "text": "The Company shall not be liable if the vehicle is being driven by a person who does not hold a valid driving license."}
    ],
    "requirements": {
        "accidental_damage": ["claim_form", "repair_estimate", "customer_description"],
        "theft": ["claim_form", "fir", "customer_description"]
    }
}

with open("data/policy/POL-2026.json", "w") as f:
    json.dump(policy, f, indent=4)

# 2. Generate Claims & Documents

claims = []

# Helper to write doc
def write_doc(claim_id, doc_type, content):
    path = f"data/documents/{claim_id}_{doc_type}.txt"
    with open(path, "w") as f:
        f.write(content)

# CASE 1: Normal (Accidental Damage)
c1_id = "CLM-001"
claims.append({
    "claim_id": c1_id,
    "policy_id": "POL-2026",
    "incident_date": "2026-05-10",
    "claim_amount": 45000,
    "incident_type": "accidental_damage",
    "vehicle_reg": "KA-01-AB-1234"
})
write_doc(c1_id, "claim_form", "Claim ID: CLM-001\nVehicle: KA-01-AB-1234\nType: Accidental Damage\nAmount: 45000 INR\nDate: 2026-05-10")
write_doc(c1_id, "repair_estimate", "Repair Estimate from AutoFix Garage.\nReplace front bumper: 20000 INR\nReplace left headlight: 15000 INR\nLabor: 10000 INR\nTotal: 45000 INR")
write_doc(c1_id, "customer_description", "I was driving to work when I accidentally rear-ended the car in front of me at a stoplight. My front bumper and left headlight were damaged.")

# CASE 2: Contradictory (Keys left in vehicle)
c2_id = "CLM-002"
claims.append({
    "claim_id": c2_id,
    "policy_id": "POL-2026",
    "incident_date": "2026-06-15",
    "claim_amount": 500000,
    "incident_type": "theft",
    "vehicle_reg": "KA-01-AB-1234"
})
write_doc(c2_id, "claim_form", "Claim ID: CLM-002\nVehicle: KA-01-AB-1234\nType: Theft\nAmount: 500000 INR\nDate: 2026-06-15")
write_doc(c2_id, "fir", "First Information Report (FIR).\nVehicle KA-01-AB-1234 reported stolen from XYZ Mall parking lot. The complainant stated they had stepped out for 5 minutes to buy water and left the keys in the ignition.")
write_doc(c2_id, "customer_description", "I parked my car at the mall and locked it securely. When I returned, it was gone.")

# CASE 3: Missing Document (Theft without FIR)
c3_id = "CLM-003"
claims.append({
    "claim_id": c3_id,
    "policy_id": "POL-2026",
    "incident_date": "2026-07-20",
    "claim_amount": 500000,
    "incident_type": "theft",
    "vehicle_reg": "KA-01-AB-1234"
})
write_doc(c3_id, "claim_form", "Claim ID: CLM-003\nVehicle: KA-01-AB-1234\nType: Theft\nAmount: 500000 INR\nDate: 2026-07-20")
write_doc(c3_id, "customer_description", "My car was stolen overnight from my driveway.")
# Missing FIR intentionally

# CASE 4: Exclusion (Drunk Driving)
c4_id = "CLM-004"
claims.append({
    "claim_id": c4_id,
    "policy_id": "POL-2026",
    "incident_date": "2026-08-05",
    "claim_amount": 150000,
    "incident_type": "accidental_damage",
    "vehicle_reg": "KA-01-AB-1234"
})
write_doc(c4_id, "claim_form", "Claim ID: CLM-004\nVehicle: KA-01-AB-1234\nType: Accidental Damage\nAmount: 150000 INR\nDate: 2026-08-05")
write_doc(c4_id, "repair_estimate", "Extensive damage to side doors and chassis. Total: 150000 INR.")
write_doc(c4_id, "fir", "FIR filed for accident. Driver collided with a street lamp. Breathalyzer test confirmed driver was intoxicated (BAC 0.15%).")
write_doc(c4_id, "customer_description", "I lost control of the car and hit a street lamp. I was perfectly sober, just tired.")

# CASE 5: Insufficient Evidence (Vague Estimate)
c5_id = "CLM-005"
claims.append({
    "claim_id": c5_id,
    "policy_id": "POL-2026",
    "incident_date": "2026-09-01",
    "claim_amount": 80000,
    "incident_type": "accidental_damage",
    "vehicle_reg": "KA-01-AB-1234"
})
write_doc(c5_id, "claim_form", "Claim ID: CLM-005\nVehicle: KA-01-AB-1234\nType: Accidental Damage\nAmount: 80000 INR\nDate: 2026-09-01")
write_doc(c5_id, "repair_estimate", "Car repair: 80000 INR")
write_doc(c5_id, "customer_description", "I hit a pothole and damaged the suspension.")

with open("data/claims/claims.json", "w") as f:
    json.dump(claims, f, indent=4)

print("Data generated successfully.")
