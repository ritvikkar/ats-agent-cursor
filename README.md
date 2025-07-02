# ATS Detection Agent

## 🎯 Overview
An **AI agent** that identifies which **Applicant Tracking System (ATS)** a company uses by analyzing public job postings.

- **Input:** A list of company names
- **Output:** Structured JSON data per company

---

## ✅ Objectives
- Determine if company is a **staffing agency**
- Locate and validate **career page URL**
- Extract up to **3 job posting URLs**
- Extract **final apply links**
- Infer **ATS type**
- Provide **confidence level**

---

## 🔁 Step-by-Step Logic
1. **Search for Career Page**
   - Uses Bing/SerpAPI to find a company-owned careers page
2. **Detect Staffing Agency**
   - Scrapes for keywords (e.g., "hire for clients", "recruitment services")
   - Returns: `"Yes"`, `"No"`, or `"Unsure"`
3. **Extract Job Postings**
   - Visits career page, extracts up to 3 job URLs
   - Skips aggregators (LinkedIn, Indeed, etc.)
4. **Extract Apply Links**
   - For each job URL, finds and follows "Apply" links/buttons
   - Captures final apply URL
5. **Determine ATS**
   - Matches apply URLs to known ATS regex patterns (see `ats_patterns.py`)
6. **Determine Confidence**
   - 3/3 same ATS → `"high"`
   - 2/3 same → `"medium"`
   - Otherwise → `"uncertain"`

---

## 🧾 JSON Output Format
**Non-staffing company:**
```json
{
  "company": "Example Inc",
  "is_staffing": "No",
  "career_page": "https://example.com/careers",
  "job_links": [
    { "job_url": "...", "apply_url": "...", "ats": "Workday" },
    { "job_url": "...", "apply_url": "...", "ats": "Workday" },
    { "job_url": "...", "apply_url": "...", "ats": "Workday" }
  ],
  "final_ats": "Workday",
  "certainty": "high"
}
```
**Staffing agency:**
```json
{
  "company": "StaffingCo",
  "is_staffing": "Yes",
  "career_page": "https://staffingco.com/careers",
  "job_links": [],
  "apply_links": [],
  "ats": null,
  "certainty": "none"
}
```

---

## 🧱 Key Project Files
- `PRD.md` – Product requirements
- `src/ats_agent/main.py` – Orchestrates the workflow
- `src/ats_agent/search.py` – Career page search logic
- `src/ats_agent/extract.py` – Job and apply link extraction
- `src/ats_agent/ats_patterns.py` – Regex patterns for ATS detection
- `src/ats_agent/utils.py` – Helper functions
- `src/ats_agent/config.py` – API keys, constants, regex list

---

## 🚀 Setup & Usage
1. **Clone the repo:**
   ```bash
   git clone https://github.com/ritvikkar/ats-agent-cursor.git
   cd ats-agent-cursor
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # Or use uv: uv pip install -r requirements.txt
   ```
3. **Set up environment variables:**
   - Copy `.env.example` to `.env` and add your API keys (OpenAI, SerpAPI, etc.)
4. **Run the agent:**
   ```bash
   PYTHONPATH=src python3 -m ats_agent.main
   ```
5. **Run tests:**
   ```bash
   pytest
   ```

---

## 📝 Notes
- **Never commit your `.env` file or secrets.**
- See `PRD.md` for full requirements and logic.
- For questions or contributions, open an issue or PR on [GitHub](https://github.com/ritvikkar/ats-agent-cursor). 