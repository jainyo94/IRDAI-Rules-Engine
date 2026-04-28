import fitz
from groq import Groq
import json
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# JURISCODE LABS — IRDAI Decision Rules Extractor
# Converts IRDAI regulatory text into machine-readable decision
# rules that can plug directly into compliance software systems
# ═══════════════════════════════════════════════════════════════

GROQ_API_KEY = "paste_your_groq_key_here"

PDF_PATH     = r"C:\Users\yogendra.jain\Downloads\Juriscode Laboratory\circular.pdf"
OUTPUT_JSON  = r"C:\Users\yogendra.jain\Downloads\Juriscode Laboratory\decision_rules.json"
OUTPUT_XLSX  = r"C:\Users\yogendra.jain\Downloads\Juriscode Laboratory\decision_rules.xlsx"

CHUNK_SIZE   = 6000   # characters per chunk sent to AI
OVERLAP      = 500    # overlap between chunks to avoid missing rules at boundaries


# ── JOB 1: READ AND CHUNK THE PDF ────────────────────────────────────────────
# Why chunking? The circular is 29,000+ characters.
# AI models have limits on how much text they can process at once.
# We split the document into overlapping sections and process each one.
# Overlap ensures rules that span a page break are not missed.

def read_and_chunk(path):
    doc = fitz.open(path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    
    total_chars = len(full_text)
    print(f"✓ PDF read — {total_chars} characters across {len(doc)} pages")
    
    chunks = []
    start = 0
    while start < total_chars:
        end = start + CHUNK_SIZE
        chunks.append(full_text[start:end])
        start += CHUNK_SIZE - OVERLAP
    
    print(f"✓ Split into {len(chunks)} chunks for processing")
    return chunks, full_text


# ── JOB 2: EXTRACT DECISION RULES FROM EACH CHUNK ────────────────────────────
# Why this prompt structure?
# Standard prompts extract obligations as plain text.
# This prompt extracts EXECUTABLE RULES — with the logic operators
# and actions needed for a software system to make decisions automatically.
# This is what makes JurisCode's output different from ChatGPT's output.

def extract_rules_from_chunk(client, chunk, chunk_number, total_chunks):
    print(f"  Processing chunk {chunk_number}/{total_chunks}...")

    prompt = f"""
You are a Legal Data Engineer at JurisCode Labs specializing in converting 
Indian insurance regulations into machine-executable decision rules.

Your task: Read the IRDAI regulatory text below and extract every rule that 
can be expressed as a logical condition with a measurable outcome.

═══════════════════════════════════════════════════════════
EXTRACTION SCHEMA — extract these exact fields for each rule:
═══════════════════════════════════════════════════════════

1. rule_id
   Format: DR-[YEAR]-[NUMBER] e.g. DR-2024-01
   Use DR-2024- prefix. Number sequentially within this chunk starting from {(chunk_number-1)*20 + 1:02d}

2. rule_name
   A short descriptive label (3-6 words) e.g. "Cashless Authorization SLA"

3. rule_category
   Choose ONE: Claim_Settlement | Product_Design | Policyholder_Rights |
   Disclosure | Premium | Grievance_Redressal | TPA_Operations |
   Underwriting | Renewal | Pre_existing_Disease | Moratorium | Fraud

4. data_field_to_check
   The specific measurable variable a system would check.
   Use snake_case. Examples:
   - days_since_claim_filing
   - cashless_approval_time_hours  
   - continuous_coverage_months
   - premium_payment_days_overdue
   - waiting_period_days
   - days_since_policy_receipt
   - ombudsman_award_compliance_days
   IMPORTANT: Must be a real measurable field, not vague text.

5. operator
   The logical comparison. Choose ONE:
   GREATER_THAN | LESS_THAN | EQUAL_TO | 
   GREATER_THAN_OR_EQUAL | LESS_THAN_OR_EQUAL | NOT_EQUAL_TO

6. target_value
   The numeric threshold. Numbers only. No units. No text.
   Examples: 30, 1, 60, 3, 15

7. target_unit
   The unit of the value. Examples: days, hours, months, years, 
   percentage, rupees, minutes. Write "none" if no unit applies.

8. action
   What the system must DO when the condition is triggered.
   Use CAPS_SNAKE_CASE. Be specific. Examples:
   - FLAG_SLA_VIOLATION
   - APPLY_PENALTY_5000_PER_DAY
   - BYPASS_NONDISCLOSURE_REJECTION
   - ALLOW_FREE_CANCELLATION
   - SHIFT_COST_TO_INSURER_FUND
   - MANDATE_CLAIM_APPROVAL
   - TRIGGER_GRIEVANCE_ESCALATION
   - BLOCK_POLICY_REJECTION

9. obligated_party
   WHO must take the action. Choose ONE:
   Insurer | TPA | Policyholder | IRDAI | Ombudsman | Agent | Broker | PMC

10. penalty_detail
    Exact penalty if rule is violated. Include amount if specified.
    Examples: "Rs. 5000 per day payable to complainant"
    Write "Not specified" only if truly absent.

11. regulatory_clause
    Copy the EXACT sentence(s) from the text that this rule is based on.
    Include the clause/section number if visible in the text.
    This is the legal source — must be verbatim from the document.

12. plain_english_explanation
    One sentence explaining this rule in simple language a non-lawyer understands.

═══════════════════════════════════════════════════════════
CRITICAL INSTRUCTIONS:
═══════════════════════════════════════════════════════════
- Only extract rules with a MEASURABLE NUMERIC threshold
- Skip vague obligations with no numeric value (e.g. "insurers shall be fair")
- Every "shall within X days/hours/months" is a rule — extract it
- Every penalty with a rupee amount or timeframe is a rule — extract it
- If a rule has TWO thresholds (e.g. "within 1 hour, final within 3 hours") 
  create TWO separate rules
- Return ONLY valid JSON array. No markdown. No explanation.
- Start with [ and end with ]
- If no qualifying rules exist in this chunk, return empty array: []

REGULATORY TEXT:
{chunk}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=4000
    )
    return response.choices[0].message.content


# ── JOB 3: PARSE AND DEDUPLICATE RESULTS ─────────────────────────────────────
# Why deduplication?
# Because chunks overlap, the same rule may appear in two chunks.
# We remove duplicates by comparing rule text similarity.

def parse_and_deduplicate(raw_results):
    all_rules = []
    seen_clauses = set()
    
    for raw in raw_results:
        clean = raw.strip()
        
        # Remove markdown code fences if present
        if "```" in clean:
            parts = clean.split("```")
            for part in parts:
                if part.startswith("json"):
                    clean = part[4:].strip()
                    break
                elif "[" in part:
                    clean = part.strip()
                    break
        
        # Extract JSON array
        start = clean.find("[")
        end = clean.rfind("]") + 1
        if start == -1 or end == 0:
            continue
            
        clean = clean[start:end]
        
        try:
            rules = json.loads(clean)
            for rule in rules:
                # Deduplicate based on regulatory clause text
                clause_key = str(rule.get("regulatory_clause", ""))[:100]
                if clause_key not in seen_clauses and clause_key.strip():
                    seen_clauses.add(clause_key)
                    all_rules.append(rule)
        except json.JSONDecodeError:
            continue
    
    # Renumber rule IDs sequentially
    for i, rule in enumerate(all_rules, 1):
        rule["rule_id"] = f"DR-2024-{i:02d}"
    
    return all_rules


# ── JOB 4: SAVE AS PROFESSIONAL XLSX ─────────────────────────────────────────
# Why Excel and not just CSV?
# A compliance officer at an insurer works in Excel.
# A professional formatted workbook with color coding signals
# that this is a serious product, not a student project.

def save_xlsx(rules, path):
    wb = Workbook()
    
    # ── Sheet 1: Decision Rules (Main) ──
    ws1 = wb.active
    ws1.title = "Decision Rules"
    
    headers = [
        "Rule ID", "Rule Name", "Category", "Data Field to Check",
        "Operator", "Target Value", "Unit", "Action",
        "Obligated Party", "Penalty Detail",
        "Plain English Explanation", "Regulatory Clause"
    ]
    
    field_map = [
        "rule_id", "rule_name", "rule_category", "data_field_to_check",
        "operator", "target_value", "target_unit", "action",
        "obligated_party", "penalty_detail",
        "plain_english_explanation", "regulatory_clause"
    ]
    
    # Header style
    header_fill   = PatternFill("solid", start_color="1F3864")
    header_font   = Font(bold=True, color="FFFFFF", name="Arial", size=10)
    center_align  = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align    = Alignment(horizontal="left",   vertical="center", wrap_text=True)
    
    # Category color coding — helps compliance teams filter visually
    category_colors = {
        "Claim_Settlement":    "FFF2CC",
        "Policyholder_Rights": "E2EFDA",
        "TPA_Operations":      "DDEBF7",
        "Grievance_Redressal": "FCE4D6",
        "Product_Design":      "EAD1DC",
        "Premium":             "D9EAD3",
        "Moratorium":          "CFE2F3",
        "Fraud":               "F4CCCC",
        "Disclosure":          "FFF3E0",
        "Underwriting":        "F3E5F5",
    }
    
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"),  bottom=Side(style="thin")
    )
    
    # Write headers
    for col, header in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col, value=header)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = center_align
        cell.border    = thin_border
    ws1.row_dimensions[1].height = 30
    
    # Write data rows
    for row_idx, rule in enumerate(rules, 2):
        category = rule.get("rule_category", "")
        row_color = category_colors.get(category, "FFFFFF")
        row_fill  = PatternFill("solid", start_color=row_color)
        
        for col_idx, field in enumerate(field_map, 1):
            value = rule.get(field, "")
            cell  = ws1.cell(row=row_idx, column=col_idx, value=str(value))
            cell.fill      = row_fill
            cell.border    = thin_border
            cell.font      = Font(name="Arial", size=9)
            cell.alignment = left_align if col_idx > 3 else center_align
        
        ws1.row_dimensions[row_idx].height = 45
    
    # Column widths
    col_widths = [12, 28, 20, 30, 22, 14, 10, 32, 18, 30, 45, 60]
    for col_idx, width in enumerate(col_widths, 1):
        ws1.column_dimensions[get_column_letter(col_idx)].width = width
    
    ws1.freeze_panes = "A2"
    ws1.auto_filter.ref = f"A1:{get_column_letter(len(headers))}1"
    
    # ── Sheet 2: Summary Dashboard ──
    ws2 = wb.create_sheet("Summary")
    ws2["A1"] = "JURISCODE LABS — IRDAI Decision Rules Summary"
    ws2["A1"].font = Font(bold=True, size=14, name="Arial", color="1F3864")
    
    ws2["A3"] = "Generated:"
    ws2["B3"] = datetime.now().strftime("%d %B %Y, %H:%M")
    ws2["A4"] = "Total Rules Extracted:"
    ws2["B4"] = len(rules)
    ws2["A5"] = "Source Document:"
    ws2["B5"] = PDF_PATH.split("\\")[-1]
    
    ws2["A3"].font = ws2["A4"].font = ws2["A5"].font = Font(bold=True, name="Arial", size=10)
    ws2["B3"].font = ws2["B4"].font = ws2["B5"].font = Font(name="Arial", size=10)
    
    # Category breakdown
    ws2["A7"] = "Rules by Category"
    ws2["A7"].font = Font(bold=True, size=11, name="Arial", color="1F3864")
    
    df = pd.DataFrame(rules)
    if "rule_category" in df.columns:
        category_counts = df["rule_category"].value_counts()
        ws2["A8"]  = "Category"
        ws2["B8"]  = "Count"
        ws2["A8"].font = ws2["B8"].font = Font(bold=True, name="Arial")
        
        for i, (cat, count) in enumerate(category_counts.items(), 9):
            ws2[f"A{i}"] = cat
            ws2[f"B{i}"] = count
            ws2[f"A{i}"].font = ws2[f"B{i}"].font = Font(name="Arial", size=10)
    
    # Party breakdown
    start_row = 9 + len(category_counts) + 2
    ws2[f"A{start_row}"] = "Rules by Obligated Party"
    ws2[f"A{start_row}"].font = Font(bold=True, size=11, name="Arial", color="1F3864")
    
    if "obligated_party" in df.columns:
        party_counts = df["obligated_party"].value_counts()
        ws2[f"A{start_row+1}"] = "Party"
        ws2[f"B{start_row+1}"] = "Count"
        for i, (party, count) in enumerate(party_counts.items(), start_row+2):
            ws2[f"A{i}"] = party
            ws2[f"B{i}"] = count
            ws2[f"A{i}"].font = ws2[f"B{i}"].font = Font(name="Arial", size=10)
    
    ws2.column_dimensions["A"].width = 35
    ws2.column_dimensions["B"].width = 15
    
    wb.save(path)
    print(f"✓ Professional Excel saved — {len(rules)} rules, 2 sheets")


# ── MAIN: RUN ALL JOBS IN SEQUENCE ───────────────────────────────────────────
if __name__ == "__main__":
    print("\nJurisCode Labs — IRDAI Decision Rules Extractor")
    print("=" * 50)
    print("Converting regulatory text → machine-readable rules")
    print("=" * 50 + "\n")
    
    # Job 1: Read and chunk PDF
    chunks, full_text = read_and_chunk(PDF_PATH)
    
    # Job 2: Extract rules from each chunk
    client = Groq(api_key=GROQ_API_KEY)
    raw_results = []
    print(f"\nExtracting decision rules from {len(chunks)} chunks:")
    
    for i, chunk in enumerate(chunks, 1):
        raw = extract_rules_from_chunk(client, chunk, i, len(chunks))
        raw_results.append(raw)
    
    # Job 3: Parse, combine, deduplicate
    print("\nParsing and deduplicating results...")
    rules = parse_and_deduplicate(raw_results)
    print(f"✓ {len(rules)} unique decision rules extracted")
    
    # Job 4: Save outputs
    print("\nSaving outputs...")
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
    print(f"✓ JSON saved → decision_rules.json")
    
    save_xlsx(rules, OUTPUT_XLSX)
    
    # Preview
    print("\n── PREVIEW (first 3 rules) ──────────────────────────────")
    for rule in rules[:3]:
        print(f"\n{rule.get('rule_id')}: {rule.get('rule_name')}")
        print(f"   IF   {rule.get('data_field_to_check')} "
              f"{rule.get('operator')} {rule.get('target_value')} "
              f"{rule.get('target_unit')}")
        print(f"   THEN {rule.get('action')}")
        print(f"   WHO  {rule.get('obligated_party')}")
        print(f"   WHY  {rule.get('regulatory_clause', '')[:80]}...")
    
    print(f"\n✓ Complete. Open decision_rules.xlsx in Excel.")
    print(f"  JurisCode Labs | {datetime.now().strftime('%d %B %Y')}")
