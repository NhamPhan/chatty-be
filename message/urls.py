from django.urls import path

from .views import (
    NotificationListView,
    FriendRequestView,
    UserView,
    UserListView,
    ThreadListView,
    MessageListView,
    ThreadDetailView,
)

urlpatterns = [
    path("notification/", NotificationListView.as_view(), name="notification-list"),
    path("friend-request/", FriendRequestView.as_view(), name="friend-request"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<uuid:pk>", UserView.as_view(), name="user"),
    path("threads/", ThreadListView.as_view(), name="thread-list"),
    path("threads/<uuid:pk>", ThreadDetailView.as_view(), name="thread-detail"),
    path("message/<uuid:thread_id>", MessageListView.as_view(), name="message-list"),
]
