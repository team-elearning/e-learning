from datetime import datetime
from typing import TypedDict, Optional

from classroom.models import ClassroomModel, MembershipModel, InvitationModel



class ClassDict(TypedDict):
    id: Optional[int]
    class_name: str
    status: str
    created_by: int
    created_on: datetime
    updated_on: datetime

class MembershipDict(TypedDict):
    id: Optional[int]
    classroom_id: int
    user_id: int
    role: str
    joined_on: datetime
    is_active: bool

class InvitationDict(TypedDict):
    id: Optional[int]
    classroom_id: int
    invite_code: str
    created_by: int
    email: str
    expires_on: datetime
    status: str
    created_on: datetime
    usage_limit: Optional[int]
    used_count: int


class ClassroomDomain:
    """Entity representing a Classroom."""

    VALID_STATUSES = ["active", "archived", "deleted"]

    def __init__(self, id: Optional[int], name: str, created_by: int,
                 description: Optional[str] = None,
                 created_on: Optional[datetime] = None,
                 updated_on: Optional[datetime] = None,
                 status: str = "active"):
        self.id = id
        self.name = name
        self.description = description
        self.created_by = created_by
        self.created_on = created_on or datetime.astimezone()
        self.updated_on = updated_on or datetime.astimezone()
        self.status = status
        self.validate()


    # --- Validation ---
    def validate(self) -> None:
        if not self.name:
            raise ValueError("Classroom name is required.")
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}")


    # --- Serialization ---
    def to_dict(self) -> ClassDict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by,
            "created_on": self.created_on,
            "updated_on": self.updated_on,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: ClassDict) -> "ClassroomDomain":
        return cls(**data)


    # --- Mapping methods ---
    @classmethod
    def from_model(cls, class_model:ClassroomModel) -> "ClassroomDomain": # model -> domain
        """Convert a UserModel instance → UserDomain."""
        return cls(
            id=class_model.id,
            username=class_model.class_name,
            created_by = class_model.created_by,
            created_on = class_model.created_on,
            updated_on = class_model.updated_on,
            status = class_model.status,
        )


    # --- Business rules ---
    def can_accept_new_members(self) -> bool:
        """Archived classrooms cannot accept new members."""
        return self.status == "active"
    
    def ensure_has_instructor(self, memberships: list["MembershipDomain"]) -> None:
        """Ensure at least one instructor exists in this classroom."""
        instructors = [m for m in memberships if m.role in ["instructor", "co_instructor"] and m.is_active]
        if len(instructors) == 0:
            raise ValueError("Classroom must have at least one instructor.")
    


class MembershipDomain:
    """Value object representing a user membership inside a classroom."""

    VALID_ROLES = ["student", "instructor", "co_instructor"]

    def __init__(self, id: Optional[int], classroom_id: int, user_id: int,
                 role: str, joined_on: Optional[datetime] = None,
                 is_active: bool = True):
        self.id = id
        self.classroom_id = classroom_id
        self.user_id = user_id
        self.role = role
        self.joined_on = joined_on or datetime.astimezone()
        self.is_active = is_active
        self.validate()


    # --- Validation ---
    def validate(self) -> None:
        if self.role not in self.VALID_ROLES:
            raise ValueError(f"Invalid role: {self.role}")


    # --- Serialization ---
    def to_dict(self) -> MembershipDict:
        return {
            "id": self.id,
            "classroom_id": self.classroom_id,
            "user_id": self.user_id,
            "role": self.role,
            "joined_on": self.joined_on,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: MembershipDict) -> "MembershipDomain":
        return cls(**data)
    

    # --- Mapping methods ---
    @classmethod
    def from_model(cls, membership_model: MembershipModel) -> "MembershipDomain":
        user_id = getattr(m, "student_id", getattr(m, "user_id", None))
        return cls(
            id=membership_model.id,
            classroom_id=membership_model.classroom,
            user_id=membership_model.student,
            role=membership_model.role.lower() if membership_model.role else "student",
            joined_on=membership_model.joined_on,
            is_active=membership_model.is_active,
    )


    # --- Business rules ---
    def can_leave_classroom(self, pending_lessons: int) -> bool:
        """Student cannot leave if they have unfinished lessons/quizzes."""
        if self.role == "student" and pending_lessons > 0:
            return False
        return True

    def can_be_removed(self, total_instructors: int) -> bool:
        """Instructor cannot be removed if they are the last one."""
        if self.role in ["instructor", "co_instructor"] and total_instructors <= 1:
            return False
        return True
    


class InvitationDomain:
    """Entity representing a Classroom invitation."""
    VALID_STATUSES = ["pending", "accepted", "expired"]

    def __init__(self, id: Optional[int], classroom_id: int, invite_code: str,
                 created_by: int, expires_on: datetime,
                 status: str = "pending",
                 email: Optional[str] = None,
                 usage_limit: Optional[int] = None,
                 used_count: int = 0):
        self.id = id
        self.classroom_id = classroom_id
        self.invite_code = invite_code
        self.created_by = created_by
        self.expires_on = expires_on
        self.status = status
        self.email = email
        self.usage_limit = usage_limit
        self.used_count = used_count
        self.validate()


    # --- Validation ---
    def validate(self) -> None:
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}")
        if self.expires_on <= datetime.utcnow():
            raise ValueError("Invitation expiry date must be in the future.")
        if self.usage_limit is not None and self.usage_limit < 1:
            raise ValueError("Usage limit must be positive if provided.")
        

    # --- Serialization ---
    def to_dict(self) -> InvitationDict:
        return {
            "id": self.id,
            "classroom_id": self.classroom_id,
            "invite_code": self.invite_code,
            "created_by": self.created_by,
            "expires_on": self.expires_on,
            "status": self.status,
            "email": self.email,
            "usage_limit": self.usage_limit,
            "used_count": self.used_count,
        }

    @classmethod
    def from_dict(cls, data: InvitationDict) -> "InvitationDomain":
        return cls(**data)
    

    # --- Mapping methods ---
    @classmethod
    def from_model(cls, invitation_model: InvitationModel) -> "InvitationDomain":
        # Support optional usage_limit/used_count fields if present on model
        usage_limit = getattr(invitation_model, "usage_limit", None)
        used_count = getattr(invitation_model, "used_count", 0)
        return cls(
            id=invitation_model.id,
            classroom_id=invitation_model.classroom,
            invite_code=invitation_model.invite_code,
            email=invitation_model.email,
            created_by=invitation_model.created_by,
            created_on=invitation_model.created_on,
            expires_on=invitation_model.expires_on,
            status=invitation_model.status.lower() if invitation_model.status else "pending",
            usage_limit=invitation_model.usage_limit,
            used_count=invitation_model.used_count,
    )

    # --- Business rules ---
    def is_valid(self) -> bool:
        if self.status != "pending":
            return False
        if datetime.astimezone() > self.expires_on:
            return False
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        return True
    
    def mark_used(self) -> None:
        """Increment usage count and expire if over limit."""
        if not self.is_valid():
            raise ValueError("Cannot use an invalid or expired invitation.")
        self.used_count += 1
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            self.status = "expired"



