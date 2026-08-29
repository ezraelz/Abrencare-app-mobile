from ..models import FamilyAuditLog


# ============================================================
# AUDIT HELPERS
# ============================================================

def _create_audit_log(
    *,
    family,
    action,
    actor=None,
    invitation=None,
    patient=None,
    metadata=None,
    request=None,
):
    """
    Create a security audit event.

    Never place secrets or passwords in metadata.
    """

    ip_address = None
    user_agent = ""

    if request is not None:
        forwarded_for = request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )

        if forwarded_for:
            ip_address = (
                forwarded_for.split(",")[0].strip()
            )
        else:
            ip_address = request.META.get(
                "REMOTE_ADDR"
            )

        user_agent = request.META.get(
            "HTTP_USER_AGENT",
            "",
        )

    return FamilyAuditLog.objects.create(
        family=family,
        actor=actor,
        action=action,
        invitation=invitation,
        patient=patient,
        metadata=metadata or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
