import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models

from django_socio_grpc.mixins import (
    CreateModelMixin,
    ListModelMixin,
    StreamModelMixin,
    get_default_grpc_messages,
    get_default_grpc_methods,
)


class UnitTestModel(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=20)
    text = models.CharField(max_length=100, null=True)

    class Meta:
        grpc_messages = {
            **get_default_grpc_messages("UnitTestModel"),
            **StreamModelMixin.get_default_message("UnitTestModel"),
        }

        grpc_methods = {
            **get_default_grpc_methods("UnitTestModel"),
            **StreamModelMixin.get_default_method("UnitTestModel"),
        }


class ForeignModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    class Meta:
        ###################################
        # Simulate a retrieve by name     #
        # Simulate a read only model      #
        ###################################
        grpc_messages = {
            **CreateModelMixin.get_default_message("ForeignModel"),
            **ListModelMixin.get_default_message("ForeignModel", pagination=True),
            "ForeignModelRetrieveRequestCustom": ["name"],
        }
        grpc_methods = {
            **ListModelMixin.get_default_method("ForeignModel"),
            "Retrieve": {
                "request": {
                    "is_stream": False,
                    "message": "ForeignModelRetrieveRequestCustom",
                },
                "response": {
                    "is_stream": False,
                    "message": "ForeignModelRetrieveRequestCustom",
                },
            },
        }


class ManyManyModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)


class SlugTestModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    special_number = models.IntegerField(null=True, blank=True)

    class Meta:
        grpc_messages = {}
        grpc_methods = {}


class RelatedFieldModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    foreign = models.ForeignKey(
        ForeignModel,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="related",
    )
    many_many = models.ManyToManyField(ManyManyModel, blank=True, related_name="relateds")

    slug_test_model = models.ForeignKey(
        SlugTestModel,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="related",
    )
    slug_many_many = models.ManyToManyField(
        ManyManyModel, blank=True, related_name="relateds_slugs"
    )

    many_many_foreigns = models.ManyToManyField(
        "RelatedFieldModel", blank=True, related_name="related_foreigns"
    )

    def custom_field_name(self):
        return "custom_field_name"

    class Meta:
        ###############################################################
        # Manually add many_many to serializer and a custom field     #
        ###############################################################
        grpc_messages = {
            **get_default_grpc_messages("RelatedFieldModel"),
            "RelatedFieldModelListResponse": [
                "uuid",
                "foreign",
                "many_many",
                "__custom__string__custom_field_name__",
                "__custom__repeated string__list_custom_field_name__",
            ],
        }

        grpc_methods = {
            **get_default_grpc_methods("RelatedFieldModel"),
            "List": {
                "request": {
                    "message": "RelatedFieldModelListRequest",
                },
                "response": {
                    "message": "RelatedFieldModelListResponse",
                },
            },
        }


class NotDisplayedModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    class Meta:
        grpc_messages = {}
        grpc_methods = {}


class SpecialFieldsModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meta_datas = models.JSONField(
        default=dict,
        blank=True,
    )
    list_datas = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True,
    )
    binary = models.BinaryField(default=None)


class ImportStructEvenInArrayModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    this_is_crazy = ArrayField(
        models.JSONField(
            default=dict,
            blank=True,
        ),
        default=list,
        blank=True,
    )

    class Meta:
        grpc_messages = {"ImportStructEvenInArrayModel": "__all__"}
        grpc_methods = {}


class SlugReverseTestModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=False)
    related_field = models.ForeignKey(
        RelatedFieldModel,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="slug_reverse_test_model",
    )

    class Meta:
        grpc_messages = {}
        grpc_methods = {}


class RecursiveTestModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.CASCADE, related_name="children"
    )
