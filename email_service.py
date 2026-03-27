import resend
import os
from io import BytesIO

resend.api_key = os.getenv('RESEND_API_KEY')

def send_ticket_email(recipient_email, recipient_name, ticket_number, event_name, ticket_type, event_date, event_location, qr_code_bytes):
    """
    Send ticket email with QR code attachment
    """
    try:
        # Create HTML email template
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .ticket-container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .ticket-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; }}
        .ticket-body {{ padding: 30px; }}
        .ticket-number {{ font-size: 28px; font-weight: bold; color: #667eea; margin: 20px 0; text-align: center; letter-spacing: 2px; }}
        .qr-container {{ text-align: center; padding: 20px; background: white; margin: 20px 0; border-radius: 8px; }}
        .qr-code {{ max-width: 220px; height: auto; }}
        .info-row {{ margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
        .info-label {{ font-weight: bold; color: #666; font-size: 12px; text-transform: uppercase; }}
        .info-value {{ color: #333; font-size: 16px; margin-top: 5px; }}
        .footer {{ text-align: center; padding: 20px; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="ticket-container">
        <div class="ticket-header">
            <h1 style="margin: 0; font-size: 28px;">Ticket9ja</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Your Event Ticket</p>
        </div>
        
        <div class="ticket-body">
            <div class="ticket-number">{ticket_number}</div>
            
            <div class="qr-container">
                <img src="cid:qrcode" alt="QR Code" class="qr-code"/>
                <p style="margin-top: 10px; color: #666; font-size: 14px;">Scan this code at the event</p>
            </div>
            
            <div class="info-row">
                <div class="info-label">Attendee Name</div>
                <div class="info-value">{recipient_name}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">Event</div>
                <div class="info-value">{event_name}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">Ticket Type</div>
                <div class="info-value">{ticket_type}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">Date & Time</div>
                <div class="info-value">{event_date}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">Venue</div>
                <div class="info-value">{event_location}</div>
            </div>
        </div>
        
        <div class="footer">
            <p>Please present this ticket (digital or printed) at the event entrance.</p>
            <p>For support, contact support@ticket9ja.com</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Send email with QR code attachment
        email_from = os.getenv('EMAIL_FROM', 'Ticket9ja <tickets@ticket9ja.com>')
        
        params = {
            "from": email_from,
            "to": [recipient_email],
            "subject": f"Your Ticket for {event_name}",
            "html": html_content,
            "attachments": [{
                "content": qr_code_bytes,
                "filename": "qrcode.png",
                "content_id": "qrcode"
            }]
        }
        
        email = resend.Emails.send(params)
        print(f"Ticket email sent to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
