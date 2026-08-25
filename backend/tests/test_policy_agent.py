import pytest
from app.core.config import settings
from app.models.approval import PolicyComplianceStatus
from app.services.policy_engine import PolicyEngine

# Comprehensive hand-labeled evaluation dataset (35 cases) spanning compliant, explicit violations,
# insufficient evidence, and subtle boundary edge cases.
HAND_LABELED_DATASET = [
    # --- 10 CLEAR COMPLIANT REQUESTS ---
    {
        "id": "C-01",
        "title": "Figma Professional Annual License",
        "description": "Standard individual designer license for UX mockups and prototyping.",
        "amount": 180.00,
        "category": "SOFTWARE_SAAS",
        "vendor_name": "Figma Inc.",
        "expected_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
    },
    {
        "id": "C-02",
        "title": "Ergonomic External Monitor for Engineering",
        "description": "Dell 27-inch 4K monitor for home workstation setup.",
        "amount": 380.00,
        "category": "HARDWARE",
        "vendor_name": "Dell Technologies",
        "expected_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
    },
    {
        "id": "C-03",
        "title": "Postman Team Subscription",
        "description": "API testing and mock server tooling for backend engineering team.",
        "amount": 340.00,
        "category": "SOFTWARE_SAAS",
        "vendor_name": "Postman Inc.",
        "expected_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
    },
    {
        "id": "C-04",
        "title": "Client Business Dinner in Chicago",
        "description": "Dinner meeting with Acme Corp prospect, 3 attendees total.",
        "amount": 180.00,
        "category": "TRAVEL_ENTERTAINMENT",
        "vendor_name": "Gibsons Steakhouse",
        "expected_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
    },
    {
        "id": "C-05",
        "title": "Solo Travel Dinner in Seattle",
        "description": "Single dinner after arriving on evening flight for tech conference.",
        "amount": 58.50,
        "category": "TRAVEL_ENTERTAINMENT",
        "vendor_name": "Wild Ginger Seattle",
        "expected_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
    },
    {
        "id": "C-06",
        "title": "Office Whiteboard Supplies and Markers",
        "description": "Pack of dry erase markers, magnetic erasers, and sticky notes for sprint room.",
        "amount": 65.00,
        "category": "OFFICE_SUPPLIES",
        "vendor_name": "Staples Business",
        "expected_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
    },
    {
        "id": "C-07",
        "title": "USB-C Hub and Dongles for MacBook",
        "description": "Standard Anker multi-port adapter for developer laptop.",
        "amount": 49.99,
        "category": "HARDWARE",
        "vendor_name": "Anker Direct",
        "expected_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
    },
    {
        "id": "C-08",
        "title": "GitHub Copilot Individual Seat",
        "description": "Standard code assistance seat for frontend engineer.",
        "amount": 120.00,
        "category": "SOFTWARE_SAAS",
        "vendor_name": "GitHub Inc.",
        "expected_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
    },
    {
        "id": "C-09",
        "title": "LinkedIn Recruiter Lite Monthly Seat",
        "description": "Monthly sourcing seat for talent acquisition team.",
        "amount": 170.00,
        "category": "SOFTWARE_SAAS",
        "vendor_name": "LinkedIn Corporation",
        "expected_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
    },
    {
        "id": "C-10",
        "title": "Team Working Lunch During Quarterly Planning",
        "description": "Sandwich box catering for 6 engineers during sprint planning.",
        "amount": 135.00,
        "category": "TRAVEL_ENTERTAINMENT",
        "vendor_name": "Mendocino Farms Catering",
        "expected_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
    },

    # --- 10 CLEAR VIOLATIONS ---
    {
        "id": "V-01",
        "title": "Equinox Monthly Gym Membership",
        "description": "Monthly personal gym membership for fitness and wellness.",
        "amount": 280.00,
        "category": "OTHER",
        "vendor_name": "Equinox Fitness",
        "expected_status": PolicyComplianceStatus.LIKELY_VIOLATION,
    },
    {
        "id": "V-02",
        "title": "Amazon Gift Cards for Sales Incentive",
        "description": "10x $100 Amazon electronic gift card reward for quarterly SDR bonus.",
        "amount": 1000.00,
        "category": "OTHER",
        "vendor_name": "Amazon Digital Services",
        "expected_status": PolicyComplianceStatus.LIKELY_VIOLATION,
    },
    {
        "id": "V-03",
        "title": "Home Electricity and Utility Bill",
        "description": "Monthly electric utility bill for remote home office.",
        "amount": 215.00,
        "category": "OTHER",
        "vendor_name": "Pacific Gas & Electric",
        "expected_status": PolicyComplianceStatus.LIKELY_VIOLATION,
    },
    {
        "id": "V-04",
        "title": "After-work Cocktails at Hotel Lounge",
        "description": "Drinks and cocktails with colleagues, bar tab only.",
        "amount": 240.00,
        "category": "TRAVEL_ENTERTAINMENT",
        "vendor_name": "The Speakeasy Lounge",
        "expected_status": PolicyComplianceStatus.LIKELY_VIOLATION,
    },
    {
        "id": "V-05",
        "title": "Solo Dinner Over Policy Limit",
        "description": "Single dinner room service during solo business travel in Boston.",
        "amount": 145.00,
        "category": "TRAVEL_ENTERTAINMENT",
        "vendor_name": "The Ritz-Carlton Dining",
        "expected_status": PolicyComplianceStatus.LIKELY_VIOLATION,
    },
    {
        "id": "V-06",
        "title": "Cryptocurrency Bonus Reward for Contractor",
        "description": "Direct USDT crypto transfer for rapid contractor milestone payment.",
        "amount": 2500.00,
        "category": "CONSULTING_CONTRACTOR",
        "vendor_name": "Binance Pay",
        "expected_status": PolicyComplianceStatus.LIKELY_VIOLATION,
    },
    {
        "id": "V-07",
        "title": "Engagement with Sanctioned Offshore Entity",
        "description": "Software localization contract with sanctioned entity lacking W8 tax forms.",
        "amount": 4200.00,
        "category": "CONSULTING_CONTRACTOR",
        "vendor_name": "Sanctioned Entity Global",
        "expected_status": PolicyComplianceStatus.LIKELY_VIOLATION,
    },
    {
        "id": "V-08",
        "title": "Personal Spa and Massage Session",
        "description": "Personal spa treatment during weekend between company meetings.",
        "amount": 220.00,
        "category": "TRAVEL_ENTERTAINMENT",
        "vendor_name": "Bliss Spa",
        "expected_status": PolicyComplianceStatus.LIKELY_VIOLATION,
    },
    {
        "id": "V-09",
        "title": "Unregistered Tax ID Contractor Payment",
        "description": "Web design assistance through unregistered tax id provider.",
        "amount": 1800.00,
        "category": "CONSULTING_CONTRACTOR",
        "vendor_name": "Unregistered Tax ID Studio",
        "expected_status": PolicyComplianceStatus.LIKELY_VIOLATION,
    },
    {
        "id": "V-10",
        "title": "Single Traveler Lunch Over Limit",
        "description": "Single solo lunch at high-end airport bistro before flight.",
        "amount": 85.00,
        "category": "TRAVEL_ENTERTAINMENT",
        "vendor_name": "Caviar & Oyster Bar SFO",
        "expected_status": PolicyComplianceStatus.LIKELY_VIOLATION,
    },

    # --- 10 AMBIGUOUS / INSUFFICIENT EVIDENCE / GOVERNANCE REVIEW ---
    {
        "id": "A-01",
        "title": "Miscellaneous Items for Project",
        "description": "Stuff needed for the upcoming demo next week.",
        "amount": 350.00,
        "category": "OFFICE_SUPPLIES",
        "vendor_name": "Various",
        "expected_status": PolicyComplianceStatus.INSUFFICIENT_EVIDENCE,
    },
    {
        "id": "A-02",
        "title": "Urgent spend for team",
        "description": "payment required immediately",
        "amount": 1200.00,
        "category": "OTHER",
        "vendor_name": "TBD",
        "expected_status": PolicyComplianceStatus.INSUFFICIENT_EVIDENCE,
    },
    {
        "id": "A-03",
        "title": "General expenses reimbursement",
        "description": "expenses incurred while working on client account",
        "amount": 480.00,
        "category": "OTHER",
        "vendor_name": "N/A",
        "expected_status": PolicyComplianceStatus.INSUFFICIENT_EVIDENCE,
    },
    {
        "id": "A-04",
        "title": "Project Materials",
        "description": "Hardware parts",
        "amount": 290.00,
        "category": "HARDWARE",
        "vendor_name": "Unknown",
        "expected_status": PolicyComplianceStatus.INSUFFICIENT_EVIDENCE,
    },
    {
        "id": "A-05",
        "title": "Custom Generative AI Agent with Customer Data",
        "description": "Integrating LLM API to process production customer data and proprietary source code.",
        "amount": 3200.00,
        "category": "SOFTWARE_SAAS",
        "vendor_name": "OpenAI API Platform",
        "expected_status": PolicyComplianceStatus.NEEDS_REVIEW,
    },
    {
        "id": "A-06",
        "title": "3-Year Enterprise CRM License Commitment",
        "description": "36-month multi-year commitment for sales pipeline management.",
        "amount": 45000.00,
        "category": "SOFTWARE_SAAS",
        "vendor_name": "Salesforce Inc.",
        "expected_status": PolicyComplianceStatus.NEEDS_REVIEW,
    },
    {
        "id": "A-07",
        "title": "Engineering Team Quarterly Offsite in Tahoe",
        "description": "Cabin rental and all hands team event expenses for 12 engineers.",
        "amount": 4200.00,
        "category": "TRAVEL_ENTERTAINMENT",
        "vendor_name": "Tahoe Mountain Lodging",
        "expected_status": PolicyComplianceStatus.NEEDS_REVIEW,
    },
    {
        "id": "A-08",
        "title": "Brand Strategy Consulting Engagement",
        "description": "10-week brand positioning advisory. SOW pending final execution.",
        "amount": 18000.00,
        "category": "CONSULTING_CONTRACTOR",
        "vendor_name": "Pentagram Design Advisory",
        "expected_status": PolicyComplianceStatus.NEEDS_REVIEW,
    },
    {
        "id": "A-09",
        "title": "Commercial Claude Enterprise Seat Deployment",
        "description": "Deploying Claude Enterprise across engineering handling confidential repositories.",
        "amount": 6000.00,
        "category": "SOFTWARE_SAAS",
        "vendor_name": "Anthropic PBC",
        "expected_status": PolicyComplianceStatus.NEEDS_REVIEW,
    },
    {
        "id": "A-10",
        "title": "Unitemized Project Payment",
        "description": "payment",
        "amount": 650.00,
        "category": "OTHER",
        "vendor_name": "",
        "expected_status": PolicyComplianceStatus.INSUFFICIENT_EVIDENCE,
    },

    # --- 5 ADVERSARIAL REAL-WORLD BOUNDARY CASES ---
    # Case E-01: Split purchase heuristic test (Sub-threshold purchase with potential anti-structuring flag)
    # Ground truth: Needs compliance review due to multiple part indicators; single-pass static rule flags as compliant under $500
    {
        "id": "E-01",
        "title": "Cloud compute credits instalment part 1",
        "description": "Payment part 1 of 3 for cloud compute cluster invoice.",
        "amount": 480.00,
        "category": "SOFTWARE_SAAS",
        "vendor_name": "AWS Cloud Services",
        "expected_status": PolicyComplianceStatus.NEEDS_REVIEW,
    },
    # Case E-02: Borderline group meal without explicit attendee count ($160 total)
    # Ground truth: Needs review because without headcount it cannot be proven <= $75/person; single-pass flags compliant
    {
        "id": "E-02",
        "title": "Dinner with prospect in Boston",
        "description": "Dinner meeting discussing pilot deployment.",
        "amount": 160.00,
        "category": "TRAVEL_ENTERTAINMENT",
        "vendor_name": "Legal Sea Foods Boston",
        "expected_status": PolicyComplianceStatus.NEEDS_REVIEW,
    },
    # Case E-03: Pre-approved developer tool slightly above standard tier but with known catalog entry
    {
        "id": "E-03",
        "title": "JetBrains All Products Pack Team Pack",
        "description": "Annual IDE licenses for 4 backend developers from standard tool catalog.",
        "amount": 1100.00,
        "category": "SOFTWARE_SAAS",
        "vendor_name": "JetBrains s.r.o.",
        "expected_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
    },
    # Case E-04: Contractor rush milestone with MSA referenced in title
    {
        "id": "E-04",
        "title": "Contractor Frontend Deliverable (MSA #4401)",
        "description": "Milestone delivery for UI revamp under signed master agreement.",
        "amount": 4800.00,
        "category": "CONSULTING_CONTRACTOR",
        "vendor_name": "PixelCraft Studios LLC",
        "expected_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
    },
    # Case E-05: Offsite hotel deposit under $1,500 but explicitly labeled as deposit for a $5k event
    {
        "id": "E-05",
        "title": "Deposit for Engineering Offsite Venue",
        "description": "Initial 20% booking deposit for $6,000 team offsite lodge.",
        "amount": 1200.00,
        "category": "TRAVEL_ENTERTAINMENT",
        "vendor_name": "Napa Valley Resort",
        "expected_status": PolicyComplianceStatus.NEEDS_REVIEW,
    },
]


def test_hand_labeled_dataset_evaluation():
    engine = PolicyEngine()
    total = len(HAND_LABELED_DATASET)
    passed = 0
    mismatches = []
    y_true = []
    y_pred = []

    for item in HAND_LABELED_DATASET:
        result = engine.evaluate_request(
            title=item["title"],
            description=item["description"],
            amount=item["amount"],
            category=item["category"],
            vendor_name=item["vendor_name"],
            prefer_offline=True,
        )
        y_true.append(item["expected_status"].value)
        y_pred.append(result.status.value)

        # Ensure citations are always present and valid
        assert len(result.citations) > 0, f"Expected citations for {item['id']}"
        for citation in result.citations:
            assert "section" in citation
            assert "line_number" in citation
            assert "snippet" in citation
            assert len(citation["snippet"]) > 5

        if result.status == item["expected_status"]:
            passed += 1
        else:
            mismatches.append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "expected": item["expected_status"].value,
                    "actual": result.status.value,
                    "reason": result.reason,
                }
            )

    accuracy = (passed / total) * 100.0

    # Binary metrics: Compliant vs Non-Compliant/Review/Violation
    true_positives = sum(
        1
        for yt, yp in zip(y_true, y_pred)
        if yt == PolicyComplianceStatus.LIKELY_COMPLIANT.value and yp == yt
    )
    false_positives = sum(
        1
        for yt, yp in zip(y_true, y_pred)
        if yt != PolicyComplianceStatus.LIKELY_COMPLIANT.value
        and yp == PolicyComplianceStatus.LIKELY_COMPLIANT.value
    )
    false_negatives = sum(
        1
        for yt, yp in zip(y_true, y_pred)
        if yt == PolicyComplianceStatus.LIKELY_COMPLIANT.value
        and yp != PolicyComplianceStatus.LIKELY_COMPLIANT.value
    )

    precision = (
        (true_positives / (true_positives + false_positives)) * 100.0
        if (true_positives + false_positives) > 0
        else 0.0
    )
    recall = (
        (true_positives / (true_positives + false_negatives)) * 100.0
        if (true_positives + false_negatives) > 0
        else 0.0
    )
    f1_score = (
        (2 * precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    print(f"\n================ POLICY AGENT EVALUATION REPORT ================")
    print(f"Total Hand-Labeled Test Cases:   {total}")
    print(f"Exact Status Matches:            {passed}/{total} ({accuracy:.1f}%)")
    print(f"Compliant Precision:             {precision:.1f}%")
    print(f"Compliant Recall:                {recall:.1f}%")
    print(f"Compliant F1 Score:              {f1_score:.1f}%")
    print(f"Citation Grounding Rate:         100.0% (all decisions cited)")
    print(f"Failure / Boundary Edge Cases:   {len(mismatches)} documented misses")
    for m in mismatches:
        print(f"  - [{m['id']}] {m['title']}: Expected {m['expected']}, Classified as {m['actual']}")
    print(f"=================================================================\n")

    assert passed >= 32, f"Expected at least 32/35 cases to pass, got {passed}/{total}"
    assert precision >= 85.0
    assert recall >= 85.0


def test_gemini_policy_agent_resilient_fallback():
    """Verify that when Gemini API is offline or returns rate-limit (429), PolicyEngine falls back cleanly."""
    from app.services.policy_engine import GeminiPolicyAgent, PolicyParser

    parser = PolicyParser(settings.POLICY_FILE_PATH)
    # Instantiate with an invalid or rate-limited key to test fallback
    agent = GeminiPolicyAgent(parser=parser, api_key="dummy_key_to_test_fallback")
    
    # Live call to dummy endpoint will fail and return None
    result = agent.evaluate(
        title="Figma License",
        description="Design tool",
        amount=180.0,
        category="SOFTWARE_SAAS",
        vendor_name="Figma",
    )
    assert result is None, "Expected Gemini agent to return None on network/auth error"

    # Orchestrator gracefully falls back to deterministic auditor
    engine = PolicyEngine()
    fallback_result = engine.evaluate_request(
        title="Figma License",
        description="Design tool license",
        amount=180.0,
        category="SOFTWARE_SAAS",
        vendor_name="Figma",
    )
    assert fallback_result is not None
    assert fallback_result.status in [PolicyComplianceStatus.LIKELY_COMPLIANT, PolicyComplianceStatus.NEEDS_REVIEW]
    assert len(fallback_result.citations) > 0

