import os
import resend
from base64 import b64encode

resend.api_key = os.getenv('RESEND_API_KEY')

def send_ticket_email(recipient_email, recipient_name, ticket_number, event_name, 
                     ticket_type, event_date, event_location, qr_code_bytes):
    """Send ticket email with QR code"""
    
    try:
        print(f"\n📧 EMAIL SERVICE CALLED")
        print(f"  To: {recipient_email}")
        print(f"  Name: {recipient_name}")
        print(f"  Ticket: {ticket_number}")
        print(f"  Event: {event_name}")
        
        # Check if API key is set
        if not resend.api_key or resend.api_key == '':
            print("❌ RESEND_API_KEY not set in environment!")
            return False
        
        print(f"  API Key: {resend.api_key[:10]}...{resend.api_key[-5:]}")
        
        # Convert QR code to base64
        qr_base64 = b64encode(qr_code_bytes).decode('utf-8')
        
        # Email HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f7fafc; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .ticket-info {{ background: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .qr-code {{ text-align: center; margin: 20px 0; }}
                .qr-code img {{ width: 200px; height: 200px; }}
                .footer {{ background: #f7fafc; padding: 20px; text-align: center; color: #718096; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎟️ Your Ticket is Ready!</h1>
                </div>
                <div class="content">
                    <p>Hi {recipient_name},</p>
                    <p>Your ticket for <strong>{event_name}</strong> has been confirmed!</p>
                    
                    <div class="ticket-info">
                        <h3>Event Details</h3>
                        <p><strong>Event:</strong> {event_name}</p>
                        <p><strong>Date:</strong> {event_date}</p>
                        <p><strong>Location:</strong> {event_location}</p>
                        <p><strong>Ticket Type:</strong> {ticket_type}</p>
                        <p><strong>Ticket Number:</strong> {ticket_number}</p>
                    </div>
                    
                    <div class="qr-code">
                        <p><strong>Your QR Code:</strong></p>
                        <img src="data:image/png;base64,{qr_base64}" alt="QR Code">
                        <p style="font-size: 14px; color: #718096;">Present this QR code at the entrance</p>
                    </div>
                    
                    <p>We look forward to seeing you at the event!</p>
                </div>
                <div class="footer">
                    <p>Powered by Ticket9ja</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        email_from = os.getenv('EMAIL_FROM', 'onboarding@resend.dev')
        print(f"  From: {email_from}")
        
        # Send email
        print("  📤 Sending via Resend API...")
        response = resend.Emails.send({
            "from": email_from,
            "to": [recipient_email],
            "subject": f"Your Ticket for {event_name}",
            "html": html
        })
        
        print(f"  ✅ Resend Response: {response}")
        print(f"  📨 Email ID: {response.get('id', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ EMAIL ERROR:")
        print(f"  Type: {type(e).__name__}")
        print(f"  Message: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
