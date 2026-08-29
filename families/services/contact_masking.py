# ============================================================
# CONTACT MASKING
# ============================================================

def _mask_contact(
    value,
    channel,
):
    """
    Mask email or phone information before
    exposing it to the frontend.
    """

    if not value:
        return ""

    if channel == "email":
        if "@" not in value:
            return "***"

        local, domain = value.split(
            "@",
            1,
        )

        if len(local) <= 2:
            masked_local = (
                "*" * len(local)
            )
        else:
            masked_local = (
                local[0]
                + "*" * (len(local) - 2)
                + local[-1]
            )

        return f"{masked_local}@{domain}"

    if len(value) <= 4:
        return "*" * len(value)

    return (
        "*" * (len(value) - 4)
        + value[-4:]
    )
