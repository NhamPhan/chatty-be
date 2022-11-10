from django.contrib.auth import get_user_model
from rest_framework import serializers

from message.models import Contact, Notification
from .user import UserViewSerializer

User = get_user_model()


class CreateFriendRequestSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=True)
    friend_id = serializers.UUIDField(required=True)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    @classmethod
    def validate_user_id(cls, value):
        user = User.objects.get(id=value)
        if not user:
            raise serializers.ValidationError("User not exist")
        return user.id

    @classmethod
    def validate_friend_id(cls, value):
        return cls.validate_user_id(value)


class ProcessFriendRequestSerializer(serializers.ModelSerializer):
    notification_id = serializers.UUIDField(required=False)

    class Meta:
        model = Contact
        fields = ("is_active", "notification_id")

    @classmethod
    def validate_notification_id(cls, value):
        notification = Notification.objects.get(id=value)
        if not notification:
            raise serializers.ValidationError("Invalid request")
        return notification.id


class ContactSerializer(serializers.ModelSerializer):
    friend = UserViewSerializer(required=False)

    class Meta:
        model = Contact
        fields = ("user_id", "friend_id", "friend")

    @classmethod
    def get_friend(cls, obj):
        return User.objects.get(id=obj.user_id)


class DeleteNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id",)

    @classmethod
    def validate_id(cls, value):
        notification = Notification.objects.get(id=value)
        if not notification or not notification.is_deleted:
            raise serializers.ValidationError("Invalid request")
        return value
