from django.urls import path
from . import views
urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('chat/<int:chatroom_id>/', views.chat_details, name='chat_detail'),
    path('new/<int:p_id>/', views.start_chat, name='start_chat'),
    # path('delete/<int:chat_id>/', views.delete_chat, name='delete_chat'),
]