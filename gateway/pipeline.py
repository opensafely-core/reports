from .models import Organisation, UserProfile


def update_user_profile(strategy, details, backend, user=None, *args, **kwargs):
    """
    Set or update a User's profile information if required.
    """
    if not user:
        return
    profile, new = UserProfile.objects.get_or_create(user=user)
    if new or (profile.title, profile.display_name) != (
        details["title"],
        details["display_name"],
    ):
        profile.title = details["title"]
        profile.display_name = details["display_name"]
        profile.save()

    organisations = details["nhsid_user_orgs"]
    for organisation_item in organisations:
        org_code = organisation_item["org_code"]
        if not profile.organisations.filter(code=org_code).exists():
            organisation, _ = Organisation.objects.get_or_create(
                name=organisation_item["org_name"], code=org_code
            )
            profile.organisations.add(organisation)
