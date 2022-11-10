from django.db import transaction
from rest_framework import status
from rest_framework.generics import get_object_or_404

from message import constants
from message.models import UserProfile
from message.utils import app_response


class UserViewMixin:
    def retrieve(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg not in kwargs and hasattr(request, "user"):
            kwargs[lookup_url_kwarg] = request.user.id
        filter_kwargs = {self.lookup_field: kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        return obj


class UserListMixin:
    def list(self, request, *args, **kwargs):
        serializer_render = self.serializer_class
        queryset = self.filter_queryset(self.get_queryset().filter(**kwargs)).order_by(
            "first_name"
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializer_render(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = serializer_render(
            queryset, many=True, context={"request": request}
        )
        return app_response(
            {"result": serializer.data, "status": status.HTTP_200_OK},
            status=status.HTTP_200_OK,
        )


class UpdateUserMixin:
    def update(self, request, *args, **kwargs):
        user = request.user
        instance = self.filter_queryset(
            self.get_queryset().filter(**kwargs, is_active=False)
        ).first()

        serializer = self.serializer_update(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        result = self.perform_update(serializer, user)

        if not result:
            return app_response(
                {
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": constants.INTERNAL_ERROR,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return app_response(
            {
                "status": status.HTTP_202_ACCEPTED,
                "result": constants.SUCCESS,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @classmethod
    def perform_update(cls, serializer, user):
        try:
            with transaction.atomic():
                validated_data = serializer.validated_data
                user.first_name = validated_data["first_name"]
                user.last_name = validated_data["last_name"]

                user_profile, _ = UserProfile.objects.update_or_create(defaults={
                    "dob": validated_data['dob'],
                    "gender": validated_data['gender']
                }, user_id=user.id)

                user_profile.save()
                user.save()

            return user
        except Exception as e:
            print(e)
        return None
