from django.db import models


class UserProfile(models.Model):
    id = models.AutoField(primary_key=True)
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


class Project(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=4096)
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['owner'])
        ]


class Token(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, primary_key=True)
    token = models.CharField(max_length=32)
    expires = models.DateTimeField()

    def __str__(self):
        return self.user.name

    class Meta:
        indexes = [
            models.Index(fields=['token'])
        ]

