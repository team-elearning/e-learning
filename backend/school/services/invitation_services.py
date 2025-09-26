import uuid
from uuid import uuid4
from typing import Optional
from django.db import transaction
from datetime import timedelta, timezone

from account.models import UserModel
from school.models import ClassroomModel, MembershipModel, InvitationModel
from school.domains.class_domain import MembershipDomain, ClassroomDomain
from school.domains.invitation_domain import InvitationDomain
from school.apis.permissions import PermissionDenied, ConflictError, NotFoundError, InvalidOperation, ensure_is_admin_or_instructor
from school.services.membership_services import join_classroom


@transaction.atomic
def create_invitation(
    requesting: UserModel,
    classroom_id: int,
    email: str,
    expire_days: int = 7,
    usage_limit: Optional[int] = None,
) -> InvitationDomain:
    """
    Create an invitation for a classroom.
    - Generates unique invite_code (UUID4).
    - Restrict by email (unique).
    - Set expiration and usage limit.
    - Initial status = "pending".
    """
    try:
        classroom_model = ClassroomModel.objects.get(id=classroom_id)
    except ClassroomModel.DoesNotExist:
        raise NotFoundError("Classroom not found.")

    ensure_is_admin_or_instructor(requesting, classroom_model)

    # Generate invite code (UUID4 → string)
    invite_code = str(uuid.uuid4())

    invitation_model = InvitationModel.objects.create(
        classroom=classroom_model,
        invite_code=invite_code,
        email=email,
        created_by=requesting.id,
        expires_on=timezone.now() + timedelta(days=expire_days),
        status="pending",
        usgaed_limit=usage_limit,
        used_count=0,
    )

    return InvitationDomain.from_model(invitation_model)


def get_invitation(*, invite_code: str = None, invitation_id: int = None) -> Optional[InvitationDomain]:
    """Fetch invitation by code or id."""
    try:
        if invite_code:
            model = InvitationModel.objects.get(invite_code=invite_code)
        elif invitation_id:
            model = InvitationModel.objects.get(id=invitation_id)
        else:
            return None
        return InvitationDomain.from_model(model)
    except InvitationModel.DoesNotExist:
        return None
    

def validate_invitation(invite_code: str) -> InvitationDomain:
    """
    Validate invitation: must be active, not expired, not over usage_limit.
    Raises InvalidOperation if invalid.
    """
    try:
        invitation_model = InvitationModel.objects.get(invite_code=invite_code)
    except InvitationModel.DoesNotExist:
        raise NotFoundError("Invitation not found.")

    invitation_domain = InvitationDomain.from_model(invitation_model)

    if not invitation_domain.is_valid():
        invitation_model.status = "expired"
        invitation_model.save(update_fields=["status"])
        raise InvalidOperation("Invitation is not valid or has expired.")

    return invitation_domain


@transaction.atomic
def accept_invitation(student: UserModel, invite_code: str) -> MembershipDomain:
    """
    Accept an invitation by invite_code. Creates membership and updates invitation usage/status.
    """
    try:
        invitation_model = InvitationModel.objects.select_for_update().get(invite_code=invite_code)
    except InvitationModel.DoesNotExist:
        raise NotFoundError("Invitation not found.")
    invitation_domain = InvitationDomain.from_model(invitation_model)

    # Check classroom status
    try:
        classroom_model = invitation_model.classroom
    except Exception:
        raise NotFoundError("Classroom for invitation not found.")
    classroom_domain = ClassroomDomain.from_model(classroom_model)
    classroom_domain.ensure_active()

    invitation_domain.mark_used()
    invitation_domain.save()

    return join_classroom(student, classroom_model.id, invite_code)


@transaction.atomic
def revoke_invitation(requesting: UserModel, invitation_id: int) -> InvitationDomain:
    """
    Revoke (cancel) an invitation.
    Only admin/instructor allowed.
    """
    try:
        invitation_model = InvitationModel.objects.select_for_update().get(id=invitation_id)
    except InvitationModel.DoesNotExist:
        raise NotFoundError("Invitation not found.")

    ensure_is_admin_or_instructor(requesting, invitation_model.classroom)

    if invitation_model.status != "active":
        raise InvalidOperation("Only active invitations can be revoked.")

    invitation_model.status = "revoked"
    invitation_model.save(update_fields=["status"])
    return InvitationDomain.from_model(invitation_model)