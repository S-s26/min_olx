from django.contrib import admin
from chat.models import chatroom,message

# Register your models here.

class messagea(admin.TabularInline):
    model = message
    extra = 1
    fields = ('message','sender')



@admin.register(chatroom)
class ProductAdmin(admin.ModelAdmin):
     inlines = [messagea]
     model = chatroom
     list_display=['product', 'buyer', 'seller', 'created_at']