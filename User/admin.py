from django.contrib import admin
from .models import Profile, filedata, LoginHistory

# Register your models here.
admin.site.register(Profile)
admin.site.register(filedata)
admin.site.register(LoginHistory)