# ============================================================
# VERIFICATION HELPER
# ============================================================

def _require_verified_invitation(
    invitation,
):
    """
    Ensure contact verification happened before
    accepting, registering, or claiming.
    """

    if not invitation.contact_verified_at:
        raise ValueError(
            "Contact verification is required "
            "before completing this invitation."
        )


# ============================================================
# CONTACT OWNERSHIP HELPER
# ============================================================

def _invitation_belongs_to_user(
    invitation,
    user,
):
    """
    Verify that an invitation's verified contact
    belongs to the authenticated user.
    """

    invitation_email = (
        invitation.email or ""
    ).strip().lower()

    user_email = (
        getattr(user, "email", "")
        or ""
    ).strip().lower()

    invitation_phone = (
        invitation.phone_number or ""
    ).strip()

    user_phone = (
        getattr(user, "phone_number", "")
        or ""
    ).strip()

    email_matches = bool(
        invitation_email
        and user_email
        and invitation_email == user_email
    )

    phone_matches = bool(
        invitation_phone
        and user_phone
        and invitation_phone == user_phone
    )

    return email_matches or phone_matches
