import json
from typing import Optional

from django.core.cache import cache
from pydantic import BaseModel


class ChatRoom(BaseModel):
    chat_id: Optional[str]
    online: list[str]
    typing: list[str]

    @property
    def key(self):
        return f"thread__{self.chat_id}"

    def join(self, member_id):
        member_id = str(member_id)
        self.online.append(member_id)
        self.save()
        return self.online

    def leave(self, member_id):
        member_id = str(member_id)
        if member_id not in self.online:
            return
        self.typing_action(member_id=member_id, is_start=False)
        self.online.remove(member_id)
        if self.online:
            return self.save()
        self.destroy()

    def typing_action(self, member_id: str, is_start=True):
        if member_id not in self.online:
            return
        if is_start:
            if member_id not in self.typing:
                self.typing.append(member_id)
        else:
            if member_id in self.typing:
                self.typing.remove(member_id)
        self.save()

    @staticmethod
    def get(chat_id: str):
        value = cache.get(f'thread__{chat_id}')
        if not value:
            return None
        loaded_data = json.loads(value)
        return ChatRoom(**loaded_data)

    def save(self):
        data = self.dict()
        return cache.set(self.key, json.dumps(data))

    def destroy(self):
        cache.delete(self.key)
        del self
