# IRDAI Rules Engine
### Regulatory Text → Machine-Executable Compliance Rules → Automated Claim Verdicts

A Python-based RegTech system built on the **IRDAI Master Circular (2024)**.  
It does two things no off-the-shelf tool does together:

1. **Extracts** every decision rule from the IRDAI circular into structured JSON
2. **Applies** those rules to real insurance documents to return a legally-grounded claim verdict

Built by [JurisCode Labs](https://github.com/jainyo94) · MIT License · Python 3.9+

---

## 🔍 The Problem

The IRDAI Master Circular is 100+ pages of dense regulatory text like:

> *"No insurer shall reject a claim on grounds of non-disclosure of a pre-existing condition if the policy has been continuously in force for 60 months or more."*

Insurance companies interpret these rules inconsistently.  
Policyholders don't know their rights.  
Compliance teams manually track hundreds of such clauses.

**This engine makes those rules executable by a machine.**

---

## ⚙️ How It Works — Two Modules
┌─────────────────────────────────────────────────────────┐
│  MODULE 1 — Rule Extractor (extract.py)                 │
│                                                         │
│  IRDAI Circular PDF  →  Groq LLaMA 3.3 70B  →          │
│  Structured JSON Rules + Color-coded Excel              │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  MODULE 2 — Document Intelligence Engine (server.py)    │
│                                                         │
│  Policy PDF + Hospital PDF  →  Fact Extraction  →       │
│  Rules Engine  →  Claim Verdict (Pay / Deny / Review)   │
└─────────────────────────────────────────────────────────┘

---

## 📤 Sample Output

### Rule extracted from circular (`rules.json`):
```json
{
  "rule_id": "DR-2024-07",
  "rule_name": "Moratorium — Non-Disclosure Waiver",
  "rule_category": "Moratorium",
  "data_field_to_check": "continuous_coverage_months",
  "operator": "GREATER_THAN_OR_EQUAL",
  "target_value": 60,
  "target_unit": "months",
  "action": "BYPASS_NONDISCLOSURE_REJECTION",
  "obligated_party": "Insurer",
  "penalty_detail": "Not specified",
  "plain_english_explanation": "After 5 years of continuous coverage, an insurer cannot reject a claim because the policyholder did not disclose a pre-existing condition."
}
```

### Claim verdict from Document Engine:
```json
{
  "verdict": "pay",
  "action": "MANDATE_CLAIM_APPROVAL",
  "message": "Claim must be accepted under DR-2024-07",
  "confidence": "HIGH",
  "applied_rule": "Moratorium — Non-Disclosure Waiver",
  "missing_fields": []
}
```

---

## 🗂️ Project Structure
IRDAI-Rules-Engine/
│
├── extract.py          # Module 1 — PDF → AI → JSON/Excel rule extractor
├── server.py           # Module 2 — Flask API + rules engine for claim checking
├── app.html            # Web UI — upload documents, view verdict in browser
├── rules.json          # Sample output — 50+ pre-extracted decision rules
├── requirements.txt    # All Python dependencies
├── .env.example        # API key setup template
├── .gitignore
└── README.md

---

## 🚀 Setup

### Prerequisites
- Python 3.9 or higher
- A free [Groq API key](https://console.groq.com) (takes 2 minutes to get)
- The IRDAI Master Circular PDF — download from [irdai.gov.in](https://irdai.gov.in)

### 1. Clone the repo
```bash
git clone https://github.com/jainyo94/IRDAI-Rules-Engine.git
cd IRDAI-Rules-Engine
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your API key

Copy `.env.example` → create a new file called `.env` → paste your key:
GROQ_API_KEY=your_actual_key_here

Then set it in your terminal:

**Windows:**
```cmd
set GROQ_API_KEY=your_actual_key_here
```

**Mac / Linux:**
```bash
export GROQ_API_KEY=your_actual_key_here
```

---

## 📋 Module 1 — Run the Rule Extractor

Converts the IRDAI circular PDF into structured decision rules.

```bash
python extract.py --pdf circular.pdf
```

**Output:**
- `decision_rules.json` — machine-readable rules
- `decision_rules.xlsx` — color-coded Excel workbook with summary dashboard

**Optional arguments:**
--pdf     Path to your PDF          (default: circular.pdf)
--json    Path for JSON output       (default: decision_rules.json)
--xlsx    Path for Excel output      (default: decision_rules.xlsx)

---

## 🌐 Module 2 — Run the Document Intelligence Engine

Upload a policy PDF and a hospital/claim PDF. Get a legally-grounded verdict.

```bash
python server.py
```

Open your browser → `http://localhost:5000`

The engine will:
1. Extract structured facts from both documents using AI
2. Run those facts against the rules database
3. Return a **Pay / Deny / Manual Review** verdict with the specific rule cited

> ⚠️ This tool assists compliance review. It does not constitute legal advice.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| PDF Reading | PyMuPDF (`fitz`) |
| AI Model | Groq API — LLaMA 3.3 70B |
| Web Framework | Flask |
| Data Processing | pandas |
| Excel Generation | openpyxl |
| Frontend | Vanilla HTML / CSS / JS |

---

## 🧠 Design Decisions

**Why Groq instead of OpenAI?**  
Groq's inference speed is 10–20x faster than OpenAI for the same LLaMA model. For processing 6,000-character chunks across a 30,000-character document, this matters.

**Why separate the extractor from the engine?**  
The rules JSON is a stable asset. Once extracted, the Document Engine runs with zero AI calls for rule-matching — only deterministic logic. This keeps costs low and verdicts auditable.

**Why chunking with overlap?**  
The circular is 29,000+ characters. LLMs have context limits. 500-character overlap between chunks ensures rules that span a page boundary are never missed.

---

## 📄 License

MIT — free to use, modify, and build on.  
If you use this in a product, a credit to JurisCode Labs is appreciated.
