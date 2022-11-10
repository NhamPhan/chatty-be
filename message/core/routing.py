from django.urls import re_path

from .views import GeneralConsumer, ChatRoomConsumer

websocket_urlpatterns = [
    re_path(r"^general$", GeneralConsumer.as_asgi()),
    re_path(r"^chat/(?P<chat_id>[0-9A-Fa-f-]+)$", ChatRoomConsumer.as_asgi()),
]
