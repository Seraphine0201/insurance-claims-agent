import sys
import os
import time
# Add the project root to Python's search path, so "agents" can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.mcpserver import MCPServer

from agents.intake_agent import process_document
from agents.verification_agent import verify_claim
from agents.assessment_agent import assess_damage
from agents.fraud_agent import run_fraud_check
from agents.decision_agent import make_decision

# Create the MCP server — this is the "job board" that lists available tools
mcp = MCPServer("insurance-claims-tools")


@mcp.tool()
def extract_document_data(image_path: str, document_type: str) -> dict:
    """
    Extract structured data from an uploaded insurance document
    (driving licence, PAN card, Aadhaar card, RC, or FIR) using OCR + AI.

    Args:
        image_path: File path to the document image.
        document_type: One of "driving_licence", "pan_card", "aadhaar_card",
                        "registration_certificate", or "fir".

    Returns:
        A dictionary with the raw OCR text and structured extracted fields
        (name, vehicle_number, licence_number, etc., depending on document type).
    """
    result = process_document(image_path, document_type)
    time.sleep(0.3)
    return result


@mcp.tool()
def verify_policy(fir_data: dict, intake_results: dict, incident_date_str: str) -> dict:
    """
    Verify a claim against the insurer's policy database — checks policy
    validity, licence validity, identity consistency across documents,
    and any traffic violations noted in the FIR.

    Args:
        fir_data: Structured data extracted from the FIR document.
        intake_results: Dictionary of {document_type: structured_data} for all
                         uploaded documents in this claim.
        incident_date_str: Date of the accident, format DD-MM-YYYY.

    Returns:
        A dictionary with verification_status (PASS/ESCALATE/REJECTED),
        matched policy ID, and detailed check results.
    """
    return verify_claim(fir_data, intake_results, incident_date_str)
    time.sleep(0.3)
    return result

@mcp.tool()
def estimate_damage(image_path: str) -> dict:
    """
    Analyze a photo of vehicle damage using AI vision, identify damaged
    parts and severity, and estimate repair cost from a reference table.

    Args:
        image_path: File path to the damage photo.

    Returns:
        A dictionary with damaged_parts, confidence level, cost_estimate,
        and whether the estimate exceeds the ₹50,000 surveyor threshold.
    """
    return assess_damage(image_path)
    time.sleep(0.3)
    return result

@mcp.tool()
def check_fraud(fir_data: dict, assessment_result: dict, policy_id: str) -> dict:
    """Check a claim for fraud signals — point-of-impact consistency between
    the FIR and assessed damage, plus claim-history cross-checks for
    duplicate FIRs or repeat third-party-vehicle collusion patterns.

    Args:
        fir_data: Structured data extracted from the FIR document.
        assessment_result: Output from estimate_damage for this claim's photos.
        policy_id: The policy ID matched by verify_policy.

    Returns:
        A dictionary with point_of_impact_check, claim_history_check,
        and overall_fraud_risk (low/medium/high).
    """
    return run_fraud_check(fir_data, assessment_result, policy_id)
    time.sleep(0.3)
    return result

@mcp.tool()
def create_claim_record(verification_result: dict, assessment_result: dict, fraud_result: dict) -> dict:
    """Make the final claims decision by combining verification, assessment,
    and fraud check results into one outcome: APPROVED, ESCALATED, or REJECTED.

    Args:
        verification_result: Output from verify_policy.
        assessment_result: Output from estimate_damage.
        fraud_result: Output from check_fraud.

    Returns:
        A dictionary with the final decision, reasons, and payout details.
    """
    return make_decision(verification_result, assessment_result, fraud_result)
    time.sleep(0.3)
    return result

if __name__ == "__main__":
    mcp.run()