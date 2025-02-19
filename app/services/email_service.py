import os
import time
import random
import string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from dotenv import load_dotenv
from app.logFile import logger

# Load environment variables
load_dotenv()
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")

def generate_verification_code(length=6):
    """
    Generate a random verification code.

    Args:
        length (int): The length of the verification code.

    Returns:
        str: The generated verification code.
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class EmailService:
    """
    A service class for sending emails using SendGrid.
    """

    def __init__(self):
        """
        Initialize the EmailService with SendGrid credentials.
        """
        self.sendgrid_client = SendGridAPIClient(SENDGRID_API_KEY)
        self.from_email = FROM_EMAIL
        self.verification_codes = {}
        self.company_name = "SKEMA Business School"
    
    def cleanup_expired_codes(self):
        """
        Remove expired verification codes from the dictionary.

        This method iterates through the dictionary of verification codes
        and deletes those that were created than 5 minutes ago (300 seconds).
        This helps keep the dictionary up-to-date and prevents
        the validation of outdated codes.

        Returns:
            None
        """
        current_time = time.time()
        for email in list(self.verification_codes.keys()):
            _, timestamp = self.verification_codes[email]
            if (current_time - timestamp) > 300:
                del self.verification_codes[email]

    def send_email_without_spam(self, subject, body, code, to_email):
        """
        Sends an email using SendGrid API.
        
        Args:
            subject (str): The subject of the email.
            body (str): The HTML content of the email.
            code (str): The verification code to be included in the email.
            to_email (str): The recipient's email address.
        
        Returns:
            bool: Returns `True` if the email was sent successfully, `False` otherwise.
        """
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=body
            )

            response = self.sendgrid_client.send(message)
            
            if response.status_code in range(200, 300):
                return True
            else:
                logger.error(f"SendGrid Error {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def send_email(self, subject, body, to_email):
        """
        Send an email using SendGrid API.

        Args:
            subject (str): The subject of the email.
            body (str): The body content of the email.
            to_email (str): The recipient's email address.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=body
            )

            response = self.sendgrid_client.send(message)
            
            if response.status_code in range(200, 300):
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"SendGrid Error {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_verification_code(self, email: str, isUser: bool = True):
        """
        Send a verification code to the given email address with a more friendly and styled email content.

        Args:
            email (str): The recipient's email address.
            isUser (bool): If True, sends user template, if False sends admin template. Defaults to True.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        code = generate_verification_code()
        self.verification_codes[email] = (code, time.time())
        subject = "SKEMA Business School - Verification Code for Alternance App"
        
        # Define content based on recipient type
        content = {
            "title": "Welcome to Alternance App!" if isUser else "Welcome to Alternance & Back-Office!",
            "recipient": "student" if isUser else "Admin",
            "app_name": "SKEMA Alternance App" if isUser else "SKEMA Alternance & Back-Office"
        }
        
        # HTML body with inline styling for better presentation
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <table width="100%" style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 20px; border-radius: 8px;">
                <tr>
                    <td style="text-align: center;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/4/46/Skema_Business_School_Logo.png" alt="SKEMA Business School" style="width: 120px; margin-bottom: 20px;" />
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center; color: #333333;">
                        <h2 style="color: #007bff;">{content['title']}</h2>
                        <p style="font-size: 16px; color: #555555;">
                            Dear {content['recipient']},<br><br>
                            To complete your registration on the <strong>{content['app_name']}</strong>, 
                            please use the verification code below to verify your email address.
                        </p>
                        <p style="font-size: 14px; color: #ff5733; font-weight: bold;">
                            This code is valid for five minutes.
                        </p>
                        <p style="font-size: 20px; color: #007bff; font-weight: bold; border: 1px solid #007bff; padding: 10px 20px; border-radius: 4px; display: inline-block;">
                            {code}
                        </p>
                        <p style="font-size: 14px; color: #999999;">
                            If you did not request this code, please ignore this email.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center; padding-top: 20px;">
                        <p style="font-size: 14px; color: #888888;">
                            Best regards,<br>
                            <strong>SKEMA Business School Team</strong>
                        </p>
                        <p style="font-size: 12px; color: #cccccc;">
                            SKEMA Business School | SKEMA Business School Lille - Avenue Willy Brandt, 59777, France Lille | https://www.skema.edu/fr/contact
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        # Send the email using the spam-safe function
        return self.send_email_without_spam(subject=subject, body=body, code=code, to_email=email)

    def verify_code(self, email, code):
        """
        Verify the provided verification code for the given email.

        This method first cleans up any expired verification codes from
        the dictionary. It then checks if the provided code matches
        the stored code for the given email. If the code is valid,
        it removes the code from the dictionary.

        Args:
            email (str): The email address to verify.
            code (str): The verification code entered by the user.

        Returns:
            bool: True if the code is valid and not expired, False otherwise.
        """
        self.cleanup_expired_codes()
        
        if email in self.verification_codes:
            stored_code, timestamp = self.verification_codes[email]

            if stored_code == code:
                del self.verification_codes[email]  
                return True
        
        return False
    
    def send_job_notification(self, line_counts, transfer_status, success):
        """
        Send a notification about the job processing status.

        Args:
            line_counts (dict): Dictionary with platform-region line counts.
            transfer_status (dict): Dictionary with transfer status by platform and region.
            success (bool): Whether the processing was successful.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        subject = "📊 Job Processing Notification"
        status = "successful" if success else "failed"

        # Constructing the body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="background-color: #ffffff; padding: 20px; border-radius: 8px;">
                <h2 style="color: #333333;">Job Processing Status</h2>
                <p style="font-size: 16px; color: #555555;">
                    The job processing has been <strong>{status}</strong>.
                </p>
                <h3>Line Counts by Platform and Region:</h3>
                <ul>
        """

        for platform, regions in line_counts.items():
            body += f"<li><strong>{platform}</strong>:<ul>"
            for region, count in regions.items():
                body += f"<li>{region}<ul>"
                body += f"<li>=> <strong>{count}</strong> lines</li>"
                body += f"<li>=> Transfer: <strong>{'Success' if transfer_status[platform][region] else 'Failed'}</strong></li>"
                body += "</ul></li>"
            body += "</ul></li>"

        body += """
                </ul>
            </div>
        </body>
        </html>
        """
        return self.send_email(subject, body, self.from_email)

    def send_clustering_notification(self, clustering_results, success):
        """
        Send a notification about the clustering process status.

        Args:
            clustering_results (dict): Dictionary with platform-region results (success or failure).
            success (bool): Whether the overall clustering process was successful.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        subject = "🧠 Clustering Process Notification"
        status = "successful" if success else "failed"

        # Constructing the body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="background-color: #ffffff; padding: 20px; border-radius: 8px;">
                <h2 style="color: #333333;">Clustering Process Status</h2>
                <p style="font-size: 16px; color: #555555;">
                    The clustering process has been <strong>{status}</strong>.
                </p>
                <h3>Results by Platform and Region:</h3>
                <ul>
        """

        for platform_region, result in clustering_results.items():
            message = result.get('message', 'No message')
            model = result.get('best_model', 'N/A')
            scores = result.get('model_scores', {})
            body += f"""
            <li><strong>{platform_region}</strong>:
                <ul>
                    <li>Status: {message}</li>
                    <li>Best Model: {model}</li>
                    <li>Model Scores: {scores}</li>
                </ul>
            </li>
            """

        body += """
                </ul>
            </div>
        </body>
        </html>
        """
        return self.send_email(subject, body, self.from_email)
