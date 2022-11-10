from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters import rest_framework as filters

from message.models import Contact


class UserFilter(filters.FilterSet):
    is_friend = filters.BooleanFilter(method="filter_friend")
    name = filters.CharFilter(method="filter_name")

    class Meta:
        model = get_user_model()
        fields = ["email", "username"]
        exclude = ["password"]

    def filter_friend(self, queryset, name, value):
        if not hasattr(self.request, "user"):
            return queryset.none
        user = self.request.user

        if value is not None:
            contacts = Contact.objects.filter(
                user_id=user.id, is_active=True, is_deleted=False
            ).all()
            friend_ids = [contact.friend_id for contact in contacts]
            lookup = Q(id__in=friend_ids) if value else (~Q(id__in=friend_ids))
            return queryset.filter(is_active=True).filter(lookup).exclude(id=user.id)
        return queryset

    def filter_name(self, queryset, name, value):
        if hasattr(self.request, "user"):
            queryset = queryset.exclude(id=self.request.user.id)
        lookup = Q(first_name__contains=value) | Q(last_name__contains=value)
        return queryset.filter(lookup)
