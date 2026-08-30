import asyncio
import os
import json
from unittest import result
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client



async def call_tool_with_retry(session, tool_name, arguments, max_retries=3):
    """
    Call an MCP tool, retrying if the response comes back with no content
    (a known intermittent issue with stdio-based MCP on some systems).
    """
    for attempt in range(1, max_retries + 1):
        result = await session.call_tool(tool_name, arguments=arguments, read_timeout_seconds=90)
        if result.content and len(result.content) > 0:
            return result
        print(f"  (empty response on attempt {attempt}, retrying...)")
        await asyncio.sleep(2)
    raise RuntimeError(f"Tool '{tool_name}' returned empty content after {max_retries} attempts")

SAMPLE_DOCS_FOLDER = "sample_docs"
DAMAGE_PHOTOS_FOLDER = "sample_docs/damage_photos"

DOCUMENT_TYPE_HINTS = {
    "licence": "driving_licence",
    "license": "driving_licence",
    "pan": "pan_card",
    "aadhaar": "aadhaar_card",
    "aadhar": "aadhaar_card",
    "rc": "registration_certificate",
    "fir": "fir",
}


def guess_document_type(filename):
    lower_name = filename.lower()
    for keyword, doc_type in DOCUMENT_TYPE_HINTS.items():
        if keyword in lower_name:
            return doc_type
    return "unknown_document"


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-u","mcp_servers/claims_mcp_server.py"],
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Step 1: List available tools
            tools = await session.list_tools()
            print("=== AVAILABLE TOOLS ===")
            for tool in tools.tools:
                first_line = next((line for line in tool.description.splitlines() if line.strip()), "")
                print(f"- {tool.name}: {first_line.strip()}")

            # Step 2: Dynamically find every "Ramesh" doc EXCEPT the violation FIR,
            # so we get exactly one FIR + the 4 identity docs — same rule test_fraud.py
            # and orchestrator.py already use: one FIR per claim.
            all_docs = [
                f for f in os.listdir(SAMPLE_DOCS_FOLDER)
                if f.lower().endswith((".png", ".jpg", ".jpeg")) and "violation" not in f.lower()
            ]

            intake_results = {}
            for filename in all_docs:
                doc_type = guess_document_type(filename)
                doc_path = os.path.join(SAMPLE_DOCS_FOLDER, filename)
                print(f"\n=== CALLING extract_document_data ({filename}) ===")
                result = await call_tool_with_retry(
                    session,
                    "extract_document_data",
                    arguments={"image_path": doc_path, "document_type": doc_type}
                )
                data = json.loads(result.content[0].text)
                print(data)
                intake_results[doc_type] = data["structured_data"]

            fir_data = intake_results["fir"]

            # Step 3: verify_policy — using data extracted above, nothing typed in
            print("\n=== CALLING verify_policy ===")
            verification_result = await call_tool_with_retry(
                session,
                "verify_policy",
                arguments={
                    "fir_data": fir_data,
                    "intake_results": intake_results,
                    "incident_date_str": fir_data.get("incident_date")
                }
            )
            verification_data = json.loads(verification_result.content[0].text)
            print(verification_data)

            policy_id = verification_data.get("policy_id")

            # Step 4: estimate_damage on every damage photo found
            damage_photo_files = [
                f for f in os.listdir(DAMAGE_PHOTOS_FOLDER)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
            damage_photo_path = os.path.join(DAMAGE_PHOTOS_FOLDER, damage_photo_files[0])

            print(f"\n=== CALLING estimate_damage ({damage_photo_files[0]}) ===")
            assessment_result = await call_tool_with_retry(
                session,
                "estimate_damage",
                arguments={"image_path": damage_photo_path}
                
            )
            assessment_data = json.loads(assessment_result.content[0].text)
            print(assessment_data)

            # Step 5: check_fraud — using the REAL policy_id from verify_policy, not typed in
            print("\n=== CALLING check_fraud ===")
            fraud_result = await call_tool_with_retry(
                session,
                "check_fraud",
                arguments={
                    "fir_data": fir_data,
                    "assessment_result": assessment_data,
                    "policy_id": policy_id
                }
            )
            fraud_data = json.loads(fraud_result.content[0].text)
            print(fraud_data)

            # Step 6: create_claim_record — the final decision, using everything above
            print("\n=== CALLING create_claim_record ===")
            decision_result = await call_tool_with_retry(
                session,
                "create_claim_record",
                arguments={
                    "verification_result": verification_data,
                    "assessment_result": assessment_data,
                    "fraud_result": fraud_data
                }
            )
            print(decision_result.content[0].text)


asyncio.run(main())