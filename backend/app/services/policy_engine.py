import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
import httpx
from pydantic import BaseModel, Field
from app.core.config import settings
from app.models.approval import PolicyComplianceStatus
from app.models.spend_request import SpendCategory

logger = logging.getLogger(__name__)


class CitationItem(BaseModel):
    section: str = Field(..., description="Section tag, e.g., SEC-1, SEC-2")
    line_number: int = Field(..., description="1-indexed line number in policy document")
    snippet: str = Field(..., description="Verbatim text from policy line")
    relevance: str = Field(..., description="Why this policy line applies to the request")


class PolicyEvaluationResult(BaseModel):
    status: PolicyComplianceStatus
    score: float = Field(..., ge=0.0, le=1.0)
    reason: str
    citations: list[dict[str, Any]]
    model_provider: str = Field(default="deterministic-rule-engine", description="Model used: gemini-3.6-flash or deterministic-rule-engine")


class PolicyParser:
    def __init__(self, policy_path: str):
        self.policy_path = policy_path
        self.lines: list[dict[str, Any]] = []
        self._load_policy()

    def _load_policy(self) -> None:
        path = Path(self.policy_path)
        if not path.exists():
            raise FileNotFoundError(f"Procurement policy file not found at: {self.policy_path}")

        content = path.read_text(encoding="utf-8")
        current_section = "GENERAL"

        for idx, line in enumerate(content.splitlines(), start=1):
            line_str = line.strip()
            if not line_str:
                continue

            sec_match = re.search(r"\[(SEC-\d+)\]", line_str)
            if sec_match:
                current_section = sec_match.group(1)

            clean_text = re.sub(r"^(\d+\.\s*|[-*#]+\s*|\[SEC-\d+\]\s*)", "", line_str).strip()
            self.lines.append(
                {
                    "line_number": idx,
                    "section": current_section,
                    "raw_text": line_str,
                    "clean_text": clean_text,
                }
            )

    def get_line(self, line_number: int) -> dict[str, Any] | None:
        for item in self.lines:
            if item["line_number"] == line_number:
                return {
                    "line_number": item["line_number"],
                    "section": item["section"],
                    "text": item["clean_text"],
                }
        return None

    def get_full_markdown(self) -> str:
        path = Path(self.policy_path)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""


class GeminiPolicyAgent:
    """Live Google Gemini LLM policy auditor with structured JSON output and grounded citation extraction."""

    def __init__(self, parser: PolicyParser, api_key: str, model: str = "gemini-3.6-flash"):
        self.parser = parser
        self.api_key = api_key
        self.model = model
        self.endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        self._cache: dict[str, PolicyEvaluationResult] = {}

    def _build_system_prompt(self) -> str:
        policy_md = self.parser.get_full_markdown()
        return f"""You are Waypoint's AI Procurement Policy Auditor.
Your task is to audit corporate spend requests against the company procurement policy below.

COMPANY PROCUREMENT POLICY DOCUMENT:
\"\"\"
{policy_md}
\"\"\"

AUDITING RULES:
1. Grounding & Citations: Every single decision MUST cite the exact policy section (e.g. SEC-1, SEC-2) and the exact line number from the document.
2. Strict Honesty on Insufficient Evidence: If the spend request is vague (e.g. title is 'miscellaneous', 'urgent spend', 'project items'), missing vendor identity, or lacks itemized cost details, you MUST classify it as INSUFFICIENT_EVIDENCE citing SEC-1 Line 4 and SEC-7 Line 27. Do NOT invent justifications.
3. Prohibited Expenses: Personal expenses, gym memberships, home utilities, cryptocurrency, unitemized alcohol, or cash gift cards MUST be classified as LIKELY_VIOLATION citing SEC-7 Line 24/26.
4. Risk & Compliance: High-risk AI handling customer data (SEC-2 Line 7), multi-year commitments > 12 months (SEC-2 Line 9), or consulting > $5,000 without signed SOW (SEC-3 Line 11) MUST be classified as NEEDS_REVIEW.
5. Standard Compliant Spend: Standard tools within amount limits from legitimate vendors must be classified as LIKELY_COMPLIANT.

RESPONSE FORMAT:
You must respond with valid JSON adhering to this schema:
{{
  "status": "LIKELY_COMPLIANT" | "NEEDS_REVIEW" | "LIKELY_VIOLATION" | "INSUFFICIENT_EVIDENCE",
  "score": float between 0.0 and 1.0,
  "reason": "Clear explanation citing the relevant policy rule",
  "citations": [
    {{
      "section": "SEC-1",
      "line_number": 2,
      "snippet": "All company expenditures must serve a direct business purpose...",
      "relevance": "Why this line applies"
    }}
  ]
}}"""

    def evaluate(
        self,
        title: str,
        description: str,
        amount: float,
        category: str,
        vendor_name: str,
        department: str | None = None,
    ) -> PolicyEvaluationResult | None:
        cache_key = f"{title.lower()}|{description.lower()}|{amount}|{category}|{vendor_name.lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        user_content = f"""Spend Request to Audit:
- Title: {title}
- Description: {description}
- Amount: ${amount:,.2f} USD
- Category: {category}
- Vendor: {vendor_name}
- Department: {department or 'General'}"""

        payload = {
            "systemInstruction": {
                "parts": [{"text": self._build_system_prompt()}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_content}]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        }

        try:
            with httpx.Client(timeout=25.0) as client:
                response = client.post(self.endpoint_url, json=payload)

            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)

                status_val = parsed.get("status", "NEEDS_REVIEW")
                status = PolicyComplianceStatus(status_val) if status_val in [s.value for s in PolicyComplianceStatus] else PolicyComplianceStatus.NEEDS_REVIEW

                citations = parsed.get("citations", [])
                if not citations:
                    citations = [
                        {
                            "section": "SEC-1",
                            "line_number": 2,
                            "snippet": "All company expenditures must serve a direct business purpose, represent market value, and adhere to compliance routing.",
                            "relevance": "General procurement compliance standard.",
                        }
                    ]

                result = PolicyEvaluationResult(
                    status=status,
                    score=float(parsed.get("score", 0.5)),
                    reason=str(parsed.get("reason", "Audited by Gemini AI policy agent.")),
                    citations=citations,
                    model_provider=f"gemini ({self.model})",
                )
                self._cache[cache_key] = result
                return result
            else:
                logger.warning(
                    f"Gemini API returned status {response.status_code}: {response.text[:200]}. Falling back to deterministic auditor."
                )
                return None
        except Exception as exc:
            logger.warning(f"Gemini policy evaluation request failed: {exc}. Falling back to deterministic auditor.")
            return None


class DeterministicPolicyAuditor:
    """Fast, deterministic policy auditor for offline benchmarking, local testing, and rate-limit fallback."""

    def __init__(self, parser: PolicyParser):
        self.parser = parser

    def evaluate(
        self,
        title: str,
        description: str,
        amount: float,
        category: str,
        vendor_name: str,
        department: str | None = None,
    ) -> PolicyEvaluationResult:
        text_corpus = f"{title} {description} {vendor_name}".lower()
        lower_title = title.lower().strip()

        # Check 1: Insufficient Grounding / Missing Information (SEC-1, Line 4; SEC-7, Line 27)
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
                model_provider="deterministic-rule-engine",
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
                model_provider="deterministic-rule-engine",
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
                        "relevance": "Strict prohibition on non-reimbursable personal expenditures.",
                    }
                ],
                model_provider="deterministic-rule-engine",
            )

        # Check 3: Travel and Entertainment Overage Boundaries (SEC-4, Line 15, 17, 18)
        if category == SpendCategory.TRAVEL_ENTERTAINMENT.value:
            if any(k in text_corpus for k in ["bar tab", "cocktails", "alcohol", "nightclub"]) and not any(k in text_corpus for k in ["dinner", "lunch", "client meeting"]):
                line = self.parser.get_line(17) or {
                    "section": "SEC-4",
                    "line_number": 17,
                    "text": "Standalone bar tabs without meal accompaniment or pre-approved team celebration budget are non-reimbursable.",
                }
                return PolicyEvaluationResult(
                    status=PolicyComplianceStatus.LIKELY_VIOLATION,
                    score=0.10,
                    reason=f"Policy violation: standalone alcohol bar tab ({line['section']} Line {line['line_number']}).",
                    citations=[
                        {
                            "section": line["section"],
                            "line_number": line["line_number"],
                            "snippet": line["text"],
                            "relevance": "Standalone bar tabs are non-reimbursable under T&E policy.",
                        }
                    ],
                    model_provider="deterministic-rule-engine",
                )

            is_dinner = "dinner" in text_corpus
            is_lunch = "lunch" in text_corpus
            is_solo_or_single = any(s in text_corpus for s in ["single", "solo", "individual", "room service", "airport bistro", "one traveler"])

            if is_dinner and (amount > 75.00 and is_solo_or_single):
                line = self.parser.get_line(15) or {
                    "section": "SEC-4",
                    "line_number": 15,
                    "text": "Meals during individual business travel are capped at $25.00 for breakfast, $35.00 for lunch, and $75.00 for dinner per person.",
                }
                return PolicyEvaluationResult(
                    status=PolicyComplianceStatus.LIKELY_VIOLATION,
                    score=0.15,
                    reason=f"Individual dinner expense (${amount:.2f}) exceeds policy cap of $75.00 ({line['section']} Line {line['line_number']}).",
                    citations=[
                        {
                            "section": line["section"],
                            "line_number": line["line_number"],
                            "snippet": line["text"],
                            "relevance": "Per diem meal threshold exceeded for individual traveler.",
                        }
                    ],
                    model_provider="deterministic-rule-engine",
                )

            if is_lunch and (amount > 35.00 and is_solo_or_single):
                line = self.parser.get_line(15) or {
                    "section": "SEC-4",
                    "line_number": 15,
                    "text": "Meals during individual business travel are capped at $25.00 for breakfast, $35.00 for lunch, and $75.00 for dinner per person.",
                }
                return PolicyEvaluationResult(
                    status=PolicyComplianceStatus.LIKELY_VIOLATION,
                    score=0.15,
                    reason=f"Individual lunch expense (${amount:.2f}) exceeds policy cap of $35.00 ({line['section']} Line {line['line_number']}).",
                    citations=[
                        {
                            "section": line["section"],
                            "line_number": line["line_number"],
                            "snippet": line["text"],
                            "relevance": "Per diem meal threshold exceeded for individual traveler.",
                        }
                    ],
                    model_provider="deterministic-rule-engine",
                )

            if amount > 1500.00:
                line = self.parser.get_line(18) or {
                    "section": "SEC-4",
                    "line_number": 18,
                    "text": "Team offsites or group events exceeding $1,500.00 total require Department Head pre-approval before booking.",
                }
                return PolicyEvaluationResult(
                    status=PolicyComplianceStatus.NEEDS_REVIEW,
                    score=0.55,
                    reason=f"Group travel / team offsite exceeds $1,500.00 threshold ({line['section']} Line {line['line_number']}). Requires Department Head review.",
                    citations=[
                        {
                            "section": line["section"],
                            "line_number": line["line_number"],
                            "snippet": line["text"],
                            "relevance": "Group event requires Department Head pre-approval.",
                        }
                    ],
                    model_provider="deterministic-rule-engine",
                )

        # Check 4: Software & SaaS Governance (SEC-2, Line 6, 7, 8, 9)
        if category == SpendCategory.SOFTWARE_SAAS.value:
            if any(ai_term in text_corpus for ai_term in ["generative ai", "llm", "claude", "gpt", "customer data", "proprietary code"]):
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
                            "relevance": "Security & SOC2 review required for AI tooling with company data.",
                        }
                    ],
                    model_provider="deterministic-rule-engine",
                )

            if any(term in text_corpus for term in ["3-year", "multi-year", "36-month", "24-month", "multi year"]):
                line = self.parser.get_line(9) or {
                    "section": "SEC-2",
                    "line_number": 9,
                    "text": "Auto-renewing or multi-year SaaS contracts exceeding 12 months require Finance and Legal review regardless of amount.",
                }
                return PolicyEvaluationResult(
                    status=PolicyComplianceStatus.NEEDS_REVIEW,
                    score=0.50,
                    reason=f"Multi-year SaaS commitment exceeding 12 months ({line['section']} Line {line['line_number']}). Mandatory Finance & Legal review required.",
                    citations=[
                        {
                            "section": line["section"],
                            "line_number": line["line_number"],
                            "snippet": line["text"],
                            "relevance": "Multi-year commitments require Legal and Finance review.",
                        }
                    ],
                    model_provider="deterministic-rule-engine",
                )

            if amount < 500.00:
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
                            "relevance": "Low-risk software tier under $500.00.",
                        }
                    ],
                    model_provider="deterministic-rule-engine",
                )

        # Check 5: Consulting & Contractor Engagements (SEC-3, Line 10, 11, 12)
        if category == SpendCategory.CONSULTING_CONTRACTOR.value:
            if any(bad in text_corpus for bad in ["sanctioned", "no w8", "unregistered tax id"]):
                line = self.parser.get_line(12) or {
                    "section": "SEC-3",
                    "line_number": 12,
                    "text": "Contractor payments without verified W-9 / W-8BEN tax forms or involving restricted offshore jurisdictions are prohibited.",
                }
                return PolicyEvaluationResult(
                    status=PolicyComplianceStatus.LIKELY_VIOLATION,
                    score=0.05,
                    reason=f"Contractor compliance violation ({line['section']} Line {line['line_number']}). Missing tax forms or restricted jurisdiction.",
                    citations=[
                        {
                            "section": line["section"],
                            "line_number": line["line_number"],
                            "snippet": line["text"],
                            "relevance": "Tax documentation and jurisdiction restriction violation.",
                        }
                    ],
                    model_provider="deterministic-rule-engine",
                )

            if amount > 5000.00 and not any(k in text_corpus for k in ["sow executed", "msa signed", "executed sow"]):
                line = self.parser.get_line(11) or {
                    "section": "SEC-3",
                    "line_number": 11,
                    "text": "All professional services and contractor engagements exceeding $5,000.00 require a fully executed Statement of Work (SOW) and Legal review prior to work commencement.",
                }
                return PolicyEvaluationResult(
                    status=PolicyComplianceStatus.NEEDS_REVIEW,
                    score=0.55,
                    reason=f"Contractor engagement > $5,000.00 ({line['section']} Line {line['line_number']}). Requires executed SOW and Legal Counsel review.",
                    citations=[
                        {
                            "section": line["section"],
                            "line_number": line["line_number"],
                            "snippet": line["text"],
                            "relevance": "High-value consulting requires Legal review and SOW.",
                        }
                    ],
                    model_provider="deterministic-rule-engine",
                )

        # Default: Standard Compliant Spend
        line1 = self.parser.get_line(2) or {
            "section": "SEC-1",
            "line_number": 2,
            "text": "All company expenditures must serve a direct business purpose, represent market value, and adhere to compliance routing.",
        }
        citations = [
            {
                "section": line1["section"],
                "line_number": line1["line_number"],
                "snippet": line1["text"],
                "relevance": "General procurement compliance standard.",
            }
        ]

        if category == SpendCategory.SOFTWARE_SAAS.value and amount > 1000.00:
            line_sec = self.parser.get_line(6)
            if line_sec:
                citations.append(
                    {
                        "section": line_sec["section"],
                        "line_number": line_sec["line_number"],
                        "snippet": line_sec["text"],
                        "relevance": "Software exceeding $1,000 requires Security & IT review.",
                    }
                )

        return PolicyEvaluationResult(
            status=PolicyComplianceStatus.LIKELY_COMPLIANT,
            score=0.92,
            reason=f"Valid business justification identified ({line1['section']} Line {line1['line_number']}). Compliant spend routed through standard tiers.",
            citations=citations,
            model_provider="deterministic-rule-engine",
        )


class PolicyEngine:
    """Orchestrator supporting dual-mode evaluation: live Google Gemini LLM agent with resilient fallback to deterministic auditor."""

    def __init__(self, policy_path: str | None = None, enable_llm: bool = True):
        self.policy_path = policy_path or settings.POLICY_FILE_PATH
        self.parser = PolicyParser(self.policy_path)
        self.deterministic_auditor = DeterministicPolicyAuditor(self.parser)
        self.gemini_agent: GeminiPolicyAgent | None = None

        if enable_llm and settings.LLM_API_KEY:
            self.gemini_agent = GeminiPolicyAgent(
                parser=self.parser,
                api_key=settings.LLM_API_KEY,
                model=settings.GEMINI_MODEL,
            )

    def evaluate_request(
        self,
        title: str,
        description: str,
        amount: float,
        category: SpendCategory | str,
        vendor_name: str,
        department: str | None = None,
        prefer_offline: bool = False,
    ) -> PolicyEvaluationResult:
        cat = category.value if isinstance(category, SpendCategory) else str(category)

        # 1. Try Gemini LLM agent if configured and not explicitly running offline benchmark
        if self.gemini_agent and not prefer_offline:
            llm_result = self.gemini_agent.evaluate(
                title=title,
                description=description,
                amount=amount,
                category=cat,
                vendor_name=vendor_name,
                department=department,
            )
            if llm_result:
                return llm_result

        # 2. Fall back to high-performance deterministic auditor
        return self.deterministic_auditor.evaluate(
            title=title,
            description=description,
            amount=amount,
            category=cat,
            vendor_name=vendor_name,
            department=department,
        )
