def send_invitation_notification(
    *,
    invitation,
    raw_token,
):
    """
    Send the invitation notification.

    IMPORTANT:
        raw_token is sensitive and must never be persisted
        or logged.

    This function should eventually dispatch an asynchronous
    task rather than sending synchronously.
    """

    # Example future implementation:
    #
    # send_invitation_email.delay(
    #     invitation_id=invitation.id,
    #     raw_token=raw_token,
    # )
    #
    # or:
    #
    # send_invitation_sms.delay(
    #     invitation_id=invitation.id,
    #     raw_token=raw_token,
    # )

    return True


def send_otp_notification(
    *,
    invitation,
    otp,
):
    """
    Send an OTP through the appropriate provider.

    The raw OTP must never be persisted or logged.
    """

    # Example future implementation:
    #
    # send_otp_email.delay(
    #     invitation_id=invitation.id,
    #     otp=otp,
    # )
    #
    # or:
    #
    # send_otp_sms.delay(
    #     invitation_id=invitation.id,
    #     otp=otp,
    # )

    return True