from typing import Optional
from django.db import transaction

from account.models import UserModel
from school.models import ClassroomModel, MembershipModel
from school.domains.class_domain import ClassroomDomain
from school.services.exceptions import PermissionDenied, ConflictError, NotFoundError, InvalidOperation
from school.services.validators import ensure_is_admin_or_instructor, ensure_is_admin



@transaction.atomic
def create_classroom(instructor: UserModel, name: str, description: Optional[str] = None) -> ClassroomDomain:
    """Create a classroom and add instructor as member."""
    # Basic permission: only instructor/admin can create class (you can relax this if needed)
    if not (instructor.is_staff or instructor.role == "instructor"):
        raise PermissionDenied("Only instructors or admins can create a classroom.")

    # Ensure unique name (class_name)
    if ClassroomModel.objects.filter(class_name__iexact=name).exists():
        raise ConflictError(f"Classroom with name '{name}' already exists.")

    classroom_model = ClassroomModel.objects.create(
        class_name=name,
        created_by=instructor.id,
        status="active",
    )

    # create membership
    MembershipModel.objects.create(
        classroom=classroom_model,
        student=instructor,
        role="instructor",
    )

    return ClassroomDomain.from_model(classroom_model)


@transaction.atomic
def archive_classroom(requesting: UserModel, classroom_id: int) -> ClassroomDomain:
    """
    Archive the classroom (soft-close). Only instructor or admin can archive.
    """
    try:
        classroom_model = ClassroomModel.objects.select_for_update().get(id=classroom_id)
    except ClassroomModel.DoesNotExist:
        raise NotFoundError("Classroom not found.")

    ensure_is_admin_or_instructor(requesting, classroom_model)

    if classroom_model.status != "active":
        raise InvalidOperation("Only active classrooms can be archived.")

    classroom_model.status = "archived"
    classroom_model.save(update_fields=["status", "updated_on"])

    return ClassroomDomain.from_model(classroom_model)


@transaction.atomic
def restore_classroom(requesting: UserModel, classroom_id: int) -> ClassroomDomain:
    """
    Restore an archived classroom to active. Only admin or instructor allowed.
    """
    try:
        classroom_model = ClassroomModel.objects.select_for_update().get(id=classroom_id)
    except ClassroomModel.DoesNotExist:
        raise NotFoundError("Classroom not found.")
    
    ensure_is_admin_or_instructor(requesting, ClassroomModel)

    if classroom_model.status != "archived":
        raise InvalidOperation("Only archived classrooms can be restored.")
    classroom_model.status = "active"
    classroom_model.save(update_fields=["status", "updated_on"])
    return ClassroomDomain.from_model(classroom_model)


@transaction.atomic
def update_classroom(requesting: UserModel, classroom_id: int, *, name: Optional[str] = None,
                     description: Optional[str] = None) -> ClassroomDomain:
    """
    Update classroom metadata. Only instructor/admin allowed.
    """
    try:
        classroom_model = ClassroomModel.objects.select_for_update().get(id=classroom_id)
    except ClassroomModel.DoesNotExist:
        raise NotFoundError("Classroom not found.")

    ensure_is_admin_or_instructor(requesting, classroom_model)

    if name:
        # ensure uniqueness of name
        if ClassroomModel.objects.filter(class_name__iexact=name).exclude(id=classroom_id).exists():
            raise ConflictError("Another classroom with this name already exists.")
        classroom_model.class_name = name
    if description is not None:
        # optional field; set even if empty string
        classroom_model.description = description

    classroom_model.save()
    return ClassroomDomain.from_model(classroom_model)


@transaction.atomic
def delete_classroom(requesting: UserModel, classroom_id: int, *, soft_delete: bool = True) -> None:
    """
    Delete classroom. Default is soft-delete (set status='deleted').
    Only admin can hard-delete. Instructors may soft-delete if permitted.
    Returns None.
    """
    try:
        classroom_model = ClassroomModel.objects.select_for_update().get(id=classroom_id)
    except ClassroomModel.DoesNotExist:
        raise NotFoundError("Classroom not found.")

    if soft_delete:
        ensure_is_admin_or_instructor(requesting, classroom_model)
        classroom_model.status = "deleted"
        classroom_model.save(update_fields=["status", "updated_on"])
        return

    # hard delete
    ensure_is_admin(requesting)
    classroom_model.delete()
    return