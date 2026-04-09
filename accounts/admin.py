from django.contrib import admin
from accounts.models import customUser
class customUserAdmin(admin.ModelAdmin):
    list_display=['username','first_name','last_name','email','phone','address']


# Register your models here.
admin.site.register(customUser,customUserAdmin)

# Register your models here.
