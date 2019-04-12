from django.db import models


class UserProfile(models.Model):
    name = models.CharField(max_length=20)
    password = models.CharField(max_length=256)
    email = models.CharField(max_length=48)
    lang = models.CharField(max_length=10, default="en_US")
    register_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['email'])
        ]
