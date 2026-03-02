# AI Outreach Agent

A personal email outreach tool that generates tailored cold emails from your resume using an LLM, lets you review and edit the draft, then sends it directly to one or many recipients — with every send logged to a PostgreSQL database.

Built for job hunting. No subscriptions, no SaaS. Runs locally, sends from your own Gmail.

---

## How it works

1. You describe the role or paste a job description
2. The app reads your resume PDF and sends both to the Sarvam AI model
3. A draft email is generated — subject line + body
4. You review it, edit if needed, then confirm send
5. The email goes out via Gmail SMTP with your resume attached
6. Every send (success or failure) is logged to Neon PostgreSQL
7. Visit `/history` to see the full send log

---

## Setup

Create a `resumes/` folder in the project root and add your resume PDF named `resume_ai.pdf`:

```
ai-outreach-agent/
└── resumes/
    └── resume_ai.pdf   ← your resume goes here
```

---

## .env

```dotenv
# Sarvam AI — https://sarvam.ai
SARVAM_API_KEY=your_sarvam_api_key_here

# Gmail App Password (not your real password)
# Google Account → Security → 2FA → App Passwords
GMAIL_EMAIL=you@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Neon PostgreSQL — https://neon.tech
DATABASE_URL=postgresql://neondb_owner:your_password@ep-your-endpoint.neon.tech/neondb?sslmode=require
```
