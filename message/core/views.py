import json

from djangochannelsrestframework.decorators import action as view_action
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.mixins import ListModelMixin
from djangochannelsrestframework.observer import model_observer

from message.core.mixins import JoinRoomCheckMixin, PersistentMixin
from message.core.models import ChatRoom
from message.core.serializers import MessageViewSerializer, MessageCreateSerializer
from message.models import Thread, Notification, Message
from message.serializers import ThreadViewSerializer


class GeneralConsumer(ListModelMixin, GenericAsyncAPIConsumer):
    queryset = Thread.objects.all()
    serializer_class = ThreadViewSerializer

    @model_observer(Thread, serializer_class=ThreadViewSerializer)
    async def thread_activity(
        self,
        message: ThreadViewSerializer,
        observer=None,
        subscribing_request_ids=None,
        **kwargs,
    ):
        for request_id in subscribing_request_ids:
            message_body = dict(request_id=request_id)
            message_body.update(message)
            await self.send_json(message_body)

    @thread_activity.groups_for_signal
    def thread_activity(self, instance: Thread, **kwargs):
        for member in instance.members.all():
            yield f"general__{member.pk}"

    @thread_activity.groups_for_consumer
    def thread_activity(self, user=None, **kwargs):
        if user is not None:
            yield f"general__{user.pk}"

    @model_observer(Notification)
    async def notification_activity(
        self,
        message: ThreadViewSerializer,
        observer=None,
        subscribing_request_ids=None,
        **kwargs,
    ):
        if subscribing_request_ids is None:
            subscribing_request_ids = []

    @view_action()
    async def subscribe_general_consumer(self, request_id, **kwargs):
        if "user" in self.scope and self.scope["user"].is_authenticated:
            user = self.scope["user"]
            await self.thread_activity.subscribe(user=user, request_id=request_id)


class ChatRoomConsumer(
    PersistentMixin, JoinRoomCheckMixin, ListModelMixin, GenericAsyncAPIConsumer
):
    queryset = Thread.objects.all()
    serializer_class = ThreadViewSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_subscribe = None

    @model_observer(Message, serializer_class=MessageViewSerializer)
    async def message_activity(
        self,
        message,
        observer=None,
        **kwargs,
    ):
        await self.send_json({"type": "message_activity", "data": message})

    @message_activity.groups_for_signal
    def message_activity(self, instance: Message, **kwargs):
        yield f"thread__{instance.thread_id}"
        yield f"pk__{instance.pk}"

    @message_activity.groups_for_consumer
    def message_activity(self, user=None, chat_id=None, **kwargs):
        if user and chat_id:
            yield ChatRoom(chat_id=chat_id, online=[], typing=[]).key

    @view_action()
    async def subscribe_to_chat(self, chat_id, **kwargs):
        if "user" in self.scope and self.scope["user"].is_authenticated:
            user = self.scope["user"]
            thread = await self.get_chat(pk=chat_id)
            if not self.check_valid(user=user, thread=thread):
                return
            await self.message_activity.subscribe(user=user, chat_id=chat_id)

    @view_action()
    async def send_message(self, message, **kwargs):
        await self.create_message(message=message)

    @view_action()
    async def join(self, chat_id, **kwargs):
        self.room_subscribe = chat_id
        await self.join_thread(chat_id)
        await self.notify_users()

    @view_action()
    async def leave(self, chat_id, **kwargs):
        await self.leave_thread(chat_id)

    @view_action()
    async def seen_messages(self, messages: list[str], **kwargs):
        pass

    @view_action()
    async def typing_action(self, start=True, **kwargs):
        await self.typing(start=start)
        await self.notify_typing()

    async def disconnect(self, code):
        if hasattr(self, "room_subscribe"):
            await self.leave_thread(self.room_subscribe)
            await self.notify_users()
        await super().disconnect(code)

    async def notify_typing(self):
        room: ChatRoom = await self.get_chat(self.room_subscribe)
        if not room:
            return
        payload = {"type": "update_typing", "typing": room.typing}
        await self.notify(payload=payload)

    async def notify_users(self):
        room: ChatRoom = await self.get_chat(self.room_subscribe)
        if not room:
            return
        payload = {"type": "update_users", "online": await self.current_users(room)}
        await self.notify(payload=payload)

    async def notify(self, payload):
        for group in self.groups:
            await self.channel_layer.group_send(group, payload)

    async def update_users(self, event: dict):
        await self.send(text_data=json.dumps({"online": event["online"], "type": "update_typing"}))

    async def update_typing(self, event: dict):
        await self.send(text_data=json.dumps({"typing": event["typing"], "type": "update_users"}))
