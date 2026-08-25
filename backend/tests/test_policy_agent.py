import pytest
from app.models.approval import PolicyComplianceStatus
from app.services.policy_engine import PolicyEngine

HAND_LABELED_DATASET = [
    # --- 10 COMPLIANT REQUESTS ---
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
    # --- 10 VIOLATIONS ---
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
    # --- 10 AMBIGUOUS / INSUFFICIENT EVIDENCE / NEEDS REVIEW ---
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
]


def test_hand_labeled_dataset_evaluation():
    engine = PolicyEngine()
    total = len(HAND_LABELED_DATASET)
    passed = 0
    y_true = []
    y_pred = []

    for item in HAND_LABELED_DATASET:
        result = engine.evaluate_request(
            title=item["title"],
            description=item["description"],
            amount=item["amount"],
            category=item["category"],
            vendor_name=item["vendor_name"],
        )
        y_true.append(item["expected_status"].value)
        y_pred.append(result.status.value)

        # Ensure citations are always present and valid
        assert len(result.citations) > 0, f"Expected citations for {item['id']}"
        for citation in result.citations:
            assert "section" in citation
            assert "line_number" in citation
            assert "snippet" in citation
            assert len(citation["snippet"]) > 10

        if result.status == item["expected_status"]:
            passed += 1
        else:
            print(f"Mismatch on {item['id']}: expected {item['expected_status']}, got {result.status}. Reason: {result.reason}")

    # Compute overall metrics
    accuracy = (passed / total) * 100.0

    # Binary metrics: Compliant vs Non-Compliant/Review/Violation
    true_positives = sum(1 for yt, yp in zip(y_true, y_pred) if yt == PolicyComplianceStatus.LIKELY_COMPLIANT.value and yp == yt)
    false_positives = sum(1 for yt, yp in zip(y_true, y_pred) if yt != PolicyComplianceStatus.LIKELY_COMPLIANT.value and yp == PolicyComplianceStatus.LIKELY_COMPLIANT.value)
    false_negatives = sum(1 for yt, yp in zip(y_true, y_pred) if yt == PolicyComplianceStatus.LIKELY_COMPLIANT.value and yp != PolicyComplianceStatus.LIKELY_COMPLIANT.value)

    precision = (true_positives / (true_positives + false_positives)) * 100.0 if (true_positives + false_positives) > 0 else 0.0
    recall = (true_positives / (true_positives + false_negatives)) * 100.0 if (true_positives + false_negatives) > 0 else 0.0

    print(f"\n================ POLICY AGENT EVALUATION REPORT ================")
    print(f"Total Hand-Labeled Test Cases: {total}")
    print(f"Exact Matches: {passed}/{total} ({accuracy:.1f}%)")
    print(f"Compliant Precision: {precision:.1f}%")
    print(f"Compliant Recall: {recall:.1f}%")
    print(f"=================================================================\n")

    assert passed == total, f"Expected {total}/{total} cases to pass, got {passed}/{total}"
    assert precision == 100.0
    assert recall == 100.0
