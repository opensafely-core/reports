import factory

from gateway.models import User
from reports.models import Category, Link, Org, Report


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"category-{n}")


class LinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Link

    report = factory.SubFactory("tests.factories.ReportFactory")


class OrgFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Org

    name = factory.Sequence(lambda n: f"org-{n}")
    slug = factory.Sequence(lambda n: f"org-{n}")


class ReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Report

    category = factory.SubFactory("tests.factories.CategoryFactory")
    created_by = factory.SubFactory("tests.factories.UserFactory")
    org = factory.SubFactory("tests.factories.OrgFactory")
    updated_by = factory.SubFactory("tests.factories.UserFactory")

    title = factory.Sequence(lambda n: f"report-{n}")
    description = factory.Sequence(lambda n: f"report-{n}")
    publication_date = factory.Faker("date_time")
    repo = "test-repo"
    report_html_file_path = "report.html"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user-{n}")
