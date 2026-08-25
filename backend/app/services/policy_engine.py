import os
import re
from dataclasses import dataclass
from pathlib import Path
from app.core.config import settings
from app.models.approval import PolicyComplianceStatus
from app.models.spend_request import SpendCategory, SpendRequest


@dataclass
class PolicyCitation:
    section: str
    line_number: int
    snippet: str
    relevance: str


@dataclass
class PolicyEvaluationResult:
    status: PolicyComplianceStatus
    score: float
    reason: str
    citations: list[dict]


class PolicyParser:
    """Parses markdown policy document into indexed lines and sections."""

    def __init__(self, policy_path: str = settings.POLICY_FILE_PATH):
        self.policy_path = policy_path
        self.sections: dict[str, dict] = {}
        self.lines: dict[int, dict] = {}
        self.raw_content = ""
        self._load_and_parse()

    def _load_and_parse(self):
        path = Path(self.policy_path)
        if not path.exists():
            return

        self.raw_content = path.read_text(encoding="utf-8")
        current_section = "GENERAL"
        section_title = "General"

        for line in self.raw_content.splitlines():
            line_str = line.strip()
            sec_match = re.search(r"##\s+\d+\.\s+(.*?)\s+\((SEC-\d+)\)", line_str)
            if sec_match:
                section_title = sec_match.group(1).strip()
                current_section = sec_match.group(2).strip()
                self.sections[current_section] = {
                    "code": current_section,
                    "title": section_title,
                    "lines": [],
                }
                continue

            line_match = re.match(r"Line\s+(\d+):\s+(.*)", line_str)
            if line_match:
                num = int(line_match.group(1))
                text = line_match.group(2).strip()
                item = {
                    "line_number": num,
                    "section": current_section,
                    "section_title": section_title,
                    "text": text,
                }
                self.lines[num] = item
                if current_section in self.sections:
                    self.sections[current_section]["lines"].append(item)

    def get_line(self, line_num: int) -> dict | None:
        return self.lines.get(line_num)


class PolicyEngine:
    """Evaluates spend requests against written corporate policy with grounded citations."""

    def __init__(self, policy_path: str = settings.POLICY_FILE_PATH):
        self.parser = PolicyParser(policy_path)

    def evaluate_request(
        self,
        title: str,
        description: str,
        amount: float,
        category: SpendCategory | str,
        vendor_name: str,
        department: str | None = None,
    ) -> PolicyEvaluationResult:
        cat = category.value if isinstance(category, SpendCategory) else str(category)
        text_corpus = f"{title} {description} {vendor_name}".lower()

        # Check 1: Insufficient Grounding / Missing Information (SEC-1, Line 4; SEC-7, Line 27)
        lower_title = title.lower().strip()
        is_vague_title = lower_title in ["payment", "invoice", "urgent payment", "stuff", "items", "project payment", "general expense", "general expenses", "miscellaneous", "misc", "urgent spend"] or any(
            vague in lower_title for vague in ["miscellaneous items", "misc expense", "general expense", "urgent spend", "unitemized"]
        )
        is_missing_vendor = not vendor_name or vendor_name.strip().lower() in ["unknown", "tbd", "n/a", "none", "various", ""]
        is_sparse_desc = len(description.strip()) < 15 and not any(k in description.lower() for k in ["license", "laptop", "flight", "lunch", "dinner", "monitor"])

        if is_vague_title or is_missing_vendor or is_sparse_desc:
            line = self.parser.get_line(4) or {
                "section": "SEC-1",
                "line_number": 4,
                "text": "Requests submitted without vendor details, itemized cost breakdowns, or legitimate justification will be returned for clarification.",
            }
            line27 = self.parser.get_line(27) or {
                "section": "SEC-7",
                "line_number": 27,
                "text": "Unsubstantiated miscellaneous expenses titled 'miscellaneous' or 'general expenses' without itemized invoices will be rejected.",
            }
            citations = [
                {
                    "section": line["section"],
                    "line_number": line["line_number"],
                    "snippet": line["text"],
                    "relevance": "Spend request lacks itemized cost breakdown or verified vendor identity.",
                }
            ]
            if is_vague_title:
                citations.append(
                    {
                        "section": line27["section"],
                        "line_number": line27["line_number"],
                        "snippet": line27["text"],
                        "relevance": "Generic or unitemized expense descriptions require substantiation.",
                    }
                )
            return PolicyEvaluationResult(
                status=PolicyComplianceStatus.INSUFFICIENT_EVIDENCE,
                score=0.20,
                reason="Insufficient evidence provided. Request lacks required vendor identification or itemized breakdown for compliance auditing.",
                citations=citations,
            )

        # Check 1b: Split purchases & multi-part transactions (SEC-1, Line 3)
        if any(term in text_corpus for term in ["instalment", "installment", "part 1", "part 2", "split payment", "deposit for"]):
            line = self.parser.get_line(3) or {
                "section": "SEC-1",
                "line_number": 3,
                "text": "Splitting purchases into multiple smaller transactions to circumvent approval thresholds is strictly prohibited.",
            }
            return PolicyEvaluationResult(
                status=PolicyComplianceStatus.NEEDS_REVIEW,
                score=0.60,
                reason=f"Potential multi-part or split transaction detected ({line['section']} Line {line['line_number']}). Requires compliance review to prevent threshold circumvention.",
                citations=[
                    {
                        "section": line["section"],
                        "line_number": line["line_number"],
                        "snippet": line["text"],
                        "relevance": "Anti-structuring rule: multi-part transaction requires review.",
                    }
                ],
            )

        # Check 2: Strictly Prohibited Personal Expenses & Prohibited Items (SEC-7, Line 24, 26)
        personal_triggers = [
            "gym membership", "fitness", "home utility", "utility bill", "electricity", "electric bill",
            "personal transit", "apartment rent", "groceries for home", "crypto", "gift card", "cash gift",
            "personal massage", "spa", "personal clothing"
        ]
        if any(trigger in text_corpus for trigger in personal_triggers):
            is_gift = any(g in text_corpus for g in ["gift card", "crypto", "cash gift"])
            line_num = 26 if is_gift else 24
            line = self.parser.get_line(line_num) or {
                "section": "SEC-7",
                "line_number": line_num,
                "text": "Personal expenses are strictly non-reimbursable." if line_num == 24 else "Giving or receiving cash, gift cards, or cryptocurrency as business gifts is strictly prohibited.",
            }
            return PolicyEvaluationResult(
                status=PolicyComplianceStatus.LIKELY_VIOLATION,
                score=0.05,
                reason=f"Violation of prohibited spend policy ({line['section']} Line {line['line_number']}). Non-business personal or cash-equivalent expenditures cannot be approved.",
                citations=[
                    {
                        "section": line["section"],
                        "line_number": line["line_number"],
                        "snippet": line["text"],
                        "relevance": "Non-compliant personal or cash-equivalent spend detected.",
                    }
                ],
            )

        # Check 3: Alcohol-only purchases (SEC-4, Line 17)
        if any(term in text_corpus for term in ["cocktails", "bar tab", "liquor", "alcohol only", "beer run"]) and not any(food in text_corpus for food in ["meal", "dinner", "lunch", "catering"]):
            line = self.parser.get_line(17) or {
                "section": "SEC-4",
                "line_number": 17,
                "text": "Alcohol-only expenditures without an accompanying business meal are non-reimbursable.",
            }
            return PolicyEvaluationResult(
                status=PolicyComplianceStatus.LIKELY_VIOLATION,
                score=0.10,
                reason=f"Violation of travel and entertainment policy ({line['section']} Line {line['line_number']}). Alcohol expenditures without an accompanying business meal are non-reimbursable.",
                citations=[
                    {
                        "section": line["section"],
                        "line_number": line["line_number"],
                        "snippet": line["text"],
                        "relevance": "Alcohol-only expenditure without business meal justification.",
                    }
                ],
            )

        # Check 4: Excessive Single Meal Limits (SEC-4, Line 15)
        if cat == "TRAVEL_ENTERTAINMENT" and any(m in text_corpus for m in ["dinner", "lunch", "breakfast", "meal", "food"]):
            # Check for explicit per-person overages if single person meal exceeds $75
            single_person = any(s in text_corpus for s in ["solo", "1 person", "single traveler", "myself", "personal dinner"]) or ("attendee" not in text_corpus and "team" not in text_corpus and "client" not in text_corpus)
            if single_person and amount > 75.0:
                line = self.parser.get_line(15) or {
                    "section": "SEC-4",
                    "line_number": 15,
                    "text": "Single meal reimbursements must not exceed $75.00 per person for dinner or $35.00 per person for lunch/breakfast.",
                }
                return PolicyEvaluationResult(
                    status=PolicyComplianceStatus.LIKELY_VIOLATION,
                    score=0.15,
                    reason=f"Single meal claim (${amount:.2f}) exceeds the maximum per-person meal allowance ($75.00) under {line['section']} Line {line['line_number']}.",
                    citations=[
                        {
                            "section": line["section"],
                            "line_number": line["line_number"],
                            "snippet": line["text"],
                            "relevance": "Individual meal expense exceeds allowable limit.",
                        }
                    ],
                )

        # Check 5: Multi-year software commitments (SEC-2, Line 9)
        if cat == "SOFTWARE_SAAS" and any(term in text_corpus for term in ["2-year", "3-year", "multi-year", "multi year", "24 month", "36 month"]):
            line = self.parser.get_line(9) or {
                "section": "SEC-2",
                "line_number": 9,
                "text": "Multi-year software commitments (>12 months) require Legal Counsel review and CFO authorization regardless of total spend.",
            }
            return PolicyEvaluationResult(
                status=PolicyComplianceStatus.NEEDS_REVIEW,
                score=0.55,
                reason=f"Multi-year software commitment detected ({line['section']} Line {line['line_number']}). Requires Legal Counsel and CFO authorization.",
                citations=[
                    {
                        "section": line["section"],
                        "line_number": line["line_number"],
                        "snippet": line["text"],
                        "relevance": "Multi-year commitment requires Legal and CFO sign-off.",
                    }
                ],
            )

        # Check 6: Generative AI Services processing customer or confidential data (SEC-2, Line 7)
        if any(ai_term in text_corpus for ai_term in ["generative ai", "llm api", "openai api", "anthropic api", "chatgpt team", "copilot", "claude enterprise"]) and any(data_term in text_corpus for data_term in ["customer data", "confidential", "source code", "proprietary", "production"]):
            line = self.parser.get_line(7) or {
                "section": "SEC-2",
                "line_number": 7,
                "text": "Use of commercial generative AI tools processing confidential company or customer data requires Security approval and SOC2 Type II verification.",
            }
            return PolicyEvaluationResult(
                status=PolicyComplianceStatus.NEEDS_REVIEW,
                score=0.50,
                reason=f"AI service handling sensitive company or customer data ({line['section']} Line {line['line_number']}). Mandatory Security review and SOC2 verification required.",
                citations=[
                    {
                        "section": line["section"],
                        "line_number": line["line_number"],
                        "snippet": line["text"],
                        "relevance": "Commercial AI tool processing confidential data requires Security verification.",
                    }
                ],
            )

        # Check 7: Restricted / Sanctioned Vendors (SEC-6, Line 21)
        sanctioned_keywords = ["sanctioned entity", "unverified offshore", "unregistered tax id", "blocked vendor", "anonymous offshore llc"]
        if any(sk in text_corpus for sk in sanctioned_keywords):
            line = self.parser.get_line(21) or {
                "section": "SEC-6",
                "line_number": 21,
                "text": "Any vendor appearing on government sanctions lists or lacking verified tax identification (W-9 / W-8BEN) cannot be onboarded.",
            }
            return PolicyEvaluationResult(
                status=PolicyComplianceStatus.LIKELY_VIOLATION,
                score=0.02,
                reason=f"Restricted vendor compliance alert ({line['section']} Line {line['line_number']}). Vendor fails tax verification or sanctions screening.",
                citations=[
                    {
                        "section": line["section"],
                        "line_number": line["line_number"],
                        "snippet": line["text"],
                        "relevance": "Vendor flagged in compliance screening.",
                    }
                ],
            )

        # Check 8: Large Team Events / Offsites (SEC-4, Line 16)
        if cat == "TRAVEL_ENTERTAINMENT" and amount > 1500.0 and any(w in text_corpus for w in ["offsite", "team event", "all hands", "dinner for team", "retreat"]):
            line = self.parser.get_line(16) or {
                "section": "SEC-4",
                "line_number": 16,
                "text": "Team offsites, dinners, or entertainment events exceeding $1,500.00 total require prior written approval from the Department VP.",
            }
            return PolicyEvaluationResult(
                status=PolicyComplianceStatus.NEEDS_REVIEW,
                score=0.60,
                reason=f"Team event spend exceeds $1,500.00 threshold ({line['section']} Line {line['line_number']}). Department VP written approval required.",
                citations=[
                    {
                        "section": line["section"],
                        "line_number": line["line_number"],
                        "snippet": line["text"],
                        "relevance": "Team entertainment threshold exceeded.",
                    }
                ],
            )

        # Check 9: High-value Consulting without Statement of Work (SEC-5, Line 19)
        if cat == "CONSULTING_CONTRACTOR" and amount > 5000.0:
            has_sow = any(s in text_corpus for s in ["sow attached", "executed msas", "sow signed", "legal approved sow"])
            if not has_sow:
                line = self.parser.get_line(19) or {
                    "section": "SEC-5",
                    "line_number": 19,
                    "text": "Consulting agreements exceeding $5,000.00 require Legal Counsel review and approval prior to contractor onboarding.",
                }
                return PolicyEvaluationResult(
                    status=PolicyComplianceStatus.NEEDS_REVIEW,
                    score=0.55,
                    reason=f"Consulting engagement exceeds $5,000.00 ({line['section']} Line {line['line_number']}). SOW and Legal Counsel review required.",
                    citations=[
                        {
                            "section": line["section"],
                            "line_number": line["line_number"],
                            "snippet": line["text"],
                            "relevance": "Consulting over $5,000 requires SOW and Legal sign-off.",
                        }
                    ],
                )

        # Check 10: Standard Compliant Purchases
        # Software under $500 from approved catalog (SEC-2, Line 8)
        if cat == "SOFTWARE_SAAS" and amount <= 500.0:
            line = self.parser.get_line(8) or {
                "section": "SEC-2",
                "line_number": 8,
                "text": "Software purchases under $500.00 from pre-approved internal app catalogs may proceed with direct manager approval only.",
            }
            return PolicyEvaluationResult(
                status=PolicyComplianceStatus.LIKELY_COMPLIANT,
                score=0.95,
                reason=f"Standard SaaS spend under $500.00 limit ({line['section']} Line {line['line_number']}). Compliant with standard manager routing.",
                citations=[
                    {
                        "section": line["section"],
                        "line_number": line["line_number"],
                        "snippet": line["text"],
                        "relevance": "Pre-approved software under $500 threshold.",
                    }
                ],
            )

        # Standard hardware or office supplies
        if cat == "HARDWARE" and amount <= 500.0:
            line = self.parser.get_line(11) or {
                "section": "SEC-3",
                "line_number": 11,
                "text": "Peripheral devices, monitors, and home office equipment exceeding $500.00 require IT Operations department verification.",
            }
            return PolicyEvaluationResult(
                status=PolicyComplianceStatus.LIKELY_COMPLIANT,
                score=0.95,
                reason=f"Peripheral equipment within allowable standard limit ({line['section']} Line {line['line_number']}). Compliant with standard procurement.",
                citations=[
                    {
                        "section": line["section"],
                        "line_number": line["line_number"],
                        "snippet": line["text"],
                        "relevance": "Equipment purchase within standard peripheral tier.",
                    }
                ],
            )

        # Standard business meal under limit (SEC-4, Line 15)
        if cat == "TRAVEL_ENTERTAINMENT" and amount <= 75.0 and any(w in text_corpus for w in ["meal", "lunch", "dinner", "breakfast", "coffee meeting"]):
            line = self.parser.get_line(15) or {
                "section": "SEC-4",
                "line_number": 15,
                "text": "Single meal reimbursements must not exceed $75.00 per person for dinner or $35.00 per person for lunch/breakfast.",
            }
            return PolicyEvaluationResult(
                status=PolicyComplianceStatus.LIKELY_COMPLIANT,
                score=0.96,
                reason=f"Business meal within per-person policy threshold ({line['section']} Line {line['line_number']}). Compliant with travel policy.",
                citations=[
                    {
                        "section": line["section"],
                        "line_number": line["line_number"],
                        "snippet": line["text"],
                        "relevance": "Meal claim within allowable per-person limit.",
                    }
                ],
            )

        # General business spend meeting standard scope (SEC-1, Line 2)
        line2 = self.parser.get_line(2) or {
            "section": "SEC-1",
            "line_number": 2,
            "text": "All company expenditures must serve a direct business purpose, represent market value, and adhere to compliance routing.",
        }
        return PolicyEvaluationResult(
            status=PolicyComplianceStatus.LIKELY_COMPLIANT,
            score=0.90,
            reason=f"Valid business justification identified ({line2['section']} Line {line2['line_number']}). Ready for approval routing.",
            citations=[
                {
                    "section": line2["section"],
                    "line_number": line2["line_number"],
                    "snippet": line2["text"],
                    "relevance": "Legitimate business expenditure adhering to core procurement policy.",
                }
            ],
        )
