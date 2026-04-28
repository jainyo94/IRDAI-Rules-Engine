# ⚖️ IRDAI-Rules-Engine: Regulatory Logic Extraction

**An Open-Source Project by [Juriscode Labs]([https://github.com/YourUsername](https://github.com/jainyo94))** *Bridging the gap between Indian Insurance Law and Executable Code.*

---

## 🚀 Overview
The **IRDAI Master Circular on Health Insurance (2024)** is a foundational document for the Indian insurance sector. However, unstructured PDFs often create a "compliance bottleneck" for InsurTech and RegTech developers.

This repository provides a **computational bridge**, converting 17+ pages of regulatory text into machine-readable **JSON** and **CSV** Rules Engines. We transform legal obligations into "If-Then-Else" logic, enabling:
* **Automated Compliance Monitoring**
* **Claim Settlement Validation**
* **Real-time Regulatory Auditing**

---

## 🛡️ Expert Verification & RLHF
Unlike standard AI-generated outputs, this dataset undergoes a rigorous **RLHF (Reinforcement Learning from Human Feedback)** pipeline to ensure legal integrity:

1.  **AI Extraction:** Initial logic mapping performed via specialized LLM pipelines (Llama-3/Groq).
2.  **Expert Audit:** Every rule is reviewed and corrected by an **Assistant Professor of Law & Insurance Law Expert** to ensure the machine logic aligns with the *Insurance Act, 1938*.
3.  **Ongoing Development:** This is a living repository. As the regulatory landscape shifts, the logic is updated to maintain a "Golden Record" of insurance compliance.

---

## 📂 Project Structure

| File | Description |
| :--- | :--- |
| `extract.py` | The Python pipeline used to parse and structure the PDF data. |
| `decision_rules.json` | The core executable engine for developer integration. |
| `decision_rules.xlsx` | A human-readable summary for compliance officers and legal teams. |
| `circular.pdf` | The original source document for reference. |

---

## 💡 Use Cases
* **For Developers:** Plug the `decision_rules.json` directly into claim processing software to automate "Free Look" or "Grace Period" validations.
* **For Legal Teams:** Use the CSV/Excel output to conduct gap analysis on existing insurance products.
* **For Founders:** Build automated risk-scoring tools for the Indian market.

---

## 🛠️ Technical Implementation
The engine focuses on **Boolean Logic** and **Numerical Thresholds**. 

**Example Logic Mapping:**
```json
{
  "rule_id": "DR-2024-02",
  "rule_name": "Free Look Period",
  "data_field_to_check": "days_since_policy_receipt",
  "operator": "LESS_THAN_OR_EQUAL",
  "target_value": "30",
  "action": "ALLOW_FREE_CANCELLATION"
}
