from typing import Optional, Callable
from django.db import transaction

from account.models import UserModel
from classroom.models import ClassroomModel, MembershipModel, InvitationModel
from classroom.domains.class_domain import MembershipDomain, InvitationDomain
from classroom.apis.permissions import PermissionDenied, ConflictError, NotFoundError, InvalidOperation, ensure_is_admin_or_instructor



@transaction.atomic
def join_classroom(student: UserModel, classroom_id: int, *, invite_code: Optional[str] = None,
                   check_pending_lessons: Optional[Callable[[int, int], int]] = None) -> MembershipDomain:
    """
    Student joins a classroom:
      - If invite_code is provided, validate it and create membership.
      - If no invite_code, attempt open-join (class must be active).
    check_pending_lessons: optional callback (user_id, classroom_id) -> pending_count (int)
    """
    try:
        classroom_model = ClassroomModel.objects.select_for_update().get(id=classroom_id)
    except ClassroomModel.DoesNotExist:
        raise NotFoundError("Classroom not found.")

    # If classroom is not active, refuse
    if classroom_model.status != "active":
        raise InvalidOperation("Cannot join non-active classroom.")

    # If invite_code provided -> validate invitation
    if invite_code:
        try:
            invitation_model = InvitationModel.objects.select_for_update().get(invite_code=invite_code, classroom=classroom_model)
        except InvitationModel.DoesNotExist:
            raise NotFoundError("Invitation not found.")

        # Build domain to use domain rule
        invitation_domain = InvitationDomain.from_model(invitation_model)
        if not invitation_domain.is_valid():
            # sync model status if necessary (model may set expired in save)
            invitation_model.status = getattr(invitation_model, "status", "expired")
            invitation_model.save(update_fields=["status"])
            raise InvalidOperation("Invitation is not valid or has expired.")

        # Ensure email match if invitation has email
        if getattr(invitation_model, "email", None):
            # if student's email doesn't match the invitation email, disallow
            if student.email.lower() != invitation_model.email.lower():
                raise PermissionDenied("Invitation email does not match your account email.")

        # create membership if not exists
        if MembershipModel.objects.filter(classroom=classroom_model, student=student, is_active=True).exists():
            raise ConflictError("User is already a member of the classroom.")

        membership_model = MembershipModel.objects.create(
            classroom=classroom_model,
            student=student,
            role="student",
        )

        # increment usage_count if model has field
        if hasattr(invitation_model, "used_count"):
            # store numeric if exists
            invitation_model.used_count = (getattr(invitation_model, "used_count") or 0) + 1
            # expire if over limit
            usage_limit = getattr(invitation_model, "usage_limit", None)
            if usage_limit is not None and invitation_model.used_count >= usage_limit:
                invitation_model.status = "expired"
            invitation_model.save(update_fields=["used_count", "status"])
        else:
            # fallback: leave as-is, maybe mark accepted
            if hasattr(invitation_model, "status"):
                invitation_model.status = "accepted"
                invitation_model.save(update_fields=["status"])

        return MembershipDomain.from_model(membership_model)

    # No invite code -> open join (policy: allow only if classroom is active)
    # Optionally you can require instructors to approve requests; here we allow direct join
    if MembershipModel.objects.filter(classroom=classroom_model, student=student, is_active=True).exists():
        raise ConflictError("User is already a member of the classroom.")

    # check pending lessons if any policy requires students to not have unfinished lessons before join? 
    # Usually this rule applies to leaving, not joining — keep for completeness if provided
    if check_pending_lessons:
        pending = check_pending_lessons(student.id, classroom_model.id)
        if pending and pending > 0:
            # you could either allow join or disallow; we disallow here to be strict
            raise InvalidOperation("You have pending items preventing joining this classroom.")

    membership_model = MembershipModel.objects.create(
        classroom=classroom_model,
        student=student,
        role="student",
    )
    return MembershipDomain.from_model(membership_model)


@transaction.atomic
def leave_classroom(student: UserModel, classroom_id: int, *,
                    check_pending_lessons: Optional[Callable[[int, int], int]] = None) -> None:
    """
    Member leaves the classroom. Student cannot leave if they have pending lessons/quizzes.
    check_pending_lessons: callback(user_id, classroom_id) -> pending_count
    """
    try:
        membership_model = MembershipModel.objects.select_for_update().get(classroom_id=classroom_id, student=student, is_active=True)
    except MembershipModel.DoesNotExist:
        raise NotFoundError("Active membership not found.")

    # If student and pending lessons exist -> block
    if membership_model.role.lower() == "student" and check_pending_lessons:
        pending = check_pending_lessons(student.id, membership_model.classroom_id)
        if pending and pending > 0:
            raise InvalidOperation("You have unfinished lessons/quizzes and cannot leave the classroom.")

    # If instructor, ensure not the last instructor
    if membership_model.role.lower() in ("instructor", "co-instructor", "co_instructor"):
        # count active instructors
        total_instructors = MembershipModel.objects.filter(
            classroom_id=membership_model.classroom_id, role__iexact="instructor", is_active=True
        ).count()
        if total_instructors <= 1:
            raise InvalidOperation("Cannot remove the last instructor from the classroom.")

    # Soft remove membership
    membership_model.is_active = False
    membership_model.save(update_fields=["is_active"])
    return


@transaction.atomic
def assign_instructor(requesting: UserModel, classroom_id: int, user_id: int) -> MembershipDomain:
    """
    Assign a user as instructor to the classroom. Admin or existing instructor can do this.
    If user is already a member with different role, update role.
    """
    try:
        classroom_model = ClassroomModel.objects.select_for_update().get(id=classroom_id)
    except ClassroomModel.DoesNotExist:
        raise NotFoundError("Classroom not found.")

    ensure_is_admin_or_instructor(requesting, classroom_model)

    try:
        user = UserModel.objects.get(id=user_id)
    except UserModel.DoesNotExist:
        raise NotFoundError("User not found.")

    membership_qs = MembershipModel.objects.filter(classroom=classroom_model, student=user)
    if membership_qs.exists():
        membership = membership_qs.select_for_update().first()
        if not membership.is_active:
            membership.is_active = True
        membership.role = "instructor"
        membership.save(update_fields=["role", "is_active"])
    else:
        membership = MembershipModel.objects.create(classroom=classroom_model, student=user, role="instructor")

    return MembershipDomain.from_model(membership)


@transaction.atomic
def remove_member(requesting: UserModel, classroom_id: int, member_id: int) -> None:
    """
    Remove a member from classroom. Instructor may remove students; admin can remove anyone.
    Instructor cannot remove the last instructor.
    """
    try:
        classroom_model = ClassroomModel.objects.select_for_update().get(id=classroom_id)
    except ClassroomModel.DoesNotExist:
        raise NotFoundError("Classroom not found.")

    ensure_is_admin_or_instructor(requesting, classroom_model)

    try:
        membership_model = MembershipModel.objects.select_for_update().get(id=member_id, classroom=classroom_model, is_active=True)
    except MembershipModel.DoesNotExist:
        raise NotFoundError("Membership not found.")

    # If the membership to remove is instructor, ensure not last
    if membership_model.role.lower() in ("instructor", "co-instructor", "co_instructor"):
        total_instructors = MembershipModel.objects.filter(
            classroom=classroom_model, role__iexact="instructor", is_active=True
        ).count()
        if total_instructors <= 1:
            raise InvalidOperation("Cannot remove the last instructor.")

    # Allow instructor to remove students or admins to remove anyone
    # If requester is instructor, disallow removing other instructors (unless admin)
    if not requesting.is_staff and membership_model.role.lower() in ("instructor", "co-instructor", "co_instructor"):
        raise PermissionDenied("Only admin can remove other instructors.")

    membership_model.is_active = False
    membership_model.save(update_fields=["is_active"])
    return