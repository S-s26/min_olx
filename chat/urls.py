from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('chat/<int:chatroom_id>/', views.chat_details, name='chat_detail'),
    path('chat/<int:chatroom_id>/history/', views.chat_history, name='chat_history'),
    path('new/<int:p_id>/', views.start_chat, name='start_chat'),
]