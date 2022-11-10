from rest_framework import serializers

from message.models import User, Thread, Member, MemberPreference, Message
from .user import UserViewSerializer
from .message import MessageViewSerializer


class ThreadCreateSerializer(serializers.Serializer):
    member_ids = serializers.ListField(child=serializers.UUIDField())
    name = serializers.CharField(required=False, max_length=250, allow_blank=True, allow_null=True)

    @staticmethod
    def validate_member_ids(value):
        result = User.objects.filter(id__in=value, is_active=True)
        if result.count() == len(value):
            return result
        raise serializers.ValidationError({"detail": "Some user is incorrect"})


class MemberPreferenceViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberPreference
        fields = ["is_creator", "is_leader"]


class MemberViewSerializer(serializers.ModelSerializer):
    user = UserViewSerializer(required=False)
    preference = serializers.SerializerMethodField(method_name="get_preference")

    class Meta:
        model = Member
        fields = ["id", "user", "thread_id", "preference"]

    def get_preference(self, obj):
        preference = MemberPreference.objects.filter(member_id=obj.id).first()
        return MemberPreferenceViewSerializer(preference).data


class ThreadViewSerializer(serializers.ModelSerializer):
    members = MemberViewSerializer(source="member_set", many=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = [
            "id",
            "name",
            "members",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "last_message",
        ]

    @staticmethod
    def get_last_message(obj):
        thread_id = obj.id
        message = (
            Message.objects.filter(
                thread_id=thread_id,
                is_deleted=False,
                thread__is_deleted=False,
                is_sent=True,
            )
            .order_by("created_at")
            .first()
        )
        return MessageViewSerializer(message).data if message else None
