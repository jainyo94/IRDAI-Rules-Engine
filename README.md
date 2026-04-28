# ⚖️ IRDAI-Rules-Engine: Regulatory Logic Extraction

## 🤝 Contact & Collaboration

This project is an evolving initiative. Whether you are building an InsurTech platform, researching computational law, or exploring regulatory automation, I would love to connect.

* **Developer & Legal Architect:** Yogendra Jain, Founder & CEO Juriscode Labs
* **LinkedIn:** JurisCode Labs- https://www.linkedin.com/company/juriscode-labs/ 
                Yogendra Jain- https://www.linkedin.com/in/theyogendr/
* **Email:** juriscodelabs@gmail.com & jainyo94@gmail.com 
* **Organization:** Juriscode Labs (Reg. MSME/Govt. of India)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status: Active](https://img.shields.io/badge/Status-Active_Development-success.svg)]()

**An Open-Source Initiative by [Juriscode Labs](https://github.com/jainyo94)** *Translating Indian Insurance Law into Machine-Readable Architecture.*

---

## 🚀 The Vision

The **IRDAI Master Circular on Health Insurance (2024)** is a 17-page foundational document governing the Indian health insurance sector. In its raw PDF format, it creates a massive "compliance bottleneck" for InsurTech platforms, TPA systems, and RegTech developers.

This repository serves as a **computational bridge**. We have successfully extracted and converted the complex, unstructured legal obligations of the Master Circular into an executable **JSON Rules Engine**. By transforming legal text into deterministic "If-Then-Else" logic, this project enables:

- 🛡️ **Automated Compliance:** System-level enforcement of regulatory deadlines.
- ⚡ **Real-Time Auditing:** Immediate flagging of violations in claim settlement workflows.
- 📊 **Risk Scoring:** Algorithmic assessment of litigation and regulatory risk.

---

## 🔬 Methodology: Expert-Driven RLHF

Unlike standard generative AI outputs, this engine is built on a foundation of strict academic and legal rigor. The extraction pipeline utilizes a specialized **Reinforcement Learning from Human Feedback (RLHF)** protocol:

1. **AI Parsing:** Initial logic mapping via Llama-3/Groq, utilizing chunked processing to handle dense regulatory text.
2. **Academic Verification:** Every rule is audited by legal academia, anchored in specialized doctoral-level insurance law research to ensure absolute fidelity to the *Insurance Act, 1938* and IRDAI regulations. 
3. **Continuous Integration:** As regulatory frameworks evolve, this logic is updated to maintain a definitive "Golden Record" for the industry.

---

## 📂 Repository Architecture

| Component | File | Description |
| :--- | :--- | :--- |
| **Logic Pipeline** | `extract.py` | The Python script utilizing `fitz` and `groq` to parse, chunk, and extract Boolean logic from the source PDF. |
| **Rules Engine** | `decision_rules.json` | The core executable dataset mapping `rule_id`, `operator`, and `target_value` for developer integration. |
| **Business Logic** | `decision_rules.xlsx` | A structured, human-readable compliance matrix for legal officers and risk managers. |
| **Source Data** | `circular.pdf` | The official IRDAI gazette document serving as the ground truth. |

---

## 💻 Developer Integration

The engine isolates **Boolean Logic** and **Numerical Thresholds** from the regulatory prose. Developers can inject this JSON directly into their backend systems.

<details>
<summary><b>Click to view a sample of the JSON structure (Rule DR-2024-02)</b></summary>

```json
[
  {
    "rule_id": "DR-2024-02",
    "rule_name": "Free Look Period",
    "rule_category": "Policyholder_Rights",
    "data_field_to_check": "days_since_policy_receipt",
    "operator": "LESS_THAN_OR_EQUAL",
    "target_value": "30",
    "target_unit": "days",
    "action": "ALLOW_FREE_CANCELLATION",
    "obligated_party": "Insurer",
    "plain_english_explanation": "Policyholders have 30 days to review and cancel their policy after receiving the policy document."
  }
]
