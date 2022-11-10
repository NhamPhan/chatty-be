from typing import Optional
from uuid import UUID

from channels.db import database_sync_to_async

from message.core.models import ChatRoom
from message.models import User, Thread, Message
from message.serializers import UserViewSerializer


class JoinRoomCheckMixin:
    @database_sync_to_async
    def check_valid(self, user: User, thread: Thread):
        if not user or not thread:
            return False
        count = thread.member_set.filter(
            user_id=user.id, memberpreference__is_deleted=False
        ).count()
        return count > 0


class PersistentMixin:
    @database_sync_to_async
    def get_chat(self, pk: UUID) -> Optional[ChatRoom]:
        thread = Thread.objects.filter(pk=pk, is_deleted=False).first()
        if not thread:
            return None
        chat_room: Optional[ChatRoom] = ChatRoom.get(chat_id=str(thread.id))
        if not chat_room:
            chat_room = ChatRoom(chat_id=str(thread.id), online=[], typing=[])
            chat_room.save()
        return chat_room

    @database_sync_to_async
    def typing(self, start=True):
        chat_id = self.room_subscribe
        if not chat_id:
            return

        room = ChatRoom.get(chat_id=chat_id)
        if not room:
            return
        user = self.scope['user']
        room.typing_action(member_id=str(user.id), is_start=start)

    @database_sync_to_async
    def current_users(self, thread: ChatRoom):
        room: Optional[ChatRoom] = ChatRoom.get(chat_id=thread.chat_id)
        if not room:
            return []
        members = User.objects.filter(id__in=room.online)
        return [UserViewSerializer(user).data for user in members]

    @database_sync_to_async
    def leave_thread(self, thread_id: str):
        user: User = self.scope["user"]
        room: Optional[ChatRoom] = ChatRoom.get(chat_id=thread_id)
        if not room:
            return
        room.leave(member_id=user.id)

    @database_sync_to_async
    def join_thread(self, thread_id):
        user: User = self.scope["user"]
        room: Optional[ChatRoom] = ChatRoom.get(chat_id=thread_id)
        if room and str(user.id) not in room.online:
            room.join(member_id=user.id)

    @database_sync_to_async
    def create_message(self, message):
        user: User = self.scope["user"]
        chat_id = self.room_subscribe
        if not chat_id:
            return
        return Message.objects.create(
            created_by=user.id,
            updated_by=user.id,
            thread_id=chat_id,
            content=message,
            is_sent=True,
        )
