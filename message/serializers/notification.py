from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .user import UserViewSerializer
from message.models import Notification

UserModel = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    payload = serializers.SerializerMethodField(method_name="build_payload")

    class Meta:
        model = Notification
        fields = (
            "id",
            "payload",
            "is_pending",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
            "notification_type",
            "recipient_id",
            "is_seen",
        )

    def build_payload(self, obj):
        if obj.notification_type == Notification.Type.FRIEND_REQUEST:
            user = UserModel.objects.get(id=obj.payload["user_id"])
            friend = UserModel.objects.get(id=obj.payload["friend_id"])
            serialized_user = UserViewSerializer(user, context=self.context)
            serialized_friend = UserViewSerializer(friend, context=self.context)
            return {
                "user": serialized_user.data,
                "friend": serialized_friend.data,
            }

        if obj.notification_type == Notification.Type.INCOMING_MESSAGE:
            # TODO: payload for message
            pass

        return obj.payload


class NotificationUpdateManySerializer(serializers.ModelSerializer):
    is_seen = serializers.BooleanField(default=True)
    id_list = serializers.ListField(child=serializers.UUIDField())

    class Meta:
        model = Notification
        fields = ('is_seen', 'id_list')

    def validate_id_list(self, value):
        result = Notification.objects.filter(id__in=value, is_seen=False)
        if result.count() == len(value):
            return result
        raise serializers.ValidationError({'detail': 'Some notification is incorrect.'})
