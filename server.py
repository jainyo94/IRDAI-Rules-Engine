from flask import Flask, request, jsonify, send_from_directory
import fitz
from groq import Groq
import json
import os
import re

# ══════════════════════════════════════════════════════════════════
# JURISCODE LABS — Document Intelligence Engine
# Accepts policy + hospital documents, extracts facts,
# checks against validated rules database, returns verdict
# ══════════════════════════════════════════════════════════════════

app = Flask(__name__, static_folder='.')

GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"  # Add your key here
RULES_FILE   = "rules.json"
FOLDER       = r"C:\Users\yogendra.jain\Downloads\Juriscode Laboratory"

# ── LOAD RULES DATABASE ───────────────────────────────────────────
# Rules are loaded from your JSON file — your protected asset
# Any update to rules.json is immediately reflected without
# changing any code. This separation is intentional.

def load_rules():
    rules_path = os.path.join(FOLDER, RULES_FILE)
    with open(rules_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['rules'], data['metadata']

# ── STEP 1: EXTRACT TEXT FROM PDF ────────────────────────────────
# Same pymupdf approach we already know works

def extract_text_from_pdf(file_storage):
    pdf_bytes = file_storage.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# ── STEP 2: EXTRACT STRUCTURED FACTS USING GROQ ──────────────────
# This is the intelligent extraction layer.
# We send both documents to Groq with very specific instructions
# about exactly what fields to find and how to classify them.
# The field names match our rules database exactly — this mapping
# is JurisCode's proprietary taxonomy.

def extract_facts(policy_text, hospital_text):
    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""
You are a legal data extraction specialist at JurisCode Labs,
expert in Indian health insurance regulations and IRDAI framework.

You have been given two documents:
1. An insurance policy document
2. A hospital/medical document (discharge summary, claim form, or diagnostic report)

Your task: Extract ONLY the specific facts listed below.
Be precise. Extract what is actually written — do not infer or assume.
If a fact is not clearly stated, use "not_found".

EXTRACT THESE EXACT FIELDS:

From the POLICY DOCUMENT:
- policy_number: the policy identification number
- policy_holder_name: full name of insured person
- policy_start_date: inception date (format: YYYY-MM-DD if possible)
- policy_end_date: expiry date
- insurer_name: name of insurance company
- sum_insured: coverage amount in rupees
- policy_ported: was this policy ported from another insurer? (yes/no/not_found)
- previous_insurer: name of previous insurer if ported
- continuous_coverage_months: total months of continuous coverage including previous policies (number only)
- conditions_declared: list any pre-existing conditions declared in proposal form
- waiting_period_clause: exact text of waiting period clause if present
- exclusions_listed: list of conditions or treatments excluded
- policy_type: individual/family floater/group

From the HOSPITAL DOCUMENT:
- patient_name: full name of patient
- admission_date: date of admission (YYYY-MM-DD if possible)
- discharge_date: date of discharge
- hospital_name: name of treating hospital
- primary_diagnosis: main diagnosis or condition being treated
- secondary_diagnosis: any additional diagnoses
- treatment_description: brief description of treatment given
- doctor_name: treating doctor name
- condition_diagnosed_when: based on medical history in document, was this condition known/diagnosed BEFORE the policy start date? (before_policy/after_policy/unknown)
- claimed_amount: amount being claimed

CLASSIFICATION FIELDS (you must determine these):
- condition_declared: was the primary diagnosis condition declared in the policy proposal? (yes/no/unknown)
- is_pre_existing: based on documents, is the condition likely pre-existing? (yes/no/unknown)
- rejection_reason: if the document mentions rejection or query, what reason is given? 
  (ped/waiting_period/non_disclosure/exclusion/none/other)

IMPORTANT RULES:
- Return ONLY valid JSON object
- No explanation, no markdown, no preamble
- Start with {{ and end with }}
- Use exact field names above
- For dates use YYYY-MM-DD format
- For yes/no fields use only: yes, no, not_found
- Numbers as integers not strings

POLICY DOCUMENT TEXT:
{policy_text[:6000]}

HOSPITAL DOCUMENT TEXT:
{hospital_text[:4000]}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=2000
    )

    raw = response.choices[0].message.content.strip()

    # Clean JSON
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            if "{" in part:
                raw = part.replace("json", "").strip()
                break

    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > 0:
        raw = raw[start:end]

    return json.loads(raw)

# ── STEP 3: CALCULATE COVERAGE MONTHS ────────────────────────────
# If coverage months not found in document, calculate from dates

def calculate_coverage_months(facts):
    months = facts.get('continuous_coverage_months')

    # Already a valid number
    if isinstance(months, int) and months > 0:
        return months

    # Try to calculate from dates
    try:
        from datetime import datetime
        policy_start  = facts.get('policy_start_date', '')
        admission_date = facts.get('admission_date', '')

        if policy_start and admission_date and policy_start != 'not_found':
            start = datetime.strptime(policy_start[:10], '%Y-%m-%d')
            admit = datetime.strptime(admission_date[:10], '%Y-%m-%d')
            delta = (admit - start).days
            return max(0, int(delta / 30.44))
    except:
        pass

    return 0

# ── STEP 4: RUN RULES ENGINE ──────────────────────────────────────
# This is the core of JurisCode's value.
# Rules are loaded from your JSON database.
# Each rule is checked against extracted facts.
# Priority determines which rule takes precedence.
# This engine is entirely yours — no AI involved at this step.

def run_rules_engine(facts, rules):
    applied_rules  = []
    final_verdict  = None
    final_action   = None
    final_message  = ""
    confidence     = "HIGH"

    # Sort rules by priority (lower number = higher priority)
    sorted_rules = sorted(rules, key=lambda r: r.get('priority', 99))

    for rule in sorted_rules:
        if final_verdict in ['pay', 'deny']:
            # Already have a definitive verdict — only higher priority overrides
            if rule.get('priority', 99) >= (applied_rules[0].get('priority', 99) if applied_rules else 99):
                continue

        field    = rule['field']
        operator = rule['operator']
        value    = rule['value']
        fact_val = facts.get(field)

        # Primary condition check
        primary_match = evaluate_condition(fact_val, operator, value)

        if not primary_match:
            continue

        # Secondary condition check if exists
        secondary = rule.get('secondary_condition')
        if secondary:
            sec_field = secondary['field']
            sec_op    = secondary['operator']
            sec_val   = secondary['value']
            sec_fact  = facts.get(sec_field)
            if not evaluate_condition(sec_fact, sec_op, sec_val):
                continue

        # Rule matched
        applied_rules.insert(0, rule)
        final_verdict = rule['verdict']
        final_action  = rule['action']
        final_message = build_message(rule, facts)

        # Pay verdicts from priority 1 are definitive
        if rule.get('priority') == 1 and final_verdict == 'pay':
            break

    # No rule matched
    if not applied_rules:
        final_verdict = 'amber'
        final_action  = 'MANUAL_REVIEW_REQUIRED'
        final_message = 'No specific rule matched the extracted facts. Manual review by compliance officer required.'
        confidence    = 'LOW'

    # Check for missing critical facts
    critical_fields = ['continuous_coverage_months', 'condition_declared',
                       'condition_diagnosed_when', 'primary_diagnosis']
    missing = [f for f in critical_fields
               if not facts.get(f) or facts.get(f) == 'not_found']

    if missing:
        confidence = 'MEDIUM' if len(missing) <= 2 else 'LOW'

    return {
        'verdict':       final_verdict,
        'action':        final_action,
        'message':       final_message,
        'applied_rules': applied_rules,
        'confidence':    confidence,
        'missing_fields': missing
    }

def evaluate_condition(fact_value, operator, rule_value):
    if fact_value is None or fact_value == 'not_found':
        return False
    try:
        if operator == '>=':
            return float(fact_value) >= float(rule_value)
        elif operator == '<=':
            return float(fact_value) <= float(rule_value)
        elif operator == '>':
            return float(fact_value) > float(rule_value)
        elif operator == '<':
            return float(fact_value) < float(rule_value)
        elif operator == '==':
            return str(fact_value).lower().strip() == str(rule_value).lower().strip()
        elif operator == '!=':
            return str(fact_value).lower().strip() != str(rule_value).lower().strip()
    except:
        return str(fact_value).lower().strip() == str(rule_value).lower().strip()
    return False

def build_message(rule, facts):
    verdict_messages = {
        'pay':   f"Claim must be accepted under {rule['id']}",
        'deny':  f"Claim may be declined under {rule['id']}",
        'amber': f"Further review required — {rule['name']}"
    }
    return verdict_messages.get(rule['verdict'], rule['name'])

# ── FLASK ROUTES ──────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(FOLDER, 'app.html')

@app.route('/check', methods=['POST'])
def check_claim():
    try:
        # Get uploaded files
        policy_file   = request.files.get('policy_doc')
        hospital_file = request.files.get('hospital_doc')

        if not policy_file or not hospital_file:
            return jsonify({'error': 'Both policy document and hospital document are required'}), 400

        # Step 1: Extract text from both PDFs
        policy_text   = extract_text_from_pdf(policy_file)
        hospital_text = extract_text_from_pdf(hospital_file)

        if len(policy_text) < 100:
            return jsonify({'error': 'Could not extract text from policy document. Please ensure it is a text-based PDF.'}), 400

        # Step 2: Extract structured facts using Groq
        facts = extract_facts(policy_text, hospital_text)

        # Step 3: Calculate coverage months if needed
        facts['continuous_coverage_months'] = calculate_coverage_months(facts)

        # Step 4: Load rules and run engine
        rules, metadata = load_rules()
        result = run_rules_engine(facts, rules)

        # Return complete response
        return jsonify({
            'success':  True,
            'facts':    facts,
            'result':   result,
            'metadata': metadata
        })

    except json.JSONDecodeError:
        return jsonify({'error': 'AI could not parse document structure. Please try with a clearer PDF.'}), 500
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

if __name__ == '__main__':
    print("\nJurisCode Labs — Document Intelligence Engine")
    print("=" * 45)
    print("Server starting at http://localhost:5000")
    print("Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000)