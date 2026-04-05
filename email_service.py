import os
import resend
from base64 import b64encode

resend.api_key = os.getenv('RESEND_API_KEY')

def send_ticket_email(recipient_email, recipient_name, ticket_number, event_name, 
                     ticket_type, event_date, event_location, qr_code_bytes):
    """Send single ticket email with QR code as attachment"""
    
    try:
        # Convert QR code to base64 for attachment
        qr_base64 = b64encode(qr_code_bytes).decode('utf-8')
        
        # Email HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    background: #f7fafc; 
                    padding: 20px;
                    margin: 0;
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 0 auto; 
                    background: white; 
                    border-radius: 12px; 
                    overflow: hidden; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                }}
                .header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    padding: 40px 30px; 
                    text-align: center; 
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                }}
                .content {{ 
                    padding: 30px; 
                    color: #2d3748;
                    line-height: 1.6;
                }}
                .ticket-info {{ 
                    background: #f7fafc; 
                    padding: 25px; 
                    border-radius: 8px; 
                    margin: 25px 0;
                    border-left: 4px solid #667eea;
                }}
                .ticket-info h3 {{
                    margin: 0 0 15px 0;
                    color: #667eea;
                    font-size: 18px;
                }}
                .ticket-info p {{ 
                    margin: 8px 0;
                    font-size: 15px;
                }}
                .ticket-info strong {{
                    color: #2d3748;
                    font-weight: 600;
                }}
                .qr-section {{
                    background: #fff;
                    border: 2px dashed #cbd5e0;
                    border-radius: 8px;
                    padding: 25px;
                    text-align: center;
                    margin: 25px 0;
                }}
                .qr-section h3 {{
                    color: #2d3748;
                    margin: 0 0 15px 0;
                    font-size: 18px;
                }}
                .qr-section p {{
                    color: #718096;
                    font-size: 14px;
                    margin: 10px 0;
                }}
                .qr-note {{
                    background: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .qr-note p {{
                    margin: 0;
                    color: #92400e;
                    font-size: 14px;
                }}
                .footer {{ 
                    background: #f7fafc; 
                    padding: 25px; 
                    text-align: center; 
                    color: #718096; 
                    font-size: 14px;
                    border-top: 1px solid #e2e8f0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎟️ Your Ticket is Ready!</h1>
                </div>
                <div class="content">
                    <p>Hi <strong>{recipient_name}</strong>,</p>
                    <p>Your ticket for <strong>{event_name}</strong> has been confirmed!</p>
                    
                    <div class="ticket-info">
                        <h3>📋 Event Details</h3>
                        <p><strong>Event Name:</strong> {event_name}</p>
                        <p><strong>Date & Time:</strong> {event_date}</p>
                        <p><strong>Location:</strong> {event_location}</p>
                        <p><strong>Ticket Type:</strong> {ticket_type}</p>
                        <p><strong>Ticket Number:</strong> <code>{ticket_number}</code></p>
                    </div>
                    
                    <div class="qr-section">
                        <h3>📱 Your QR Code</h3>
                        <p><strong>Your QR code is attached to this email</strong></p>
                        <p>Download and save it to your phone for easy access at the event.</p>
                    </div>
                    
                    <div class="qr-note">
                        <p><strong>💡 Important:</strong> Present the attached QR code at the entrance.</p>
                    </div>
                    
                    <p>See you at the event!</p>
                </div>
                <div class="footer">
                    <p><strong>Ticket9ja</strong></p>
                    <p>Professional Event Ticketing Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        email_from = os.getenv('EMAIL_FROM', 'onboarding@resend.dev')
        
        # Send email with QR code as attachment
        response = resend.Emails.send({
            "from": email_from,
            "to": [recipient_email],
            "subject": f"🎟️ Your Ticket for {event_name} - {ticket_number}",
            "html": html,
            "attachments": [
                {
                    "filename": f"{ticket_number}.png",
                    "content": qr_base64
                }
            ]
        })
        
        return True
        
    except Exception as e:
        print(f"     Email sending error: {type(e).__name__}: {str(e)}")
        return False
