from django.db.models import Q
from rest_framework import status

from message import constants
from message.models import Notification, Contact
from message.utils import app_response


class FriendRequestMixin:
    @staticmethod
    def _check_contact_is_presented(user_id, friend_id):
        contacts = Contact.objects.filter(
            Q(user_id=user_id, friend_id=friend_id)
            | Q(user_id=friend_id, friend_id=user_id),
            is_active=True,
        ).all()
        return contacts

    @staticmethod
    def _check_request_is_created(user_id, friend_id):
        lookup = Q(payload__user_id=user_id, payload__friend_id=friend_id) | Q(
            payload__user_id=friend_id, payload__friend_id=user_id
        )
        notification = Notification.objects.filter(lookup).filter(
            is_pending=True, is_deleted=False
        )
        return notification.all()

    def create_friend_request(self, request, *args, **kwargs):
        if not hasattr(request, "user"):
            return app_response(
                {
                    "status": status.HTTP_403_FORBIDDEN,
                    "detail": constants.LOGIN_TIMEOUT,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.serializer_create(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        user_id = serializer.validated_data["user_id"]
        friend_id = serializer.validated_data["friend_id"]

        if user_id != user.id or friend_id == user.id:
            return app_response(
                {"status": status.HTTP_403_FORBIDDEN, "detail": constants.FAILED},
                status=status.HTTP_403_FORBIDDEN,
            )

        contact_presented = self._check_contact_is_presented(
            user_id=user.id, friend_id=friend_id
        )
        if contact_presented:
            return app_response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "detail": constants.ALREADY_FRIEND,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_created = self._check_contact_is_presented(
            user_id=user.id, friend_id=friend_id
        )
        if request_created:
            return app_response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "detail": constants.FRIEND_REQUEST_ALREADY_SENT,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance = self.perform_create(serializer, user)
        if instance:
            return app_response(
                {
                    "result": self.serializer_class(instance).data,
                    "status": status.HTTP_201_CREATED,
                },
                status=status.HTTP_201_CREATED,
            )
        return app_response(
            {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": constants.INTERNAL_ERROR,
            }
        )

    def process_friend_request(self, request, *args, **kwargs):
        if not hasattr(request, "user"):
            return app_response(
                {
                    "status": status.HTTP_403_FORBIDDEN,
                    "detail": constants.LOGIN_TIMEOUT,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.serializer_put(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance = self.perform_update(serializer, request.user)
        if instance:
            return app_response(
                {
                    "result": self.serializer_view(instance).data,
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )
        return app_response(
            {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": constants.INTERNAL_ERROR,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def delete_friend_request(self, request, *args, **kwargs):
        if not hasattr(request, "user"):
            return app_response(
                {
                    "status": status.HTTP_403_FORBIDDEN,
                    "detail": constants.LOGIN_TIMEOUT,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.serializer_delete(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        self.perform_delete(serializer, user)

    def list(self, request, *args, **kwargs):
        if not hasattr(request, "user"):
            return app_response(
                {
                    "status": status.HTTP_403_FORBIDDEN,
                    "detail": constants.LOGIN_TIMEOUT,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        user = request.user
        serializer_render = self.serializer_view

        lookup = Q(user_id=user.id, is_active=True)
        queryset = self.filter_queryset(
            self.get_queryset().filter(**kwargs, is_deleted=False).filter(lookup)
        )
        page = self.paginate_queryset(queryset)

        if page:
            serializer = serializer_render(data=page, many=True)
            return self.get_paginate_response(serializer.data)

        serializer = serializer_render(queryset, many=True)
        return app_response(
            {"result": serializer.data, "status": status.HTTP_200_OK},
            status=status.HTTP_200_OK,
        )

    @classmethod
    def perform_create(cls, serializer, user):
        friend_id = serializer.validated_data.get("friend_id")
        notification_type = Notification.Type.FRIEND_REQUEST

        payload = {
            "user_id": str(user.id),
            "friend_id": str(friend_id),
        }
        notification, _ = Notification.objects.update_or_create(
            defaults={
                "payload": payload,
                "recipient_id": friend_id,
                "created_by": user.id,
                "is_pending": True,
                "is_sent": False,
                "is_seen": False,
            },
            payload=payload,
            recipient_id=friend_id,
            created_by=user.id,
            notification_type=notification_type,
        )
        # TODO: Send request via Websocket
        return notification

    @classmethod
    def perform_update(cls, serializer, user):
        notification = Notification.objects.get(
            id=serializer.validated_data["notification_id"]
        )

        is_active = serializer.validated_data["is_active"]
        user_id = notification.payload["user_id"]
        friend_id = notification.payload["friend_id"]

        if str(user.id) != friend_id:
            return None

        notification.is_pending = False
        notification.save()

        Contact.objects.update_or_create(
            defaults={
                "is_active": is_active,
                "created_by": user.id,
                "updated_by": user.id,
            },
            user_id=friend_id,
            friend_id=user_id,
        )
        return Contact.objects.update_or_create(
            defaults={
                "is_active": is_active,
                "created_by": user.id,
                "updated_by": user.id,
            },
            user_id=user_id,
            friend_id=friend_id,
        )

    @classmethod
    def perform_delete(cls, serializer, user):
        notification = Notification.objects.get(
            id=serializer.validated_data["notification_id"]
        )

        notification.is_deleted = True
        notification.updated_by = user.id
        notification.save()
        return True
