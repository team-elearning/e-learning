from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist

from account.domains.parental_consent_domain import ParentalConsentDomain
from account.models import ParentalConsent


def grant_consent(domain: ParentalConsentDomain) -> ParentalConsentDomain:
    consent, _ = ParentalConsent.objects.update_or_create(
        parent_id=domain.parent_id,
        child_id=domain.child_id,
        defaults={
            "scopes": domain.scopes,
            "metadata": domain.metadata,
            "revoked_at": None,
        },
    )
    return ParentalConsentDomain.from_model(consent)


def revoke_consent(parent_id: int, child_id: int) -> bool:
    try:
        consent = ParentalConsent.objects.get(parent_id=parent_id, child_id=child_id)
        consent.revoked_at = datetime.now()
        consent.save()
        return True
    except ObjectDoesNotExist:
        return False


def has_consent(parent_id: int, child_id: int) -> bool:
    return ParentalConsent.objects.filter(
        parent_id=parent_id, child_id=child_id, revoked_at__isnull=True
    ).exists()


def list_consents_for_parent(parent_id: int) -> list[ParentalConsentDomain]:
    consents = ParentalConsent.objects.filter(parent_id=parent_id, revoked_at__isnull=True)
    return [ParentalConsentDomain.from_model(c) for c in consents]


def check_consent_for_child(parent_id: int, child_id: int) -> bool:
    return ParentalConsent.objects.filter(
        parent_id=parent_id, child_id=child_id, revoked_at__isnull=True
    ).exists()