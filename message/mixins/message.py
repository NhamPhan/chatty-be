from django.db.models import Q
from rest_framework import status

from message import constants
from message.models import Thread
from message.utils import app_response


class MessageListMixin:
    def list(self, request, *args, **kwargs):
        if not self.check_has_view_permission(request, *args, **kwargs):
            return app_response(
                {
                    "status": status.HTTP_403_FORBIDDEN,
                    "detail": constants.FORBIDDEN,
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer_render = self.serializer_view
        queryset = self.filter_queryset(
            self.get_queryset().filter(**kwargs, is_deleted=False)
        )
        page = self.paginate_queryset(queryset)
        if page:
            serializer = serializer_render(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return paginated

        serializer = serializer_render(queryset, many=True)

        return app_response(
            {"result": serializer.data, "status": status.HTTP_200_OK},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def check_has_view_permission(request, *args, **kwargs):
        thread_id = kwargs.get("thread_id")
        thread = Thread.objects.filter(id=thread_id, is_deleted=False).first()
        if not thread:
            return False
        user = request.user
        member = thread.memberpreference_set.filter(
            member__user_id=user.id, is_deleted=False
        ).first()
        return bool(member)
