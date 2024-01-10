from typing import List, Optional

import pytest
from django.db import models
from rest_framework import serializers

from django_socio_grpc import proto_serializers
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.protobuf import ProtoComment, ProtoRegistrationError
from django_socio_grpc.protobuf.proto_classes import (
    EmptyMessage,
    FieldCardinality,
    ProtoField,
    ProtoMessage,
    RequestProtoMessage,
    ResponseProtoMessage,
    StructMessage,
)
from django_socio_grpc.services import Service
from django_socio_grpc.tests.fakeapp.models import RelatedFieldModel
from django_socio_grpc.tests.fakeapp.serializers import (
    BasicProtoListChildSerializer,
    BasicServiceSerializer,
    RelatedFieldModelSerializer,
)

from django_socio_grpc import generics, mixins


class MyDefaultValueModel(models.Model):
    string_required = models.CharField(max_length=20)
    string_blank = models.CharField(max_length=20, blank=True)
    string_nullable = models.CharField(max_length=20, null=True)
    string_default = models.CharField(max_length=20, default="default")
    string_required_but_serializer_default = models.CharField(max_length=20)
    int_required = models.IntegerField()
    int_nullable = models.IntegerField(null=True)
    int_default = models.IntegerField(default=5)
    int_required_but_serializer_default = models.IntegerField()
    boolean_required = models.BooleanField()
    boolean_default_false = models.BooleanField(default=False)
    boolean_default_true = models.BooleanField(default=True)
    boolean_required_but_serializer_default = models.IntegerField()



class MyDefaultSerializer(proto_serializers.ModelProtoSerializer):
    string_required_but_serializer_default = serializers.CharField(default="default_serializer")
    int_required_but_serializer_default = serializers.IntegerField(default=10)
    boolean_required_but_serializer_default = serializers.CharField(default=False)

    class Meta:
        model = MyDefaultValueModel
        fields = "__all__"



class UnitTestModelService(generics.AsyncModelService):
    queryset = MyDefaultValueModel.objects.all().order_by("id")
    serializer_class = MyDefaultSerializer


class TestDefaultValue:
    # FROM_FIELD
    def test_from_field_string(self):
        ser = MyDefaultSerializer()
        field = ser.fields["string_required"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "string_required"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.NONE

        # ---------------------------------

        ser = MyDefaultSerializer()
        field = ser.fields["string_blank"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "string_blank"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

        # ---------------------------------

        ser = MyDefaultSerializer()
        field = ser.fields["string_nullable"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "string_nullable"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

        # ---------------------------------

        ser = MyDefaultSerializer()
        field = ser.fields["string_default"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "string_default"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

        # ---------------------------------

        ser = MyDefaultSerializer()
        field = ser.fields["string_required_but_serializer_default"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "string_required_but_serializer_default"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL