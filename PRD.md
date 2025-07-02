# **ATS Detection Agent — Product Requirements Document (PRD)**

## **🎯 Overview**

We are building an **AI agent** that identifies which **Applicant Tracking System (ATS)** a company uses by analyzing public job postings.  
 **Input**: a list of company names  
 **Output**: structured JSON data per company

---

## **✅ Objectives**

* Determine if company is a **staffing agency**

* Locate and validate **career page URL**

* Extract up to **3 job posting URLs**

* Extract **final apply links**

* Infer **ATS type**

* Provide **confidence level**

---

## **🔁 Step-by-Step Logic**

### **1\. Search for Career Page**

* Query: `{{company_name}} careers site:.com` (via Bing or SerpAPI)

* Must return a **company-owned domain**

* Page must include or link to job listings

### **2\. Detect Staffing Agency**

* Scrape website for keywords:

  * "hire for clients", "recruitment services"

* Return either `"Yes"`, `"No"`, or `"Unsure"` for `"is_staffing"`

### **3\. Extract Job Postings**

* Visit career page

* Extract up to 3 job URLs

* Skip pages hosted on aggregators like LinkedIn, Indeed, etc.

### **4\. Extract Apply Links**

* For each job URL:

  * Find “Apply” button or link

  * Follow redirects and capture final URL

### **5\. Determine ATS**

Match apply URLs using regex patterns:

| ATS System | Regex Pattern |
| ----- | ----- |
| SAP SuccessFactors | `career\d+\.successfactors\.com` |
| SAP SuccessFactors (Cloud) | `[^\/]+\.jobs\.hr\.cloud\.sap` |
| Workday | `\.myworkdayjobs\.com` |
| Bullhorn | (no fixed pattern) |
| iCIMS | `\.icims\.com\/jobs\/` |
| Greenhouse | `boards\.greenhouse\.io` or `job-boards\.greenhouse\.io` |
| Cornerstone OnDemand (CSOD) | `\.csod\.com\/ats\/careersite\/` |
| Oracle Taleo Enterprise | `\.taleo\.net\/careersection\/` |
| Avature | `\.avature\.net\/` |
| Workable | `apply\.workable\.com\/` |
| Oracle Recruiting Cloud (ORC) | `\.oraclecloud\.com\/hcmUI\/CandidateExperience\/` |
| Lever | `jobs\.lever\.co\/` |
| SmartRecruiters | `jobs\.smartrecruiters\.com\/` |
| Teamtailor | `[^\/]+\.teamtailor\.com\/` |
| JazzHR | `\.applytojob\.com\/apply\/` |
| Recruitee | `\.recruitee\.com\/` |
| Talemetry | `jobs\.talemetry\.com\/` |
| JobAdder | `apply\.jobadder\.com\/` |
| JobDiva | `www1\.jobdiva\.com\/` |
| Jobvite | `jobs\.jobvite\.com\/` |
| Gupy | `\.gupy\.io\/jobs\/` |

### **6\. Determine Confidence**

* 3/3 same ATS → `"high"`

* 2/3 same → `"medium"`

* Otherwise → `"uncertain"`

---

## **🧾 JSON Output Formats**

**For a non-staffing company:**

json  
CopyEdit  
`{`  
  `"company": "Example Inc",`  
  `"is_staffing": "No",`  
  `"career_page": "https://example.com/careers",`  
  `"job_links": [`  
    `{ "job_url": "...", "apply_url": "...", "ats": "Workday" },`  
    `{ "job_url": "...", "apply_url": "...", "ats": "Workday" },`  
    `{ "job_url": "...", "apply_url": "...", "ats": "Workday" }`  
  `],`  
  `"final_ats": "Workday",`  
  `"certainty": "high"`  
`}`

**For a staffing agency:**

json  
CopyEdit  
`{`  
  `"company": "StaffingCo",`  
  `"is_staffing": "Yes",`  
  `"career_page": "https://staffingco.com/careers",`  
  `"job_links": [],`  
  `"apply_links": [],`  
  `"ats": null,`  
  `"certainty": "none"`  
`}`

---

## **🧱 Key Project Files**

* `PRD.md` – this document

* `main.py` – orchestrates the full workflow

* `search.py` – handles career page search logic

* `extract.py` – extracts job and apply links

* `ats_patterns.py` – defines regex patterns for ATS detection

* `utils.py` – helper functions (HTTP requests, deduping links, etc.)

* `config.py` – house API keys, constants, regex list

