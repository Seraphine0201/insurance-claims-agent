import streamlit as st

# st.set_page_config(page_title="FAQ", page_icon="❓", layout="wide")

st.title("❓ Frequently Asked Questions")

faqs = [
    (
        "What documents do I need to file a claim?",
        "You'll need five documents from the at-fault policyholder: a driving "
        "licence, PAN card, Aadhaar card, vehicle Registration Certificate (RC), "
        "and the First Information Report (FIR) filed with the police after the "
        "accident. You'll also need one or more clear photos of the damage to "
        "the third-party vehicle."
    ),
    (
        "How long does claim processing take?",
        "Most claims are processed within minutes of submission. If your claim "
        "requires additional review — for example, if the estimated damage cost "
        "exceeds ₹50,000 and a licensed surveyor must be assigned — this can take "
        "longer, in line with standard regulatory timelines."
    ),
    (
        "Why was my claim escalated instead of approved immediately?",
        "Claims are escalated for human review in several situations: if the "
        "estimated repair cost is ₹50,000 or more (which legally requires a "
        "licensed surveyor), if the uploaded damage photos aren't clear enough "
        "for a confident automated assessment, or if any details need further "
        "verification. Escalation is not a rejection — it simply means a person "
        "will review your claim before a final decision is made."
    ),
    (
        "What is 'third-party' insurance, and who does it cover?",
        "Third-party insurance covers damage or injury you (the policyholder) "
        "cause to someone else's vehicle or property. If you're the person whose "
        "vehicle was hit, you are the 'third party' — the claim is filed against "
        "the at-fault driver's policy, and you do not need your own insurance "
        "policy with the same insurer to be compensated."
    ),
    (
        "What happens if the at-fault driver had an invalid or expired licence?",
        "An invalid licence does not prevent an innocent third party from being "
        "compensated. This system follows the standard 'pay and recover' "
        "principle: the insurer pays the claim to the third party first, then "
        "separately pursues recovery of costs from the policyholder."
    ),
    (
        "How can I check the status of my claim?",
        "Use the 'Track My Claim' page in the sidebar and enter your Claim ID, "
        "which you received after submitting your claim."
    ),
    (
        "Is my data secure?",
        "Yes. Uploaded documents are processed only to verify and assess your "
        "claim. Detailed internal records are restricted to authorized insurance "
        "staff only, and every claim decision is logged in a permanent, "
        "tamper-evident audit trail for compliance purposes."
    ),
    (
        "What if my claim was rejected?",
        "A rejection typically means the policy was not active on the date of "
        "the incident, or key details could not be verified. Please contact "
        "our support team (see the Contact page) for a detailed explanation "
        "and next steps."
    ),
]

for question, answer in faqs:
    with st.expander(question):
        st.write(answer)