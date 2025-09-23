from uuid import uuid4
from typing import Optional
from django.db import transaction
from datetime import timedelta, timezone

from account.models import UserModel
from classroom.models import ClassroomModel, MembershipModel, InvitationModel
from classroom.domains.class_domain import MembershipDomain, InvitationDomain
from classroom.apis.permissions import PermissionDenied, ConflictError, NotFoundError, InvalidOperation, ensure_is_admin_or_instructor



@transaction.atomic
def create_invitation(requesting: UserModel, classroom_id: int, *, email: Optional[str] = None,
                      expire_days: int = 7, usage_limit: Optional[int] = None) -> InvitationDomain:
    """
    Create invitation. Only instructor/admin allowed.
    Returns InvitationDomain.
    """
    try:
        classroom_model = ClassroomModel.objects.get(id=classroom_id)
    except ClassroomModel.DoesNotExist:
        raise NotFoundError("Classroom not found.")

    ensure_is_admin_or_instructor(requesting, classroom_model)

    # create unique invite_code
    invite_code = str(uuid4())

    # If model Invitation has usage_limit/used_count fields add them, else ignore
    inv_kwargs = dict(
        classroom=classroom_model,
        invite_code=invite_code,
        email=email,
        created_by=requesting.id,
        expires_on=timezone.now() + timedelta(days=expire_days),
        status="pending",
    )
    if hasattr(InvitationModel, "usage_limit"):
        inv_kwargs["usage_limit"] = usage_limit
        inv_kwargs["used_count"] = 0

    invitation_model = InvitationModel.objects.create(**inv_kwargs)
    return InvitationDomain.from_model(invitation_model)


@transaction.atomic
def accept_invitation(student: UserModel, invite_code: str) -> MembershipDomain:
    """
    Accept an invitation by invite_code. Creates membership and updates invitation usage/status.
    """
    try:
        invitation_model = InvitationModel.objects.select_for_update().get(invite_code=invite_code)
    except InvitationModel.DoesNotExist:
        raise NotFoundError("Invitation not found.")

    # Check classroom status
    try:
        classroom = invitation_model.classroom
    except Exception:
        raise NotFoundError("Classroom for invitation not found.")

    if classroom.status != "active":
        raise InvalidOperation("Cannot accept invitation for non-active classroom.")

    invitation_domain = InvitationDomain.from_model(invitation_model)
    if not invitation_domain.is_valid():
        # sync model status if needed
        if hasattr(invitation_model, "status"):
            invitation_model.status = "expired"
            invitation_model.save(update_fields=["status"])
        raise InvalidOperation("Invitation is not valid or has expired.")

    # If invitation has email bound, enforce it
    if getattr(invitation_model, "email", None) and (student.email.lower() != invitation_model.email.lower()):
        raise PermissionDenied("This invitation is not for your email.")

    # Prevent duplicate membership
    if MembershipModel.objects.filter(classroom=classroom, student=student, is_active=True).exists():
        raise ConflictError("User already member of the classroom.")

    membership_model = MembershipModel.objects.create(classroom=classroom, student=student, role="student")

    # update invitation usage/status
    if hasattr(invitation_model, "used_count"):
        invitation_model.used_count = (getattr(invitation_model, "used_count") or 0) + 1
        usage_limit = getattr(invitation_model, "usage_limit", None)
        if usage_limit is not None and invitation_model.used_count >= usage_limit:
            invitation_model.status = "expired"
        invitation_model.save(update_fields=["used_count", "status"])
    else:
        # mark accepted if possible
        if hasattr(invitation_model, "status"):
            invitation_model.status = "accepted"
            invitation_model.save(update_fields=["status"])

    return MembershipDomain.from_model(membership_model)


@transaction.atomic
def revoke_invitation(requesting: UserModel, invitation_id: int) -> InvitationDomain:
    """
    Revoke a pending invitation. Only instructor/admin that created or admin can revoke.
    """
    try:
        invitation_model = InvitationModel.objects.select_for_update().get(id=invitation_id)
    except InvitationModel.DoesNotExist:
        raise NotFoundError("Invitation not found.")

    # permission: admin can revoke any; instructor that created it can revoke
    if not (requesting.is_staff or invitation_model.created_by == requesting.id):
        raise PermissionDenied("Not authorized to revoke this invitation.")

    if getattr(invitation_model, "status", "").lower() != "pending":
        raise InvalidOperation("Only pending invitations can be revoked.")

    invitation_model.status = "expired"
    # if model has updated_on or modified timestamp, it will update in save()
    invitation_model.save(update_fields=["status"])
    return InvitationDomain.from_model(invitation_model)