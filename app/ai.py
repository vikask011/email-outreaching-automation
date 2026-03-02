import requests
import json
import re
from pypdf import PdfReader
from app.config import SARVAM_API_KEY

SARVAM_URL = "https://api.sarvam.ai/v1/chat/completions"
RESUME_PATH = "resumes/resume.pdf"


# -------------------------------------------------------
# Extract Text From Resume PDF
# -------------------------------------------------------
def extract_resume_text():
    try:
        reader = PdfReader(RESUME_PATH)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"

        text = re.sub(r"\s+", " ", text)

        if not text.strip():
            raise Exception("Resume content empty.")

        return text[:4000]

    except Exception as e:
        raise Exception(f"Failed to read resume PDF: {str(e)}")


# -------------------------------------------------------
# Extract Company Name
# -------------------------------------------------------
def extract_company_name(text: str):
    patterns = [
        r"\bat\s+([A-Z][A-Za-z0-9&\-\s]{2,40}?)(?:\s+for|\s+as|\s+–|\s+-|,|\.|$)",
        r"\bfor\s+([A-Z][A-Za-z0-9&\-\s]{2,40}?)(?:\s+as|\s+–|\s+-|,|\.|$)",
        r"\bcompany[:\s]+([A-Z][A-Za-z0-9&\-\s]{2,40}?)(?:,|\.|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1).strip()
            generic = {"the", "a", "an", "this", "their", "our", "your", "my"}
            if candidate.lower().split()[0] not in generic:
                return candidate
    return None


# -------------------------------------------------------
# Prompt Builder
# -------------------------------------------------------
def build_prompt(user_instruction: str, recipient_name: str = "", email_style: str = "targeted"):
    company_name = extract_company_name(user_instruction)
    resume_text = extract_resume_text()

    style_instructions = {
        "targeted": (
            "Targeted application for a specific role. "
            "Show you understand what the role actually requires day-to-day, "
            "then connect 1-2 things you've done that are directly relevant. "
            "Do not summarize your whole background."
        ),
        "cold": (
            "Cold outreach — no specific open role. "
            "Keep it short and respectful. One line on what kind of work you do, "
            "one line on why you're reaching out to them specifically if possible. "
            "Low pressure, no pitch."
        ),
        "referral": (
            "Referral or inquiry email. "
            "Warm, direct. One line on background, one on what you're looking for. "
            "Ask for a direction or introduction, not a job."
        ),
    }

    greeting = f"Dear {recipient_name}," if recipient_name.strip() else "Dear Hiring Manager,"
    company_line = (
        f"The company is: {company_name}. If it naturally fits, reference it — but only if it sounds genuine."
        if company_name
        else "Company not mentioned. Do not invent or guess one."
    )

    return f"""
You are ghostwriting a cold outreach email for a software engineer.

The reader is a senior developer, engineering manager, or HR professional.
They receive dozens of these emails. What stands out is NOT a list of achievements —
it is clarity, relevance, and the sense that the person knows what they are doing.

STYLE: {style_instructions.get(email_style, style_instructions["targeted"])}

---
ROLE / CONTEXT:
{user_instruction}

{company_line}
---

RESUME (only use what is directly relevant to the role above):
{resume_text}
---

HOW A GOOD OUTREACH EMAIL WORKS:

A hiring manager or senior engineer reading this email is asking three questions:
1. Does this person understand what the role actually involves?
2. Have they done something similar or adjacent?
3. Is this worth five more minutes of my time?

Your job is to answer those three questions in as few words as possible.

WHAT TO WRITE:

Paragraph 1:
- Show you understand the role — what kind of problems it involves, what the team likely cares about
- Then briefly show you've worked on something similar
- Name a specific project from the resume if relevant, but describe what problem it solved — not its metrics
- 3-4 sentences maximum

Paragraph 2:
- One supporting point that adds a different dimension — could be a technical depth, a domain, a workflow
- 2-3 sentences only

Closing:
- One sentence, calm and direct
- "Resume attached." or "Happy to share more context if useful." or similar
- No enthusiasm, no desperation, no call-to-action

---
TONE RULES — this is the most important section:

Think like a senior engineer writing to another senior engineer.
- Confident but not boastful
- Specific but not exhaustive
- Professional but human — like an email written at a desk, not generated
- Do NOT list metrics or percentages — a senior person does not need to prove themselves with numbers
- Do NOT mention hackathon wins, rankings, or CGPA — irrelevant to a professional audience
- Do NOT over-explain projects — name them and describe the problem they solved, not the implementation
- Do NOT use superlatives: "highly scalable", "cutting-edge", "robust", "innovative"
- Do NOT use filler phrases: "I am passionate about", "I would welcome", "I am excited to", "I specialize in"
- Do NOT start with "I am a Software Engineer" or "I am writing to apply"
- Each sentence should earn its place — if it doesn't add information, cut it

---
FORMAT:
- Start EXACTLY with: {greeting}
- Blank line
- Paragraph 1
- Blank line
- Paragraph 2
- Blank line
- Closing sentence
- Blank line
- End EXACTLY with:
Best regards,
Vikas K

- Under 400 words total
- No bullet points, no markdown, no bold
- Use \\n\\n between every paragraph in the JSON body field

---
Return ONLY valid JSON. Nothing before or after it.

{{
  "subject": "...",
  "body": "..."
}}
"""


# -------------------------------------------------------
# JSON Cleaner
# -------------------------------------------------------
def clean_json(text: str):
    text = text.strip()
    text = re.sub(r"```json|```", "", text).strip()

    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end == 0:
        raise Exception(f"Model did not return valid JSON. Raw: {text[:500]}")

    try:
        return json.loads(text[start:end], strict=False)
    except json.JSONDecodeError as e:
        raise Exception(f"JSON parse error: {str(e)} | Raw: {text[start:end][:300]}")


# -------------------------------------------------------
# Generate Email
# -------------------------------------------------------
def generate_email(user_instruction: str, recipient_name: str = "", email_style: str = "targeted"):
    headers = {
        "Authorization": f"Bearer {SARVAM_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sarvam-m",
        "messages": [
            {
                "role": "user",
                "content": build_prompt(user_instruction, recipient_name, email_style)
            }
        ],
        "temperature": 0.3,
        "max_tokens": 700
    }

    response = requests.post(SARVAM_URL, headers=headers, json=payload, timeout=30)

    if response.status_code != 200:
        raise Exception(f"API Error {response.status_code}: {response.text}")

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    email = clean_json(content)

    # Normalize paragraph spacing
    email["body"] = re.sub(r'\n{3,}', '\n\n', email["body"].strip())

    return email