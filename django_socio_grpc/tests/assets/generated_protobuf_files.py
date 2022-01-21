SIMPLE_MODEL_GENERATED = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";

service UnitTestModelController {
    rpc ListWithExtraArgs(ListWithExtraArgsRequest) returns (UnitTestModelListExtraArgs) {}
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModel) returns (UnitTestModel) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModel) {}
    rpc Update(UnitTestModel) returns (UnitTestModel) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModel) {}
}

message ListWithExtraArgsRequest {
    bool archived = 1;
}

message UnitTestModelListExtraArgs {
    int32 count = 1;
    string query_fetched_datetime = 2;
    repeated UnitTestModel results = 3;
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
    rpc ListWithExtraArgs(ListWithExtraArgsRequest) returns (UnitTestModelListExtraArgs) {}
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModel) returns (UnitTestModel) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModel) {}
    rpc Update(UnitTestModel) returns (UnitTestModel) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModel) {}
}

service SyncUnitTestModelController {
    rpc ListWithExtraArgs(ListWithExtraArgsRequest) returns (UnitTestModelListExtraArgs) {}
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModel) returns (UnitTestModel) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModel) {}
    rpc Update(UnitTestModel) returns (UnitTestModel) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModel) {}
}

service ForeignModelController {
    rpc List(ForeignModelListRequest) returns (ForeignModelListResponse) {}
    rpc Retrieve(ForeignModelRetrieveRequest) returns (ForeignModel) {}
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

service ImportStructEvenInArrayModelController {
    rpc Create(ImportStructEvenInArrayModel) returns (ImportStructEvenInArrayModel) {}
}

message ListWithExtraArgsRequest {
    bool archived = 1;
}

message UnitTestModelListExtraArgs {
    int32 count = 1;
    string query_fetched_datetime = 2;
    repeated UnitTestModel results = 3;
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

message ForeignModelListRequest {
}

message ForeignModelListResponse {
    repeated ForeignModel results = 1;
    int32 count = 2;
}

message ForeignModel {
    string uuid = 1;
    string name = 2;
}

message ForeignModelRetrieveRequest {
    string name = 1;
}

message RelatedFieldModelListRequest {
}

message RelatedFieldModelListResponse {
    repeated RelatedFieldModel list_custom_field_name = 1;
    int32 count = 2;
}

message RelatedFieldModel {
    string uuid = 1;
    ForeignModel foreign_obj = 2;
    repeated ManyManyModel many_many_obj = 3;
    string custom_field_name = 4;
    string foreign = 5;
    repeated string many_many = 6;
}

message ManyManyModel {
    string uuid = 1;
    string name = 2;
}

message RelatedFieldModelRetrieveRequest {
    string uuid = 1;
}

message RelatedFieldModelDestroyRequest {
    string uuid = 1;
}

message SpecialFieldsModelListRequest {
}

message SpecialFieldsModelListResponse {
    repeated SpecialFieldsModel results = 1;
    int32 count = 2;
}

message SpecialFieldsModel {
    string uuid = 1;
    google.protobuf.Struct meta_datas = 2;
    repeated int32 list_datas = 3;
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

"""

CUSTOM_APP_MODEL_GENERATED = """syntax = "proto3";

package myproject.fakeapp;

service ForeignModelController {
    rpc List(ForeignModelListRequest) returns (ForeignModelListResponse) {}
    rpc Retrieve(ForeignModelRetrieveRequest) returns (ForeignModel) {}
}

message ForeignModelListRequest {
}

message ForeignModelListResponse {
    repeated ForeignModel results = 1;
    int32 count = 2;
}

message ForeignModel {
    string uuid = 1;
    string name = 2;
}

message ForeignModelRetrieveRequest {
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

message RelatedFieldModelListRequest {
}

message RelatedFieldModelListResponse {
    repeated RelatedFieldModel list_custom_field_name = 1;
    int32 count = 2;
}

message RelatedFieldModel {
    string uuid = 1;
    ForeignModel foreign_obj = 2;
    repeated ManyManyModel many_many_obj = 3;
    string custom_field_name = 4;
    string foreign = 5;
    repeated string many_many = 6;
}

message ForeignModel {
    string uuid = 1;
    string name = 2;
}

message ManyManyModel {
    string uuid = 1;
    string name = 2;
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

service ImportStructEvenInArrayModelController {
    rpc Create(ImportStructEvenInArrayModel) returns (ImportStructEvenInArrayModel) {}
}

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

message UnitTestModelListRequest {
}

message UnitTestModelListResponse {
    repeated UnitTestModel results = 1;
    int32 count = 2;
}

message UnitTestModel {
    int32 id = 1;
    string text = 2;
    string title = 3;
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
