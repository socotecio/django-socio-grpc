from django_socio_grpc import generics
from django_socio_grpc.decorators import grpc_action
from fakeapp.serializers import BasicServiceSerializer


class BasicService(generics.GenericService):
    @grpc_action(
        request=[{"name": "user_name", "type": "string"}],
        response=BasicServiceSerializer,
    )
    async def FetchDataForUser(self, request, context):
        # INFO - AM - 14/01/2022 - Do something here as filter user with the user name
        print(request.user_name)

        user_data = {
            "email": "fake_email@email.com",
            "birth_date": "25/01/1996",
            "slogan": "Do it better",
        }

        serializer = BasicServiceSerializer(
            {"user_name": request.user_name, "user_data": user_data}
        )
        return serializer.message
