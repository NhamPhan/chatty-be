from rest_framework import serializers

from message.models import Message


class MessageViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "content",
            "thread_id",
            "created_by",
            "updated_at",
            "created_at",
            "seen_by",
        ]
