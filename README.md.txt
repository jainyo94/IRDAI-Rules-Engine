# JurisCode Labs — Legal Intelligence Engine
### IRDAI Health Insurance Compliance System

**Govt. Recognised MSME | Reg: MP-20-0105989**  
*Applied Legal Data Engineering for Indian Insurance Regulation*

---

## What This Is

JurisCode Labs is an applied R&D organisation that translates 
complex Indian insurance regulations and judicial precedents into 
structured, machine-readable compliance intelligence.

This repository contains the working prototype of our 
**Health Insurance Claim Compliance Engine** — a system that:

1. Extracts structured decision rules from IRDAI circulars automatically
2. Accepts real insurance policy and hospital documents via file upload
3. Extracts legally relevant facts from both documents using AI
4. Checks those facts against a validated judicial rules database
5. Returns a compliance verdict with the exact IRDAI regulatory source

---

## The Problem We Are Solving

IRDAI issued 40+ circulars on health insurance in 2024 alone.
Every new circular creates obligations that compliance teams 
must implement manually — a process that takes weeks and 
produces inconsistent results.

Claims are rejected on legally invalid grounds because the 
compliance system does not know the current regulatory position.

This engine fixes that. Not theoretically — demonstrably.

---

## System Components

| File | Purpose |
|------|---------|
| `extract.py` | Converts IRDAI circular PDFs into structured decision rules |
| `server.py` | Flask backend — accepts document uploads, extracts facts, runs rules engine |
| `app.html` | Browser interface — upload policy + hospital documents, get verdict |
| `rules.json` | Validated rules database — the core IP of JurisCode Labs |

---

## How It Works
User uploads: Policy PDF + Hospital Document PDF
↓
Text extraction (pymupdf)
↓
AI fact extraction (Groq LLaMA-3.3-70B)
Extracts: coverage months, declared conditions,
diagnosis, admission date, portability status
↓
Rules engine checks facts against rules.json
↓
Verdict: Pay / Deny / Review Required
With: exact IRDAI clause, rule applied, confidence level

---

## Current Rules Database

6 validated rules covering Pre-existing Disease disputes:

| Rule ID | Name | Logic |
|---------|------|-------|
| DR-2024-PED-01 | Moratorium 48 Months | IF coverage >= 48 months THEN cannot reject on PED |
| DR-2024-PED-02 | Standard Waiting Period | IF declared AND coverage >= 36 months THEN pay |
| DR-2024-PED-03 | Portability Credit | IF ported THEN credit previous waiting period |
| DR-2024-PED-04 | Non-disclosure Remedy | IF not declared THEN proportionate remedy only |
| DR-2024-PED-05 | Post-inception Diagnosis | IF diagnosed after policy start THEN not PED |
| DR-2024-PED-06 | Specific Disease 24 Month Cap | IF coverage >= 24 months THEN verify specific list |

Source: IRDAI Master Circular on Health Insurance 2024

---

## Setup Instructions

### Requirements
Python 3.10+
pip install pymupdf groq pandas openpyxl flask

### Configuration
1. Get a free Groq API key at console.groq.com
2. Open server.py and replace YOUR_GROQ_API_KEY_HERE with your key
3. Same for extract.py

### Running the Document Analysis System
cd juriscode-directory
python server.py
Open browser: http://localhost:5000

Upload your policy PDF and hospital document. Get compliance verdict.

### Running the Circular Extractor
python extract.py
Place any IRDAI circular as circular.pdf in the same folder.
Outputs: decision_rules.json and decision_rules.xlsx

---

## Regulatory Basis

All rules are sourced from and validated against:
- IRDAI Master Circular on Health Insurance 2024
- IRDAI (Health Insurance) Regulations 2016
- Insurance Act 1938

Legal validation: Yogendra Jain, LL.M. Insurance Law, NUJS Kolkata
PhD Candidate (Insurance Law) | Registered Advocate MP/207/2017

---

## Research Collaboration

JurisCode Labs is actively expanding its validated rules corpus.
We are building structured legal intelligence across all IRDAI
health insurance regulations and appellate judicial precedents.

For research collaboration, internship enquiries, or commercial
discussion: juriscodelabs@gmail.com

---

## Important Notes

- This is a research prototype — not a production compliance system
- Rules are validated but the corpus is not yet comprehensive
- AI extraction accuracy depends on document quality
- Documents are processed locally — only text is sent to Groq for AI extraction

---

*JurisCode Labs | MSME Reg: MP-20-0105989 | juriscodelabs@gmail.com*