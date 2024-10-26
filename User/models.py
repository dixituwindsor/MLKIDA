from django.core.files.storage import FileSystemStorage
from django.db import models
from django.contrib.auth.models import User
import uuid
# Create your models here.


class Profile(User):
    profile_id = models.UUIDField(default=uuid.uuid4, unique=True,
                                    primary_key=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.first_name)

    class Meta:
        ordering = ['created']


class LoginHistory(models.Model):
    user = models.TextField(max_length=100, blank=True, null=True)
    login_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.user)


class filedata(models.Model):
    username = models.CharField(max_length=100, blank=True, null=True)
    max_size_in_bytes = 2 * 1073741824 # allow files upto 2 gb
    title = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='uploaded_videos/', null=False, blank=False, max_length=max_size_in_bytes)
    predatory_mites = models.CharField(max_length=10)
    feeder_mites = models.CharField(max_length=10)
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.title)

