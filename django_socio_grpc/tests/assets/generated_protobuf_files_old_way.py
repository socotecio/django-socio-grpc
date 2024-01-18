SIMPLE_MODEL_GENERATED = """syntax = "proto3";

package myproject.unittestmodel;

import "google/protobuf/empty.proto";

service UnitTestModelController {
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModel) returns (UnitTestModel) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModel) {}
    rpc Update(UnitTestModel) returns (UnitTestModel) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModel) {}
}

message UnitTestModel {
    int32 id = 1;
    string title = 2;
    string text = 3;
}

message UnitTestModelListRequest {
}

message UnitTestModelListResponse {
    repeated UnitTestModel results = 1;
    int32 count = 2;
}

message UnitTestModelRetrieveRequest {
    int32 id = 1;
}

message UnitTestModelDestroyRequest {
    int32 id = 1;
}

message UnitTestModelStreamRequest {
}

"""

SIMPLE_APP_MODEL_NO_GENERATION = """syntax = "proto3";

package myproject.fakeapp;

"""

SIMPLE_APP_MODEL_GENERATED = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";

service UnitTestModelController {
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModel) returns (UnitTestModel) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModel) {}
    rpc Update(UnitTestModel) returns (UnitTestModel) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModel) {}
}

message UnitTestModel {
    int32 id = 1;
    string title = 2;
    string text = 3;
}

message UnitTestModelListRequest {
}

message UnitTestModelListResponse {
    repeated UnitTestModel results = 1;
    int32 count = 2;
}

message UnitTestModelRetrieveRequest {
    int32 id = 1;
}

message UnitTestModelDestroyRequest {
    int32 id = 1;
}

message UnitTestModelStreamRequest {
}

"""

ALL_APP_GENERATED = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";
import "google/protobuf/struct.proto";

service UnitTestModelController {
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModel) returns (UnitTestModel) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModel) {}
    rpc Update(UnitTestModel) returns (UnitTestModel) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModel) {}
}

service ForeignModelController {
    rpc List(ForeignModelListRequest) returns (ForeignModelListResponse) {}
    rpc Retrieve(ForeignModelRetrieveRequestCustom) returns (ForeignModelRetrieveRequestCustom) {}
}

service ManyManyModelController {
    rpc List(ManyManyModelListRequest) returns (ManyManyModelListResponse) {}
    rpc Create(ManyManyModel) returns (ManyManyModel) {}
    rpc Retrieve(ManyManyModelRetrieveRequest) returns (ManyManyModel) {}
    rpc Update(ManyManyModel) returns (ManyManyModel) {}
    rpc Destroy(ManyManyModelDestroyRequest) returns (google.protobuf.Empty) {}
}

service RelatedFieldModelController {
    rpc List(RelatedFieldModelListRequest) returns (RelatedFieldModelListResponse) {}
    rpc Create(RelatedFieldModel) returns (RelatedFieldModel) {}
    rpc Retrieve(RelatedFieldModelRetrieveRequest) returns (RelatedFieldModel) {}
    rpc Update(RelatedFieldModel) returns (RelatedFieldModel) {}
    rpc Destroy(RelatedFieldModelDestroyRequest) returns (google.protobuf.Empty) {}
}

service SpecialFieldsModelController {
    rpc List(SpecialFieldsModelListRequest) returns (SpecialFieldsModelListResponse) {}
    rpc Create(SpecialFieldsModel) returns (SpecialFieldsModel) {}
    rpc Retrieve(SpecialFieldsModelRetrieveRequest) returns (SpecialFieldsModel) {}
    rpc Update(SpecialFieldsModel) returns (SpecialFieldsModel) {}
    rpc Destroy(SpecialFieldsModelDestroyRequest) returns (google.protobuf.Empty) {}
}

service RecursiveTestModelController {
    rpc List(RecursiveTestModelListRequest) returns (RecursiveTestModelListResponse) {}
    rpc Create(RecursiveTestModel) returns (RecursiveTestModel) {}
    rpc Retrieve(RecursiveTestModelRetrieveRequest) returns (RecursiveTestModel) {}
    rpc Update(RecursiveTestModel) returns (RecursiveTestModel) {}
    rpc Destroy(RecursiveTestModelDestroyRequest) returns (google.protobuf.Empty) {}
}

service DefaultValueModelController {
    rpc List(DefaultValueModelListRequest) returns (DefaultValueModelListResponse) {}
    rpc Create(DefaultValueModel) returns (DefaultValueModel) {}
    rpc Retrieve(DefaultValueModelRetrieveRequest) returns (DefaultValueModel) {}
    rpc Update(DefaultValueModel) returns (DefaultValueModel) {}
    rpc Destroy(DefaultValueModelDestroyRequest) returns (google.protobuf.Empty) {}
}

message UnitTestModel {
    int32 id = 1;
    string title = 2;
    string text = 3;
}

message UnitTestModelListRequest {
}

message UnitTestModelListResponse {
    repeated UnitTestModel results = 1;
    int32 count = 2;
}

message UnitTestModelRetrieveRequest {
    int32 id = 1;
}

message UnitTestModelDestroyRequest {
    int32 id = 1;
}

message UnitTestModelStreamRequest {
}

message ForeignModel {
    string uuid = 1;
    string name = 2;
}

message ForeignModelListRequest {
}

message ForeignModelListResponse {
    repeated ForeignModel results = 1;
    int32 count = 2;
}

message ForeignModelRetrieveRequestCustom {
    string name = 1;
}

message ManyManyModel {
    string uuid = 1;
    string name = 2;
}

message ManyManyModelListRequest {
}

message ManyManyModelListResponse {
    repeated ManyManyModel results = 1;
    int32 count = 2;
}

message ManyManyModelRetrieveRequest {
    string uuid = 1;
}

message ManyManyModelDestroyRequest {
    string uuid = 1;
}

message RelatedFieldModel {
    string uuid = 1;
    string foreign = 2;
    string slug_test_model = 3;
}

message RelatedFieldModelListRequest {
}

message RelatedFieldModelListResponse {
    string uuid = 1;
    string foreign = 2;
    repeated string many_many = 3;
    string custom_field_name = 4;
    repeated string list_custom_field_name = 5;
}

message RelatedFieldModelRetrieveRequest {
    string uuid = 1;
}

message RelatedFieldModelDestroyRequest {
    string uuid = 1;
}

message SpecialFieldsModel {
    string uuid = 1;
    google.protobuf.Struct meta_datas = 2;
    repeated int32 list_datas = 3;
    bytes binary = 4;
}

message SpecialFieldsModelListRequest {
}

message SpecialFieldsModelListResponse {
    repeated SpecialFieldsModel results = 1;
    int32 count = 2;
}

message SpecialFieldsModelRetrieveRequest {
    string uuid = 1;
}

message SpecialFieldsModelDestroyRequest {
    string uuid = 1;
}

message ImportStructEvenInArrayModel {
    string uuid = 1;
    repeated google.protobuf.Struct this_is_crazy = 2;
}

message RecursiveTestModel {
    string uuid = 1;
    string parent = 2;
}

message RecursiveTestModelListRequest {
}

message RecursiveTestModelListResponse {
    repeated RecursiveTestModel results = 1;
    int32 count = 2;
}

message RecursiveTestModelRetrieveRequest {
    string uuid = 1;
}

message RecursiveTestModelDestroyRequest {
    string uuid = 1;
}

message DefaultValueModel {
    string id = 1;
    string string_required = 2;
    string string_blank = 3;
    string string_nullable = 4;
    string string_default = 5;
    string string_default_and_blank = 6;
    string string_null_default_and_blank = 7;
    string string_required_but_serializer_default = 8;
    string string_default_but_serializer_default = 9;
    string string_nullable_default_but_serializer_default = 10;
    int32 int_required = 11;
    int32 int_nullable = 12;
    int32 int_default = 13;
    int32 int_required_but_serializer_default = 14;
    bool boolean_required = 15;
    bool boolean_nullable = 16;
    bool boolean_default_false = 17;
    bool boolean_default_true = 18;
    bool boolean_required_but_serializer_default = 19;
}

message DefaultValueModelListRequest {
}

message DefaultValueModelListResponse {
    repeated DefaultValueModel results = 1;
    int32 count = 2;
}

message DefaultValueModelRetrieveRequest {
    string id = 1;
}

message DefaultValueModelDestroyRequest {
    string id = 1;
}

"""

CUSTOM_APP_MODEL_GENERATED = """syntax = "proto3";

package myproject.fakeapp;

service ForeignModelController {
    rpc List(ForeignModelListRequest) returns (ForeignModelListResponse) {}
    rpc Retrieve(ForeignModelRetrieveRequestCustom) returns (ForeignModelRetrieveRequestCustom) {}
}

message ForeignModel {
    string uuid = 1;
    string name = 2;
}

message ForeignModelListRequest {
}

message ForeignModelListResponse {
    repeated ForeignModel results = 1;
    int32 count = 2;
}

message ForeignModelRetrieveRequestCustom {
    string name = 1;
}

"""

MODEL_WITH_M2M_GENERATED = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";

service RelatedFieldModelController {
    rpc List(RelatedFieldModelListRequest) returns (RelatedFieldModelListResponse) {}
    rpc Create(RelatedFieldModel) returns (RelatedFieldModel) {}
    rpc Retrieve(RelatedFieldModelRetrieveRequest) returns (RelatedFieldModel) {}
    rpc Update(RelatedFieldModel) returns (RelatedFieldModel) {}
    rpc Destroy(RelatedFieldModelDestroyRequest) returns (google.protobuf.Empty) {}
}

message RelatedFieldModel {
    string uuid = 1;
    string foreign = 2;
    string slug_test_model = 3;
}

message RelatedFieldModelListRequest {
}

message RelatedFieldModelListResponse {
    string uuid = 1;
    string foreign = 2;
    repeated string many_many = 3;
    string custom_field_name = 4;
    repeated string list_custom_field_name = 5;
}

message RelatedFieldModelRetrieveRequest {
    string uuid = 1;
}

message RelatedFieldModelDestroyRequest {
    string uuid = 1;
}

"""

MODEL_WITH_STRUCT_IMORT_IN_ARRAY = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/struct.proto";

message ImportStructEvenInArrayModel {
    string uuid = 1;
    repeated google.protobuf.Struct this_is_crazy = 2;
}

"""


SIMPLE_APP_MODEL_OLD_ORDER = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";

service UnitTestModelController {
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModel) returns (UnitTestModel) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModel) {}
    rpc Update(UnitTestModel) returns (UnitTestModel) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModel) {}
}

message UnitTestModel {
    int32 id = 1;
    string text = 2;
}

message UnitTestModelListRequest {
}

message UnitTestModelListResponse {
    repeated UnitTestModel results = 1;
    int32 count = 2;
}

message UnitTestModelRetrieveRequest {
    int32 id = 1;
}

message UnitTestModelDestroyRequest {
    int32 id = 1;
}

message UnitTestModelStreamRequest {
}

"""

SIMPLE_APP_MODEL_GENERATED_FROM_OLD_ORDER = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";

service UnitTestModelController {
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModel) returns (UnitTestModel) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModel) {}
    rpc Update(UnitTestModel) returns (UnitTestModel) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModel) {}
}

message UnitTestModel {
    int32 id = 1;
    string text = 2;
    string title = 3;
}

message UnitTestModelListRequest {
}

message UnitTestModelListResponse {
    repeated UnitTestModel results = 1;
    int32 count = 2;
}

message UnitTestModelRetrieveRequest {
    int32 id = 1;
}

message UnitTestModelDestroyRequest {
    int32 id = 1;
}

message UnitTestModelStreamRequest {
}

"""

APP_MODEL_WITH_CUSTOM_FIELD_OLD_ORDER = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";

service RelatedFieldModelController {
    rpc List(RelatedFieldModelListRequest) returns (RelatedFieldModelListResponse) {}
    rpc Create(RelatedFieldModel) returns (RelatedFieldModel) {}
    rpc Retrieve(RelatedFieldModelRetrieveRequest) returns (RelatedFieldModel) {}
    rpc Update(RelatedFieldModel) returns (RelatedFieldModel) {}
    rpc Destroy(RelatedFieldModelDestroyRequest) returns (google.protobuf.Empty) {}
}

message RelatedFieldModel {
    string uuid = 1;
}

message RelatedFieldModelListRequest {
}

message RelatedFieldModelListResponse {
    string uuid = 1;
    string custom_field_name = 2;
}

message RelatedFieldModelRetrieveRequest {
    string uuid = 1;
}

message RelatedFieldModelDestroyRequest {
    string uuid = 1;
}

"""

APP_MODEL_WITH_CUSTOM_FIELD_FROM_OLD_ORDER = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";

service RelatedFieldModelController {
    rpc List(RelatedFieldModelListRequest) returns (RelatedFieldModelListResponse) {}
    rpc Create(RelatedFieldModel) returns (RelatedFieldModel) {}
    rpc Retrieve(RelatedFieldModelRetrieveRequest) returns (RelatedFieldModel) {}
    rpc Update(RelatedFieldModel) returns (RelatedFieldModel) {}
    rpc Destroy(RelatedFieldModelDestroyRequest) returns (google.protobuf.Empty) {}
}

message RelatedFieldModel {
    string uuid = 1;
    string foreign = 2;
    string slug_test_model = 3;
}

message RelatedFieldModelListRequest {
}

message RelatedFieldModelListResponse {
    string uuid = 1;
    string custom_field_name = 2;
    string foreign = 3;
    repeated string many_many = 4;
    repeated string list_custom_field_name = 5;
}

message RelatedFieldModelRetrieveRequest {
    string uuid = 1;
}

message RelatedFieldModelDestroyRequest {
    string uuid = 1;
}

"""
