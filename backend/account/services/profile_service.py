from account.domains.profile_domain import ProfileDomain
from account.models import Profile 



def create_profile(domain: ProfileDomain) -> ProfileDomain:
    profile = Profile.objects.create(
        user_id=domain.user_id,
        display_name=domain.display_name,
        avatar_url=domain.avatar_url,
        dob=domain.dob,
        gender=domain.gender,
        language=domain.language,
        metadata=domain.metadata,
    )
    return ProfileDomain.from_model(profile)


def update_profile(user_id: int, data: dict) -> ProfileDomain:
    profile = Profile.objects.get(user_id=user_id)
    for field, value in data.items():
        setattr(profile, field, value)
    profile.save()
    return ProfileDomain.from_model(profile)


def get_profile_by_user(user_id: int) -> ProfileDomain:
    profile = Profile.objects.get(user_id=user_id)
    return ProfileDomain.from_model(profile)