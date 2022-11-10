from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, filters
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated, AllowAny

from message.filters import UserFilter
from message.mixins import (
    FriendRequestMixin,
    NotificationListMixin,
    UserListMixin,
    NotificationUpdateMixin,
    ThreadListMixin,
    ThreadCreateMixin,
    UpdateUserMixin,
    MessageListMixin,
)
from message.models import Notification, Contact, User, Thread, Message
from message.paginates import (
    UserListPagination,
    NotificationPagination,
    ThreadPagination,
    MessagePagination,
)
from message.serializers import (
    CreateFriendRequestSerializer,
    ProcessFriendRequestSerializer,
    DeleteNotificationSerializer,
    NotificationSerializer,
    NotificationUpdateManySerializer,
    ContactSerializer,
    UserViewSerializer,
    ThreadViewSerializer,
    ThreadCreateSerializer,
    UpdateProfileSerializer,
    MessageViewSerializer,
)


class FriendRequestView(FriendRequestMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Contact.objects.all()
    filterset_fields = ("friend_id",)
    search_fields = ("friend__name", "friend__email")
    serializer_class = NotificationSerializer

    serializer_create = CreateFriendRequestSerializer
    serializer_view = ContactSerializer
    serializer_put = ProcessFriendRequestSerializer
    serializer_delete = DeleteNotificationSerializer

    @swagger_auto_schema()
    def get(self, request, *args, **kwargs):
        self.serializer_class = ContactSerializer
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(request_body=CreateFriendRequestSerializer)
    def post(self, request, *args, **kwargs):
        return self.create_friend_request(request=request, *args, **kwargs)

    @swagger_auto_schema(request_body=ProcessFriendRequestSerializer)
    def put(self, request, *args, **kwargs):
        return self.process_friend_request(request=request, *args, **kwargs)

    @swagger_auto_schema(request_body=DeleteNotificationSerializer)
    def delete(self, request, *args, **kwargs):
        return self.delete_friend_request(request=request, *args, **kwargs)


class NotificationListView(
    NotificationListMixin, NotificationUpdateMixin, generics.GenericAPIView
):
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all()
    filterset_fields = (
        "is_pending",
        "recipient",
    )
    filter_backends = []
    pagination_class = NotificationPagination

    serializer_class = NotificationSerializer
    serializer_view = NotificationSerializer
    serializer_update = NotificationUpdateManySerializer

    @swagger_auto_schema()
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(request_body=NotificationUpdateManySerializer)
    def put(self, request, *args, **kwargs):
        return self.update(request=request, is_many=True, *args, **kwargs)


class UserView(RetrieveModelMixin, UpdateUserMixin, generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserViewSerializer
    serializer_update = UpdateProfileSerializer
    queryset = User.objects.all()

    @swagger_auto_schema()
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(request_body=UpdateProfileSerializer)
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class UserListView(UserListMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    search_fields = ["username", "email"]

    filter_backends = [
        filters.SearchFilter,
        DjangoFilterBackend,
    ]
    filterset_class = UserFilter
    pagination_class = UserListPagination
    serializer_class = UserViewSerializer

    @swagger_auto_schema()
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ThreadListView(ThreadListMixin, ThreadCreateMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Thread.objects.all()

    serializer_class = ThreadViewSerializer
    serializer_create = ThreadCreateSerializer

    search_fields = ["name"]

    filter_backends = [filters.SearchFilter]
    pagination_class = ThreadPagination

    @swagger_auto_schema()
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(request_body=ThreadCreateSerializer)
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ThreadDetailView(RetrieveModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Thread.objects.all()

    serializer_class = ThreadViewSerializer

    @swagger_auto_schema()
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class MessageListView(MessageListMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Message.objects.all()

    serializer_class = MessageViewSerializer
    serializer_view = MessageViewSerializer
    pagination_class = MessagePagination

    filter_backends = [filters.SearchFilter]

    @swagger_auto_schema()
    def get(self, request, *args, **kwargs):
        return self.list(request=request, *args, **kwargs)
