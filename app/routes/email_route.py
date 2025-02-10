from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from app.services import email_service, user_data_manager_service, datamanager_service
from app.logFile import logger
import os
from jose import JWTError, jwt

email_router = APIRouter(prefix="/auth")

# Model for the verification code request
class VerificationRequest(BaseModel):
    email: str
    code: str
    user_role: str  # "admin" ou "user"
    log_to_alternance: bool = True

# Model for the refresh token request
class RefreshTokenRequest(BaseModel):
    refreshToken: str

# Model for the email request
class EmailRequest(BaseModel):
    email: str


@email_router.post("/send-verification-code")
async def send_verification_code(request: EmailRequest):
    """
    Endpoint to send a verification code to the provided email address.
    The email is validated as follows:
    1. If the email ends with "@skema.edu", it is considered valid and a new account is created if needed.
    2. If the email does not belong to the SKEMA domain, it is checked against the database.
    3. If the email is neither from the SKEMA domain nor found in the database, an error is returned.
    
    Args:
        email (str): The email address to send the verification code to.
        
    Returns:
        dict: A message indicating whether the verification code was sent successfully or not.
            - If successful: {"message": "Verification code sent successfully", "status": True, "user_role": <role>}
            - If failed: {"message": <error_message>, "status": False, "detail": <error_detail>}
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)  
            user_info = user_data_manager.get_user_by_email(request.email)
            # Check if the email is from SKEMA domain
            is_skema_email = request.email.endswith("@skema.edu")
            
            if not is_skema_email and not user_info:
                raise HTTPException(
                    status_code=400,
                    detail="This email is neither from SKEMA nor registered in our database."
                )
            
            #if is_skema_email and not user_info:
            #    user_id, user_role = user_data_manager.get_or_create_user(request.email)
            #    user_info = {"_id": user_id, "user_role": user_role}
                
        is_user = user_info is not None and user_info.get("user_role") != "admin"

        if user_info and email_service.send_verification_code(request.email, is_user):
            return {"message": "Verification code sent successfully", "status": True, "user_role": user_info['user_role']}
        else:
            raise HTTPException(status_code=500, detail="Failed to send verification code")

    except Exception as e:
        logger.error(f"An error occurred while sending the verification code: {str(e)}")
        return JSONResponse(
            content={"message": "An error occurred while sending the verification code", "status": False, "detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@email_router.post("/verify-code")
async def verify_code(verification_request: VerificationRequest):
    """
    Endpoint to verify the provided verification code for the given email address.

    Args:
        email (str): The email address to verify.
        code (str): The verification code entered by the user.
        user_role (str): The role of the user ("admin" or "user").
        log_to_alternance (bool): Whether to log the connection to the alternance database.

    Returns:
        dict: A message indicating whether the verification code is valid or not.
    """
    try:
        email = verification_request.email.lower()  
        code = verification_request.code
        user_role = verification_request.user_role.lower()  
        log_to_alternance = verification_request.log_to_alternance

        if email_service.verify_code(email, code):
            with datamanager_service() as mongodb_manager:
                user_data_manager = user_data_manager_service(mongodb_manager)

                if user_role == "admin":
                    log_result = user_data_manager.log_admin(email)
                elif user_role == "user":
                    log_result = user_data_manager.log_user(email)
                else:
                    raise ValueError("Invalid user_role. Must be 'admin' or 'user'.")

                if log_to_alternance:
                    user_data_manager.log_connection(email, user_role)

                if log_result["status"]:
                    user_id = log_result["_id"]  
                    return {"user_id": user_id, "statut": True}
                else:
                    return {"message": "User not found", "status": False}
        else:
            return {"message": "Invalid verification code", "status": False}

    except Exception as e:
        logger.error(f"An error occurred while verifying the code: {str(e)}")
        return JSONResponse(
            content={"message": "An error occurred while verifying the code", "status": False, "detail": str(e)},
            status_code=500
        )

@email_router.post('/verify-code-with-token')
async def verify_code_and_send_token(verification_request: VerificationRequest):
    """
    Endpoint to verify the provided verification code for the given email address,
    log the user according to their role, and send access and refresh tokens if the code is valid.

    Args:
        verification_request (VerificationRequest): Contains email, code, user_role, and log_to_alternance flag.

    Returns:
        JSONResponse: A message indicating whether the verification code is valid and the tokens if successful.
    """
    try:
        email = verification_request.email.lower()
        code = verification_request.code
        user_role = verification_request.user_role.lower()
        log_to_alternance = verification_request.log_to_alternance

        if email_service.verify_code(email, code):
            with datamanager_service() as mongodb_manager:
                user_data_manager = user_data_manager_service(mongodb_manager)

                if user_role == "admin":
                    log_result = user_data_manager.log_admin(email)
                elif user_role == "user":
                    log_result = user_data_manager.log_user(email)
                else:
                    raise ValueError("Invalid user_role. Must be 'admin' or 'user'.")

                if log_to_alternance:
                    user_data_manager.log_connection(email, user_role)

                if not log_result["status"]:
                    return JSONResponse(
                        content={"message": "User not found", "status": False},
                        status_code=status.HTTP_404_NOT_FOUND
                    )

                # Generate tokens
                access_token_exp = datetime.now(timezone.utc) + timedelta(minutes=50)
                refresh_token_exp = datetime.now(timezone.utc) + timedelta(days=7)

                payload = {
                    'email': email,
                    'exp': access_token_exp,
                    'user_id': log_result["_id"],
                    'role': user_role
                }

                refresh_payload = {
                    'email': email,
                    'exp': refresh_token_exp,
                    'user_id': log_result["_id"],
                    'role': user_role
                }

                secret_key = os.getenv('SECRET_KEY')

                access_token = jwt.encode(payload, secret_key, algorithm='HS256')
                refresh_token = jwt.encode(refresh_payload, secret_key, algorithm='HS256')

                data = {
                    "status": True,
                    "user_id": log_result["_id"],
                    "accessToken": access_token,
                    "accessTokenExpiresAt": access_token_exp.isoformat(),
                    "refreshToken": refresh_token,
                    "refreshTokenExpiresAt": refresh_token_exp.isoformat(),
                    "message": "Verification code is valid",
                }
                return JSONResponse(content=data, status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(
                content={"message": "Invalid verification code", "status": False},
                status_code=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        logger.error(f"An error occurred while verifying the code: {str(e)}")
        return JSONResponse(
            content={"message": "An error occurred while verifying the code", "status": False, "detail": str(e)},
            status_code=500
        )


@email_router.post('/refresh-token')
async def refresh_access_token(refresh_token_request: RefreshTokenRequest):
    """
    Endpoint to refresh the access token using the refresh token.

    Args:
        refresh_token_request (RefreshTokenRequest): Contains the refresh token.

    Returns:
        JSONResponse: New access token and refresh token if the refresh token is valid.
    """
    try:
        refresh_token = refresh_token_request.refreshToken
        secret_key = os.getenv('SECRET_KEY')
        
        payload = jwt.decode(refresh_token, secret_key, algorithms=['HS256'])
        
        email = payload.get('email')
        user_id = payload.get('user_id')
        role = payload.get('role')

        if not all([email, user_id, role]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token - missing required claims"
            )

        access_token_exp = datetime.now(timezone.utc) + timedelta(minutes=50)
        refresh_token_exp = datetime.now(timezone.utc) + timedelta(days=7)

        access_payload = {
            'email': email,
            'exp': access_token_exp,
            'user_id': user_id,
            'role': role
        }

        refresh_payload = {
            'email': email,
            'exp': refresh_token_exp,
            'user_id': user_id,
            'role': role
        }

        new_access_token = jwt.encode(access_payload, secret_key, algorithm='HS256')
        new_refresh_token = jwt.encode(refresh_payload, secret_key, algorithm='HS256')

        data = {
            'status': True,
            'user_id': user_id,
            'accessToken': new_access_token,
            'accessTokenExpiresAt': access_token_exp.isoformat(),
            'refreshToken': new_refresh_token,
            'refreshTokenExpiresAt': refresh_token_exp.isoformat()
        }
        return JSONResponse(content=data, status_code=status.HTTP_200_OK)

    except JWTError as jwt_error:
        logger.error(f"JWT error while refreshing token: {str(jwt_error)}")
        return JSONResponse(
            content={"message": "Invalid refresh token", "status": False},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        logger.error(f"An error occurred while refreshing the token: {str(e)}")
        return JSONResponse(
            content={"message": "An error occurred while refreshing the token", "status": False, "detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@email_router.post("/get-user-id-by-email")
async def get_user_id_by_email(request: EmailRequest):
    """
    Retrieve a user's ID given their email address.

    Args:
        request (EmailRequest): The request containing the user's email.

    Returns:
        dict: A dictionary containing the user's ID or an error message.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)  
            user_id = user_data_manager.get_user_by_email(request.email)

        if user_id:
            return {"user_id": user_id}
        else:
            return {"message": "Aucun utilisateur trouvé avec cet e-mail."}

    except Exception as e:
        logger.error(f"Error retrieving user by email: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Error retrieving user by email"}
        )

@email_router.get("/test-email")
async def test_email():
    """
    Endpoint to test email sending functionality.
    
    This route is temporarily added for testing purposes to ensure
    that emails can be sent successfully in the Azure environment.
    It should be removed or secured before moving to production.

    Returns:
        dict: A message indicating whether the email was sent successfully or not.
    """
    subject = "Test Email from Azure"
    body = """
    <html>
    <body>
        <h1>Test Email</h1>
        <p>This is a test email sent from the Azure environment.</p>
    </body>
    </html>
    """
    to_email = email_service.email_user 

    try:
        success = email_service.send_email(subject, body, to_email)
        if success:
            return {"message": "Test email sent successfully"}
        else:
            raise Exception("Email sending failed without raising an error.")
    except Exception as e:
        return {"error": str(e)}



