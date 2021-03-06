from django.contrib.auth.models import User

import account_pb2
import account_pb2_grpc
from django_socio_grpc.test import RPCTestCase


class UserServiceTest(RPCTestCase):
    def test_create_user(self):
        stub = account_pb2_grpc.UserControllerStub(self.channel)
        response = stub.Create(account_pb2.User(username="tom", email="tom@account.com"))
        self.assertEqual(response.username, "tom")
        self.assertEqual(response.email, "tom@account.com")
        self.assertEqual(User.objects.count(), 1)
