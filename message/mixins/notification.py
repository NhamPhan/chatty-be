from django.db import transaction
from django.db.models import Q
from django.http import Http404
from rest_framework import status

from message import constants
from message.utils import app_response


class NotificationListMixin:
    def list(self, request, *args, **kwargs):
        if not hasattr(request, "user"):
            return app_response(
                {
                    "status": status.HTTP_403_FORBIDDEN,
                    "detail": constants.LOGIN_TIMEOUT,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer_render = self.serializer_view
        user = request.user

        lookup_filter = Q(recipient_id=user.id) | Q(created_by=user.id)
        queryset = self.filter_queryset(
            self.get_queryset().filter(**kwargs, is_deleted=False).filter(lookup_filter)
        )
        page = self.paginate_queryset(queryset)

        if page:
            serializer = serializer_render(
                page, many=True, context={"request": request}
            )
            paginated = self.get_paginated_response(serializer.data)

            return paginated

        serializer = serializer_render(
            queryset, many=True, context={"request": request}
        )

        return app_response(
            {"result": serializer.data, "status": status.HTTP_200_OK},
            status=status.HTTP_200_OK,
        )


class NotificationUpdateMixin:
    def update(self, request, is_many=False, *args, **kwargs):
        if not hasattr(request, 'user'):
            return app_response(
                {
                    "status": status.HTTP_403_FORBIDDEN,
                    "detail": constants.LOGIN_TIMEOUT,
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        if not is_many:
            instance = self.filter_queryset(
                self.get_queryset().filter(
                    **kwargs,
                    is_delete=False,
                    recipient=request.user
                )
            ).first()
            if instance:
                serializer = self.serializer_class(instance, data=request.data)
                serializer.is_valid(raise_exception=True)
                perform_update = self.perform_update(serializer)
                if perform_update:
                    return app_response(
                        {
                            "status": status.HTTP_200_OK,
                            "result": "The information was successfully updated.",
                        },
                        status=status.HTTP_200_OK,
                    )
                return app_response(
                    {
                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "An unexpected error occurred, the update was not changed.",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    is_errors=True,
                )
            raise Http404
        else:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance_list = serializer.validated_data.get('id_list', [])
            if instance_list:
                serializer_list = []
                data = serializer.validated_data
                del data['id_list']
                for instance in instance_list:
                    serializer = self.serializer_update(instance, data=data)
                    serializer.is_valid(raise_exception=True)
                    serializer_list.append(serializer)
                perform_update = self.perform_update_list(serializer_list=serializer_list)
                if perform_update:
                    return app_response(
                        {'status': status.HTTP_200_OK, 'result': 'The information was successfully updated.'},
                        status=status.HTTP_200_OK)
                return app_response({'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                                     'result': 'An unexpected error occurred, the update was not changed.'},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            raise Http404

    @classmethod
    def perform_update(cls, serializer):
        try:
            with transaction.atomic():
                instance = serializer.save()
            return instance
        except Exception as e:
            print(e)
        return None

    @classmethod
    def perform_update_list(cls, serializer_list):
        try:
            with transaction.atomic():
                for serializer in serializer_list:
                    serializer.save()
            return True
        except Exception as e:
            print(e)
        return False
