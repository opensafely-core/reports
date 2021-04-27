import structlog

from .models import Organisation

logger = structlog.getLogger()


def update_user_profile(strategy, details, backend, user=None, *args, **kwargs):
    """
    Set or update a user's organisation if required.
    """
    if not user:
        return

    organisations = details["nhsid_user_orgs"]
    for organisation_item in organisations:
        org_code = organisation_item["org_code"]
        if not user.organisations.filter(code=org_code).exists():
            organisation, new = Organisation.objects.get_or_create(
                name=organisation_item["org_name"], code=org_code
            )
            if new:
                logger.info(
                    "Organisation created",
                    org_id=organisation.pk,
                    org_code=organisation.code,
                )
            user.organisations.add(organisation)
            logger.info(
                "Organisation added for user",
                user_id=user.pk,
                username=user.username,
                org_id=organisation.pk,
                org_code=organisation.code,
            )
