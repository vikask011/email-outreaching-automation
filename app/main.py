from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List
import time

from app.ai import generate_email
from app.email_service import send_email

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ==============================
# STEP 1: Generate Draft
# ==============================
@app.post("/generate", response_class=HTMLResponse)
def generate(
    request: Request,
    names: List[str] = Form(...),
    emails: List[str] = Form(...),
    prompt: str = Form(...),
    email_style: str = Form("targeted")
):
    try:
        # Clean inputs
        names = [n.strip() for n in names]
        emails = [e.strip() for e in emails]
        recipients = list(zip(names, emails))

        is_single = len(recipients) == 1
        first_name = names[0] if is_single and names[0] else ""

        # Single recipient: personalize draft directly
        # Multiple recipients: generate with blank name, personalize at send time
        email_data = generate_email(
            user_instruction=prompt,
            recipient_name=first_name,
            email_style=email_style
        )

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "subject": email_data["subject"],
                "body": email_data["body"],
                "draft_ready": True,
                "recipients": recipients,
                "is_multi": not is_single,
                "prompt": prompt,
                "email_style": email_style,
            }
        )

    except Exception as e:
        names = [n.strip() for n in names]
        emails = [e.strip() for e in emails]
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": str(e),
                "recipients": list(zip(names, emails)),
                "prompt": prompt,
                "email_style": email_style,
            }
        )


# ==============================
# STEP 2: Send to All
# ==============================
@app.post("/send", response_class=HTMLResponse)
def send(
    request: Request,
    names: List[str] = Form(...),
    emails: List[str] = Form(...),
    subject: str = Form(...),
    body: str = Form(...)
):
    sent_count = 0
    failed = []

    for name, email in zip(names, emails):
        email = email.strip()
        name = name.strip()

        # Replace greeting with recipient's name if available
        personalized_body = body
        if name:
            # Replace any existing "Dear ..., " greeting line
            import re
            personalized_body = re.sub(
                r"^Dear [^,\n]+,",
                f"Dear {name},",
                body,
                count=1,
                flags=re.MULTILINE
            )

        try:
            send_email(
                to_email=email,
                subject=subject,
                body=personalized_body,
                resume_path="resumes/resume_ai.pdf"
            )
            sent_count += 1
            time.sleep(2)  # avoid Gmail rate limiting

        except Exception as e:
            failed.append(f"{email} ({str(e)})")

    all_recipients = list(zip([n.strip() for n in names], [e.strip() for e in emails]))

    if failed:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": f"Sent to {sent_count}. Failed: {', '.join(failed)}",
                "recipients": all_recipients,
            }
        )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "success": f"✓ Sent to {sent_count} recipient{'s' if sent_count != 1 else ''}",
            "recipients": all_recipients,
        }
    )