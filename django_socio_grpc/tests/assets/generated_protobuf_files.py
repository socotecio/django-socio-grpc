SIMPLE_MODEL_GENERATED = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";

service UnitTestModelController {
    rpc ListWithExtraArgs(UnitTestModelListWithExtraArgsRequest) returns (UnitTestModelListExtraArgsResponse) {}
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModelRequest) returns (UnitTestModelResponse) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModelResponse) {}
    rpc Update(UnitTestModelRequest) returns (UnitTestModelResponse) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModelResponse) {}
}

message UnitTestModelListWithExtraArgsRequest {
    bool archived = 1;
}

message UnitTestModelListExtraArgsResponse {
    int32 count = 1;
    string query_fetched_datetime = 2;
    repeated UnitTestModelResponse results = 3;
}

message UnitTestModelResponse {
    int32 id = 1;
    string title = 2;
    string text = 3;
}

message UnitTestModelListRequest {
}

message UnitTestModelListResponse {
    repeated UnitTestModelResponse results = 1;
    int32 count = 2;
}

message UnitTestModelRequest {
    int32 id = 1;
    string title = 2;
    string text = 3;
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
    rpc Create(UnitTestModelRequest) returns (UnitTestModelResponse) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModelResponse) {}
    rpc Update(UnitTestModelRequest) returns (UnitTestModelResponse) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModelResponse) {}
}

message UnitTestModelResponse {
    int32 id = 1;
    string text = 2;
    string title = 3;
}

message UnitTestModelListRequest {
}

message UnitTestModelListResponse {
    repeated UnitTestModelResponse results = 1;
    int32 count = 2;
}

message UnitTestModelRequest {
    int32 id = 1;
    string title = 2;
    string text = 3;
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

CUSTOM_APP_MODEL_GENERATED = """syntax = "proto3";

package myproject.fakeapp;

service ForeignModelController {
    rpc List(ForeignModelListRequest) returns (ForeignModelListResponse) {}
    rpc Retrieve(ForeignModelRetrieveCustomRetrieveRequest) returns (ForeignModelRetrieveCustomResponse) {}
}

message ForeignModelResponse {
    string uuid = 1;
    string name = 2;
}

message ForeignModelListRequest {
}

message ForeignModelListResponse {
    repeated ForeignModelResponse results = 1;
    int32 count = 2;
}

message ForeignModelRetrieveCustomRetrieveRequest {
    string name = 1;
}

message ForeignModelRetrieveCustomResponse {
    string name = 1;
    string custom = 2;
}

"""

MODEL_WITH_M2M_GENERATED = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";

service RelatedFieldModelController {
    rpc List(RelatedFieldModelListRequest) returns (RelatedFieldModelListResponse) {}
    rpc Create(RelatedFieldModelRequest) returns (RelatedFieldModelResponse) {}
    rpc Retrieve(RelatedFieldModelRetrieveRequest) returns (RelatedFieldModelResponse) {}
    rpc Update(RelatedFieldModelRequest) returns (RelatedFieldModelResponse) {}
    rpc Destroy(RelatedFieldModelDestroyRequest) returns (google.protobuf.Empty) {}
}

message RelatedFieldModelResponse {
    string uuid = 1;
    ForeignModelResponse foreign_obj = 2;
    repeated ManyManyModelResponse many_many_obj = 3;
    int32 slug_test_model = 4;
    repeated bool slug_reverse_test_model = 5;
    repeated string slug_many_many = 6;
    string custom_field_name = 7;
    string foreign = 8;
    repeated string many_many = 9;
}

message ForeignModelResponse {
    string uuid = 1;
    string name = 2;
}

message ManyManyModelResponse {
    string uuid = 1;
    string name = 2;
}

message RelatedFieldModelListRequest {
}

message RelatedFieldModelListResponse {
    repeated RelatedFieldModelResponse list_custom_field_name = 1;
    int32 count = 2;
}

message RelatedFieldModelRequest {
    string uuid = 1;
    repeated ManyManyModelRequest many_many_obj = 2;
    string custom_field_name = 3;
    string foreign = 4;
    repeated string many_many = 5;
}

message ManyManyModelRequest {
    string uuid = 1;
    string name = 2;
    string test_write_only_on_nested = 3;
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
    rpc Create(ImportStructEvenInArrayModelRequest) returns (ImportStructEvenInArrayModelResponse) {}
}

message ImportStructEvenInArrayModelRequest {
    string uuid = 1;
    repeated google.protobuf.Struct this_is_crazy = 2;
}

message ImportStructEvenInArrayModelResponse {
    string uuid = 1;
    repeated google.protobuf.Struct this_is_crazy = 2;
}

"""


SIMPLE_APP_MODEL_OLD_ORDER = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";

service UnitTestModelController {
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModelRequest) returns (UnitTestModelResponse) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModelResponse) {}
    rpc Update(UnitTestModelRequest) returns (UnitTestModelResponse) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModelResponse) {}
}

message UnitTestModelRequest {
    int32 id = 1;
    string title = 2;
    string text = 3;
}

message UnitTestModelResponse {
    int32 id = 1;
    string text = 2;
}

message UnitTestModelListRequest {
}

message UnitTestModelListResponse {
    repeated UnitTestModelResponse results = 1;
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
    rpc Create(UnitTestModelRequest) returns (UnitTestModelResponse) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModelResponse) {}
    rpc Update(UnitTestModelRequest) returns (UnitTestModelResponse) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModelResponse) {}
}

message UnitTestModelResponse {
    int32 id = 1;
    string text = 2;
    string title = 3;
}

message UnitTestModelListRequest {
}

message UnitTestModelListResponse {
    repeated UnitTestModelResponse results = 1;
    int32 count = 2;
}

message UnitTestModelRequest {
    int32 id = 1;
    string title = 2;
    string text = 3;
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

MODEL_WITH_KNOWN_METHOD_OVERRIDED_GENERATED = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";
import "google/protobuf/struct.proto";

service SpecialFieldsModelController {
    rpc Retrieve(SpecialFieldsModelRetrieveRequest) returns (CustomRetrieveResponseSpecialFieldsModelResponse) {}
    rpc List(SpecialFieldsModelListRequest) returns (SpecialFieldsModelListResponse) {}
    rpc Create(SpecialFieldsModelRequest) returns (SpecialFieldsModelResponse) {}
    rpc Update(SpecialFieldsModelRequest) returns (SpecialFieldsModelResponse) {}
    rpc Destroy(SpecialFieldsModelDestroyRequest) returns (google.protobuf.Empty) {}
}

message SpecialFieldsModelRetrieveRequest {
    string uuid = 1;
}

message CustomRetrieveResponseSpecialFieldsModelResponse {
    string uuid = 1;
    int32 default_method_field = 2;
    repeated google.protobuf.Struct custom_method_field = 3;
}

message SpecialFieldsModelResponse {
    string uuid = 1;
    google.protobuf.Struct meta_datas = 2;
    repeated int32 list_datas = 3;
    bytes binary = 4;
}

message SpecialFieldsModelListRequest {
}

message SpecialFieldsModelListResponse {
    repeated SpecialFieldsModelResponse results = 1;
    int32 count = 2;
}

message SpecialFieldsModelRequest {
    string uuid = 1;
    google.protobuf.Struct meta_datas = 2;
    repeated int32 list_datas = 3;
}

message SpecialFieldsModelDestroyRequest {
    string uuid = 1;
}

"""

NO_MODEL_GENERATED = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";
import "google/protobuf/struct.proto";

service BasicController {
    rpc FetchDataForUser(BasicFetchDataForUserRequest) returns (BasicServiceResponse) {}
    rpc TestEmptyMethod(google.protobuf.Empty) returns (google.protobuf.Empty) {}
    rpc GetMultiple(google.protobuf.Empty) returns (BasicServiceListResponse) {}
    rpc MyMethod(CustomNameForRequest) returns (CustomNameForResponse) {}
    rpc MixParam(CustomMixParamForListRequest) returns (BasicMixParamListResponse) {}
    rpc MixParamWithSerializer(BasicParamWithSerializerListRequest) returns (BasicMixParamWithSerializerListResponse) {}
    rpc TestBaseProtoSerializer(BaseProtoExampleRequest) returns (BaseProtoExampleListResponse) {}
    rpc BasicList(BasicProtoListChildListResponse) returns (BasicProtoListChildListResponse) {}
}

message BasicFetchDataForUserRequest {
    string user_name = 1;
}

message BasicServiceResponse {
    string user_name = 1;
    google.protobuf.Struct user_data = 2;
    bytes bytes_example = 3;
    repeated google.protobuf.Struct list_of_dict = 4;
}

message BasicServiceListResponse {
    repeated BasicServiceResponse results = 1;
    int32 count = 2;
}

message CustomNameForRequest {
    string user_name = 1;
}

message CustomNameForResponse {
    string user_name = 1;
}

message CustomMixParamForRequest {
    string user_name = 1;
}

message CustomMixParamForListRequest {
    repeated CustomMixParamForRequest results = 1;
    int32 count = 2;
}

message BasicMixParamResponse {
    string user_name = 1;
}

message BasicMixParamListResponse {
    repeated BasicMixParamResponse results = 1;
    int32 count = 2;
}

message BasicParamWithSerializerRequest {
    string user_name = 1;
    google.protobuf.Struct user_data = 2;
    string user_password = 3;
    bytes bytes_example = 4;
    repeated google.protobuf.Struct list_of_dict = 5;
}

message BasicParamWithSerializerListRequest {
    repeated BasicParamWithSerializerRequest results = 1;
    int32 count = 2;
}

message BasicMixParamWithSerializerListResponse {
    repeated google.protobuf.Struct results = 1;
    int32 count = 2;
}

message BaseProtoExampleRequest {
    string uuid = 1;
    int32 number_of_elements = 2;
    bool is_archived = 3;
}

message BaseProtoExampleResponse {
    string uuid = 1;
    int32 number_of_elements = 2;
    bool is_archived = 3;
}

message BaseProtoExampleListResponse {
    repeated BaseProtoExampleResponse results = 1;
    int32 count = 2;
}

message BasicProtoListChildRequest {
    int32 id = 1;
    string title = 2;
    string text = 3;
}

message BasicProtoListChildListResponse {
    repeated BasicProtoListChildResponse results = 1;
    int32 count = 2;
}

message BasicProtoListChildResponse {
    int32 id = 1;
    string title = 2;
    string text = 3;
}

"""


ALL_APP_GENERATED_NO_SEPARATE = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";
import "google/protobuf/struct.proto";

service UnitTestModelController {
    rpc ListWithExtraArgs(UnitTestModelListWithExtraArgsRequest) returns (UnitTestModelListExtraArgs) {}
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModel) returns (UnitTestModel) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModel) {}
    rpc Update(UnitTestModel) returns (UnitTestModel) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModel) {}
}

service SyncUnitTestModelController {
    rpc ListWithExtraArgs(SyncUnitTestModelListWithExtraArgsRequest) returns (UnitTestModelListExtraArgs) {}
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModel) returns (UnitTestModel) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModel) {}
    rpc Update(UnitTestModel) returns (UnitTestModel) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModel) {}
}

service SpecialFieldsModelController {
    rpc Retrieve(SpecialFieldsModelRetrieveRequest) returns (CustomRetrieveResponseSpecialFieldsModel) {}
    rpc List(SpecialFieldsModelListRequest) returns (SpecialFieldsModelListResponse) {}
    rpc Create(SpecialFieldsModel) returns (SpecialFieldsModel) {}
    rpc Update(SpecialFieldsModel) returns (SpecialFieldsModel) {}
    rpc Destroy(SpecialFieldsModelDestroyRequest) returns (google.protobuf.Empty) {}
}

service BasicController {
    rpc FetchDataForUser(BasicFetchDataForUserRequest) returns (BasicService) {}
    rpc TestEmptyMethod(google.protobuf.Empty) returns (google.protobuf.Empty) {}
    rpc GetMultiple(google.protobuf.Empty) returns (BasicServiceListResponse) {}
    rpc MyMethod(CustomNameForRequest) returns (CustomNameForResponse) {}
    rpc MixParam(CustomMixParamForRequestList) returns (BasicMixParamListResponse) {}
    rpc MixParamWithSerializer(BasicParamWithSerializerRequestList) returns (BasicMixParamWithSerializerListResponse) {}
    rpc TestBaseProtoSerializer(BaseProtoExample) returns (BaseProtoExampleListResponse) {}
    rpc BasicList(BasicProtoListChildListResponse) returns (BasicProtoListChildListResponse) {}
}

service ForeignModelController {
    rpc List(ForeignModelListRequest) returns (ForeignModelListResponse) {}
    rpc Retrieve(ForeignModelRetrieveCustomRetrieveRequest) returns (ForeignModelRetrieveCustom) {}
}

service ImportStructEvenInArrayModelController {
    rpc Create(ImportStructEvenInArrayModel) returns (ImportStructEvenInArrayModel) {}
}

service RelatedFieldModelController {
    rpc List(RelatedFieldModelListRequest) returns (RelatedFieldModelListResponse) {}
    rpc Create(RelatedFieldModel) returns (RelatedFieldModel) {}
    rpc Retrieve(RelatedFieldModelRetrieveRequest) returns (RelatedFieldModel) {}
    rpc Update(RelatedFieldModel) returns (RelatedFieldModel) {}
    rpc Destroy(RelatedFieldModelDestroyRequest) returns (google.protobuf.Empty) {}
}

message UnitTestModelListWithExtraArgsRequest {
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

message SyncUnitTestModelListWithExtraArgsRequest {
    bool archived = 1;
}

message SpecialFieldsModelRetrieveRequest {
    string uuid = 1;
}

message CustomRetrieveResponseSpecialFieldsModel {
    string uuid = 1;
    int32 default_method_field = 2;
    repeated google.protobuf.Struct custom_method_field = 3;
}

message BasicFetchDataForUserRequest {
    string user_name = 1;
}

message BasicService {
    string user_name = 1;
    google.protobuf.Struct user_data = 2;
    string user_password = 3;
    bytes bytes_example = 4;
    repeated google.protobuf.Struct list_of_dict = 5;
}

message BasicServiceListResponse {
    repeated BasicService results = 1;
    int32 count = 2;
}

message CustomNameForRequest {
    string user_name = 1;
}

message CustomNameForResponse {
    string user_name = 1;
}

message CustomMixParamForRequest {
    string user_name = 1;
}

message CustomMixParamForRequestList {
    repeated CustomMixParamForRequest results = 1;
    int32 count = 2;
}

message BasicMixParamResponse {
    string user_name = 1;
}

message BasicMixParamListResponse {
    repeated BasicMixParamResponse results = 1;
    int32 count = 2;
}

message BasicParamWithSerializerRequest {
    string user_name = 1;
    google.protobuf.Struct user_data = 2;
    string user_password = 3;
    bytes bytes_example = 4;
    repeated google.protobuf.Struct list_of_dict = 5;
}

message BasicParamWithSerializerRequestList {
    repeated BasicParamWithSerializerRequest results = 1;
    int32 count = 2;
}

message BasicMixParamWithSerializerListResponse {
    repeated google.protobuf.Struct results = 1;
    int32 count = 2;
}

message BaseProtoExample {
    string uuid = 1;
    int32 number_of_elements = 2;
    bool is_archived = 3;
}

message BaseProtoExampleListResponse {
    repeated BaseProtoExample results = 1;
    int32 count = 2;
}

message BasicProtoListChild {
    int32 id = 1;
    string title = 2;
    string text = 3;
}

message BasicProtoListChildListResponse {
    repeated BasicProtoListChild results = 1;
    int32 count = 2;
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

message ForeignModelRetrieveCustomRetrieveRequest {
    string name = 1;
}

message ForeignModelRetrieveCustom {
    string name = 1;
    string custom = 2;
}

message ImportStructEvenInArrayModel {
    string uuid = 1;
    repeated google.protobuf.Struct this_is_crazy = 2;
}

message RelatedFieldModel {
    string uuid = 1;
    ForeignModel foreign_obj = 2;
    repeated ManyManyModel many_many_obj = 3;
    int32 slug_test_model = 4;
    repeated bool slug_reverse_test_model = 5;
    repeated string slug_many_many = 6;
    string custom_field_name = 7;
    string foreign = 8;
    repeated string many_many = 9;
}

message ManyManyModel {
    string uuid = 1;
    string name = 2;
    string test_write_only_on_nested = 3;
}

message RelatedFieldModelListRequest {
}

message RelatedFieldModelListResponse {
    repeated RelatedFieldModel list_custom_field_name = 1;
    int32 count = 2;
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

message SpecialFieldsModelDestroyRequest {
    string uuid = 1;
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

ALL_APP_GENERATED_SEPARATE = """syntax = "proto3";

package myproject.fakeapp;

import "google/protobuf/empty.proto";
import "google/protobuf/struct.proto";

service UnitTestModelController {
    rpc ListWithExtraArgs(UnitTestModelListWithExtraArgsRequest) returns (UnitTestModelListExtraArgsResponse) {}
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModelRequest) returns (UnitTestModelResponse) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModelResponse) {}
    rpc Update(UnitTestModelRequest) returns (UnitTestModelResponse) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModelResponse) {}
}

service SyncUnitTestModelController {
    rpc ListWithExtraArgs(SyncUnitTestModelListWithExtraArgsRequest) returns (UnitTestModelListExtraArgsResponse) {}
    rpc List(UnitTestModelListRequest) returns (UnitTestModelListResponse) {}
    rpc Create(UnitTestModelRequest) returns (UnitTestModelResponse) {}
    rpc Retrieve(UnitTestModelRetrieveRequest) returns (UnitTestModelResponse) {}
    rpc Update(UnitTestModelRequest) returns (UnitTestModelResponse) {}
    rpc Destroy(UnitTestModelDestroyRequest) returns (google.protobuf.Empty) {}
    rpc Stream(UnitTestModelStreamRequest) returns (stream UnitTestModelResponse) {}
}

service SpecialFieldsModelController {
    rpc Retrieve(SpecialFieldsModelRetrieveRequest) returns (CustomRetrieveResponseSpecialFieldsModelResponse) {}
    rpc List(SpecialFieldsModelListRequest) returns (SpecialFieldsModelListResponse) {}
    rpc Create(SpecialFieldsModelRequest) returns (SpecialFieldsModelResponse) {}
    rpc Update(SpecialFieldsModelRequest) returns (SpecialFieldsModelResponse) {}
    rpc Destroy(SpecialFieldsModelDestroyRequest) returns (google.protobuf.Empty) {}
}

service BasicController {
    rpc FetchDataForUser(BasicFetchDataForUserRequest) returns (BasicServiceResponse) {}
    rpc TestEmptyMethod(google.protobuf.Empty) returns (google.protobuf.Empty) {}
    rpc GetMultiple(google.protobuf.Empty) returns (BasicServiceListResponse) {}
    rpc MyMethod(CustomNameForRequest) returns (CustomNameForResponse) {}
    rpc MixParam(CustomMixParamForListRequest) returns (BasicMixParamListResponse) {}
    rpc MixParamWithSerializer(BasicParamWithSerializerListRequest) returns (BasicMixParamWithSerializerListResponse) {}
    rpc TestBaseProtoSerializer(BaseProtoExampleRequest) returns (BaseProtoExampleListResponse) {}
    rpc BasicList(BasicProtoListChildListResponse) returns (BasicProtoListChildListResponse) {}
}

service ForeignModelController {
    rpc List(ForeignModelListRequest) returns (ForeignModelListResponse) {}
    rpc Retrieve(ForeignModelRetrieveCustomRetrieveRequest) returns (ForeignModelRetrieveCustomResponse) {}
}

service ImportStructEvenInArrayModelController {
    rpc Create(ImportStructEvenInArrayModelRequest) returns (ImportStructEvenInArrayModelResponse) {}
}

service RelatedFieldModelController {
    rpc List(RelatedFieldModelListRequest) returns (RelatedFieldModelListResponse) {}
    rpc Create(RelatedFieldModelRequest) returns (RelatedFieldModelResponse) {}
    rpc Retrieve(RelatedFieldModelRetrieveRequest) returns (RelatedFieldModelResponse) {}
    rpc Update(RelatedFieldModelRequest) returns (RelatedFieldModelResponse) {}
    rpc Destroy(RelatedFieldModelDestroyRequest) returns (google.protobuf.Empty) {}
}

message UnitTestModelListWithExtraArgsRequest {
    bool archived = 1;
}

message UnitTestModelListExtraArgsResponse {
    int32 count = 1;
    string query_fetched_datetime = 2;
    repeated UnitTestModelResponse results = 3;
}

message UnitTestModelResponse {
    int32 id = 1;
    string title = 2;
    string text = 3;
}

message SyncUnitTestModelListWithExtraArgsRequest {
    bool archived = 1;
}

message SpecialFieldsModelRetrieveRequest {
    string uuid = 1;
}

message CustomRetrieveResponseSpecialFieldsModelResponse {
    string uuid = 1;
    int32 default_method_field = 2;
    repeated google.protobuf.Struct custom_method_field = 3;
}

message BasicFetchDataForUserRequest {
    string user_name = 1;
}

message BasicServiceResponse {
    string user_name = 1;
    google.protobuf.Struct user_data = 2;
    bytes bytes_example = 3;
    repeated google.protobuf.Struct list_of_dict = 4;
}

message BasicServiceListResponse {
    repeated BasicServiceResponse results = 1;
    int32 count = 2;
}

message CustomNameForRequest {
    string user_name = 1;
}

message CustomNameForResponse {
    string user_name = 1;
}

message CustomMixParamForRequest {
    string user_name = 1;
}

message CustomMixParamForListRequest {
    repeated CustomMixParamForRequest results = 1;
    int32 count = 2;
}

message BasicMixParamResponse {
    string user_name = 1;
}

message BasicMixParamListResponse {
    repeated BasicMixParamResponse results = 1;
    int32 count = 2;
}

message BasicParamWithSerializerRequest {
    string user_name = 1;
    google.protobuf.Struct user_data = 2;
    string user_password = 3;
    bytes bytes_example = 4;
    repeated google.protobuf.Struct list_of_dict = 5;
}

message BasicParamWithSerializerListRequest {
    repeated BasicParamWithSerializerRequest results = 1;
    int32 count = 2;
}

message BasicMixParamWithSerializerListResponse {
    repeated google.protobuf.Struct results = 1;
    int32 count = 2;
}

message BaseProtoExampleRequest {
    string uuid = 1;
    int32 number_of_elements = 2;
    bool is_archived = 3;
}

message BaseProtoExampleResponse {
    string uuid = 1;
    int32 number_of_elements = 2;
    bool is_archived = 3;
}

message BaseProtoExampleListResponse {
    repeated BaseProtoExampleResponse results = 1;
    int32 count = 2;
}

message BasicProtoListChildRequest {
    int32 id = 1;
    string title = 2;
    string text = 3;
}

message BasicProtoListChildListResponse {
    repeated BasicProtoListChildResponse results = 1;
    int32 count = 2;
}

message BasicProtoListChildResponse {
    int32 id = 1;
    string title = 2;
    string text = 3;
}

message ForeignModelResponse {
    string uuid = 1;
    string name = 2;
}

message ForeignModelListRequest {
}

message ForeignModelListResponse {
    repeated ForeignModelResponse results = 1;
    int32 count = 2;
}

message ForeignModelRetrieveCustomRetrieveRequest {
    string name = 1;
}

message ForeignModelRetrieveCustomResponse {
    string name = 1;
    string custom = 2;
}

message ImportStructEvenInArrayModelRequest {
    string uuid = 1;
    repeated google.protobuf.Struct this_is_crazy = 2;
}

message ImportStructEvenInArrayModelResponse {
    string uuid = 1;
    repeated google.protobuf.Struct this_is_crazy = 2;
}

message RelatedFieldModelResponse {
    string uuid = 1;
    ForeignModelResponse foreign_obj = 2;
    repeated ManyManyModelResponse many_many_obj = 3;
    int32 slug_test_model = 4;
    repeated bool slug_reverse_test_model = 5;
    repeated string slug_many_many = 6;
    string custom_field_name = 7;
    string foreign = 8;
    repeated string many_many = 9;
}

message ManyManyModelResponse {
    string uuid = 1;
    string name = 2;
}

message RelatedFieldModelListRequest {
}

message RelatedFieldModelListResponse {
    repeated RelatedFieldModelResponse list_custom_field_name = 1;
    int32 count = 2;
}

message RelatedFieldModelRequest {
    string uuid = 1;
    repeated ManyManyModelRequest many_many_obj = 2;
    string custom_field_name = 3;
    string foreign = 4;
    repeated string many_many = 5;
}

message ManyManyModelRequest {
    string uuid = 1;
    string name = 2;
    string test_write_only_on_nested = 3;
}

message RelatedFieldModelRetrieveRequest {
    string uuid = 1;
}

message RelatedFieldModelDestroyRequest {
    string uuid = 1;
}

message SpecialFieldsModelResponse {
    string uuid = 1;
    google.protobuf.Struct meta_datas = 2;
    repeated int32 list_datas = 3;
    bytes binary = 4;
}

message SpecialFieldsModelListRequest {
}

message SpecialFieldsModelListResponse {
    repeated SpecialFieldsModelResponse results = 1;
    int32 count = 2;
}

message SpecialFieldsModelRequest {
    string uuid = 1;
    google.protobuf.Struct meta_datas = 2;
    repeated int32 list_datas = 3;
}

message SpecialFieldsModelDestroyRequest {
    string uuid = 1;
}

message UnitTestModelListRequest {
}

message UnitTestModelListResponse {
    repeated UnitTestModelResponse results = 1;
    int32 count = 2;
}

message UnitTestModelRequest {
    int32 id = 1;
    string title = 2;
    string text = 3;
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
