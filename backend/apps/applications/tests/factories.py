import factory
from django.contrib.auth import get_user_model

from apps.applications.models import Application, Tag

User = get_user_model()


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f"tag-{n}")
    color = "#3B82F6"
    user = factory.LazyAttribute(lambda o: User.objects.first())


class ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Application

    user = factory.LazyAttribute(lambda o: User.objects.first())
    company = factory.Faker("company")
    role = factory.Faker("job")
    job_type = "internship"
    status = "saved"
    priority = "medium"
