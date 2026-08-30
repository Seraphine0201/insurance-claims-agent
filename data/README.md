# Data Files Reference

## cost_reference.json
Used by: **Assessment Agent**
Purpose: Maps damaged part + severity → cost range (₹). Assessment Agent classifies
damage from photos via Gemini vision, then looks up the actual price here instead
of letting the AI hallucinate a number.

## mock_policies.json
Used by: **Verification Agent**
Purpose: Simulates the insurer's policy database. Verification Agent cross-checks
OCR-extracted policyholder documents (Aadhaar/PAN/licence) against this to confirm
policy validity, licence validity, and identity match.

## claim_history.json
Used by: **Fraud Check Agent**
Purpose: Past third-party claims per policyholder. Used for point-of-impact
consistency checks and duplicate/collusion detection (e.g. same third-party
vehicle number appearing across multiple claims from the same policyholder).