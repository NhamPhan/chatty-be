from django.conf import settings
from django.db.models import Q
from rest_framework import serializers

from message.models import UserProfile, Contact, Notification, User


class ProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(required=False)

    class Meta:
        model = UserProfile
        fields = ("dob", "avatar", "id", "active_avatar", "avatars")

    @classmethod
    def get_avatar(cls, obj):
        if not obj.avatars:
            return None
        if -1 < obj.active_avatar < len(obj.avatars):
            return obj.avatars[obj.active_avatar]
        return None


class UserViewSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)
    contact_type = serializers.SerializerMethodField(method_name="get_contact_type")
    notification_id = serializers.SerializerMethodField(
        method_name="get_notification_id"
    )

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "username",
            "last_name",
            "profile",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
            "email",
            "contact_type",
            "notification_id",
        )

    def get_contact_type(self, obj):
        request = self.context.get("request")
        user = None
        if request and hasattr(request, "user"):
            user = request.user
        if not user:
            return None

        if obj.id == user.id:
            return "me"

        me = self._get_pending_friend_request(user_id=user.id, friend_id=obj.id)
        if me:
            return "pending_sent"
        other_user = self._get_pending_friend_request(user_id=obj.id, friend_id=user.id)
        if other_user:
            return "pending"

        contact = Contact.objects.filter(
            user_id=user.id, friend_id=obj.id, is_deleted=False
        ).first()
        if not (contact and contact.is_active):
            return "stranger"
        return "friend"

    @staticmethod
    def _get_pending_friend_request(user_id, friend_id):
        notification_type = Notification.Type.FRIEND_REQUEST
        lookup = Q(
            payload__user_id=str(user_id),
            payload__friend_id=str(friend_id),
            notification_type=notification_type,
            is_pending=True,
            is_deleted=False,
        )
        return Notification.objects.filter(lookup).first()

    def get_notification_id(self, obj):
        notification_id = self.context.get("notification_id")
        if notification_id:
            return notification_id

        request = self.context.get("request")
        user = None
        if request and hasattr(request, "user"):
            user = request.user
        if not user:
            return None

        notification = self._get_pending_friend_request(
            user_id=obj.id, friend_id=user.id
        )
        if not notification:
            return None
        return notification.id


class UpdateProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=250, required=True)
    last_name = serializers.CharField(max_length=250, required=True)
    dob = serializers.DateField(required=True)
    gender = serializers.ChoiceField(choices=settings.GENDER_CHOICE, default="male")

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'dob', 'gender')
