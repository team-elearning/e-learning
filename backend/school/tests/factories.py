# school/tests/factories.py
from factories import factory
from django.utils import timezone
from school.models import School, Classroom, Enrollment

class SchoolFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = School

    name = factory.Sequence(lambda n: f"School {n}")
    address = factory.Faker("address")
    phone = factory.Faker("phone_number")
    created_on = factory.LazyFunction(timezone.now)

class ClassroomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Classroom

    school = factory.SubFactory(SchoolFactory)
    name = factory.Sequence(lambda n: f"Class {n}")
    grade = factory.Iterator(["1", "2", "3", "4", "5"])
    metadata = {}

class EnrollmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Enrollment

    student = factory.SubFactory("account.tests.factories.UserFactory", role="student")
    classroom = factory.SubFactory(ClassroomFactory)
    joined_on = factory.LazyFunction(timezone.now)
    is_active = True
