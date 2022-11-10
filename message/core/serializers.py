from rest_framework import serializers

from message.models import Message, Thread


class MessageViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["content", "thread_id"]

    def validate_thread_id(self, value):
        thread = Thread.objects.filter(pk=value).first()
        if not thread:
            raise serializers.ValidationError({'detail': 'Some notification is incorrect.'})
        return thread.id
