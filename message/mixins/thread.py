from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import ValidationError

from message import constants
from message.models import Thread, Member, MemberPreference
from message.utils import app_response


class ThreadCreateMixin:
    @staticmethod
    def add_member(thread_id, user, member, is_creator=False, is_leader=False):
        created_member = Member.objects.create(
            thread_id=thread_id,
            created_by=user.id,
            updated_by=user.id,
            user_id=member.id,
            is_deleted=False,
        )
        MemberPreference.objects.create(
            member_id=created_member.id,
            created_by=user.id,
            updated_by=user.id,
            thread_id=thread_id,
            is_creator=is_creator,
            is_leader=is_leader,
        )
        return created_member

    def create(self, request, *args, **kwargs):
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
        instance = self.perform_create(serializer, request.user)
        if not isinstance(instance, Exception):
            return app_response(
                {
                    "status": status.HTTP_201_CREATED,
                    "result": self.serializer_class(instance).data,
                },
                status=status.HTTP_201_CREATED,
            )
        elif isinstance(instance, ValidationError):
            raise instance

        return app_response(
            {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": constants.INTERNAL_ERROR,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            is_errors=True,
        )

    def perform_create(self, serializer, user):
        try:
            users = serializer.validated_data["member_ids"]
            thread_name = serializer.validated_data["name"]

            thread_members = [*users, user]
            with transaction.atomic():
                threads = Thread.objects.filter(
                    is_deleted=False, members__in=thread_members
                )
                if threads.count() > 0:
                    for thread in threads:
                        member_count = thread.member_set.count()
                        if member_count != len(thread_members):
                            continue
                        return thread

                thread = Thread.objects.create(
                    created_by=user.id, updated_by=user.id, name=thread_name
                )

                self.add_member(
                    thread_id=thread.id,
                    user=user,
                    member=user,
                    is_creator=True,
                    is_leader=True,
                )
                for member in users:
                    self.add_member(thread_id=thread.id, user=user, member=member)
                return thread
        except Exception as e:
            print(e)
            return e


class ThreadDeleteMixin:
    pass


class ThreadListMixin:
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
        serializer_render = self.serializer_class
        lookup = Q(member__user_id=user.id)
        queryset = self.filter_queryset(
            self.get_queryset().filter(**kwargs, is_deleted=False).filter(lookup)
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializer_render(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = serializer_render(queryset, many=True)
        return app_response(
            {"result": serializer.data, "status": status.HTTP_200_OK},
            status=status.HTTP_200_OK,
        )
