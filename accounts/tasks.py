from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_password_reset_email(
    self,
    email,
    username,
    code,
):
    subject = "Password Reset Code - AbrenCare"

    message = f"""
            Hello {username},

            You requested a password reset for your AbrenCare account.

            Your password reset code is:

            {code}

            This code will expire in 10 minutes.

            If you did not request this password reset, you can safely ignore
            this email.

            Best regards,
            AbrenCare Team
            """

    html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Password Reset</title>
            </head>

            <body style="
                margin:0;
                padding:0;
                background:#f5f5f5;
                font-family:Arial,sans-serif;
            ">

            <div style="
                max-width:600px;
                margin:40px auto;
                background:#ffffff;
                border-radius:10px;
                overflow:hidden;
            ">

                <div style="
                    padding:30px;
                    text-align:center;
                    background:#667eea;
                    color:#ffffff;
                ">
                    <h1>AbrenCare</h1>
                    <p>Password Reset Request</p>
                </div>

                <div style="padding:30px;">

                    <h2>Hello {username},</h2>

                    <p>
                        You requested a password reset for your
                        AbrenCare account.
                    </p>

                    <p>
                        Your password reset code is:
                    </p>

                    <div style="
                        margin:25px 0;
                        padding:20px;
                        text-align:center;
                        font-size:32px;
                        font-weight:bold;
                        letter-spacing:8px;
                        background:#f5f5f5;
                        border-radius:8px;
                    ">
                        {code}
                    </div>

                    <p>
                        <strong>
                            This code will expire in 10 minutes.
                        </strong>
                    </p>

                    <p>
                        If you did not request this password reset,
                        you can safely ignore this email.
                    </p>

                    <p>
                        Best regards,<br>
                        AbrenCare Team
                    </p>

                </div>
            </div>

            </body>
            </html>
            """

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_password_reset_confirmation_email(
    self,
    email,
    username,
):
    subject = "Password Reset Successful - AbrenCare"

    message = f"""
        Hello {username},

        Your AbrenCare password has been successfully reset.

        If you did not make this change, please contact support immediately.

        Best regards,
        AbrenCare Team
        """

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
