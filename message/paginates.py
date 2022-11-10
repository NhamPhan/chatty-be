from collections import OrderedDict

from django.conf import settings
from django.db.models import Q
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response

from message.middleware import get_request_user
from message.models import Notification


class UserListPagination(CursorPagination):
    page_size = 10
    ordering = ["-first_name", "-last_name"]


class NotificationPagination(CursorPagination):
    page_size = 10
    ordering = ["-created_at", "-is_pending"]

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                    ("count_new", self.count_new_notifications()),
                ]
            )
        )

    @staticmethod
    def count_new_notifications():
        user = get_request_user()
        if not user:
            return 0
        lookup = Q(recipient_id=user.id) | Q(created_by=user.id)
        query = Notification.objects.filter(is_deleted=False, is_seen=False).filter(lookup)
        sliced_query = query[: settings.NOTIFICATION_LIMIT]
        return len(sliced_query)


class ThreadPagination(CursorPagination):
    page_size = 10
    ordering = ["-created_at", ]


class MessagePagination(CursorPagination):
    page_size = 20
    ordering = ["-created_at"]
