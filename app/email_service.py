import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from app.config import GMAIL_EMAIL, GMAIL_APP_PASSWORD


def format_html(body: str) -> str:
    """Convert plain text email body to clean HTML."""

    # Convert each line to a paragraph, preserve blank lines as spacing
    paragraphs = body.strip().split("\n\n")

    html_paragraphs = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Signature block — render as smaller muted text
        if para.startswith("Best regards"):
            lines = para.replace("\n", "<br>")
            html_paragraphs += f"""
            <p style="margin: 28px 0 0 0; color: #4a5568; font-size: 14px; line-height: 1.6;">
                {lines}
            </p>
            """
        else:
            lines = para.replace("\n", "<br>")
            html_paragraphs += f"""
            <p style="margin: 0 0 18px 0; color: #1a202c; font-size: 15px; line-height: 1.75;">
                {lines}
            </p>
            """

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
</head>
<body style="margin:0; padding:0; background:#f4f6f8; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" border="0"
    style="background:#f4f6f8; padding: 40px 20px;">
    <tr>
      <td align="center">

        <!-- Email Card -->
        <table width="600" cellpadding="0" cellspacing="0" border="0"
          style="background:#ffffff; border-radius:12px;
                 box-shadow: 0 2px 12px rgba(0,0,0,0.07);
                 overflow:hidden; max-width:600px; width:100%;">

          <!-- Top accent bar -->
          <tr>
            <td style="background: linear-gradient(90deg, #1a202c 0%, #2d3748 100%);
                       height: 4px; font-size:0; line-height:0;">&nbsp;</td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding: 40px 44px 36px 44px;">
              {html_paragraphs}
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding: 0 44px;">
              <hr style="border:none; border-top:1px solid #e2e8f0; margin:0;">
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 20px 44px 32px 44px;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td>
                    <p style="margin:0; font-size:12px; color:#a0aec0; font-family: 'Helvetica Neue', Arial, sans-serif;">
                      Resume attached · <a href="mailto:vikask050905@gmail.com"
                        style="color:#a0aec0; text-decoration:underline;">vikask050905@gmail.com</a>
                    </p>
                  </td>
                  <td align="right">
                    <p style="margin:0; font-size:12px; color:#cbd5e0;">Vikas K</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>
        <!-- End Email Card -->

      </td>
    </tr>
  </table>

</body>
</html>
"""


def send_email(to_email: str, subject: str, body: str, resume_path: str):
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = GMAIL_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        # Plain text fallback (for clients that don't render HTML)
        plain_part = MIMEText(body, "plain", "utf-8")

        # HTML formatted version
        html_part = MIMEText(format_html(body), "html", "utf-8")

        # Attach both — email clients prefer the last one (HTML)
        msg.attach(plain_part)
        msg.attach(html_part)

        # Attach resume PDF
        with open(resume_path, "rb") as f:
            pdf = MIMEApplication(f.read(), _subtype="pdf")
            file_name = resume_path.split("/")[-1]
            pdf.add_header("Content-Disposition", "attachment", filename=file_name)
            msg.attach(pdf)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)

    except smtplib.SMTPAuthenticationError:
        raise Exception("SMTP Authentication Failed. Check your Gmail App Password.")

    except smtplib.SMTPRecipientsRefused:
        raise Exception(f"Recipient refused: {to_email}")

    except Exception as e:
        raise Exception(f"Failed to send to {to_email}: {str(e)}")