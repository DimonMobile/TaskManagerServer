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
    name = models.CharField(max_length=30, primary_key=True)
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
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, primary_key=True)
    token = models.CharField(max_length=32)
    expires = models.DateTimeField()

    def __str__(self):
        return self.user.name

    class Meta:
        indexes = [
            models.Index(fields=['token'])
        ]


class Issue(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    creator = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=False, related_name='issue_creator')
    estimate = models.IntegerField(null=False)
    assignee = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, related_name='issue_assignee')
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=4096)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    issue_type = models.IntegerField(null=False)
    created = models.TimeField(auto_now_add=True)
    status = models.IntegerField(null=False, default=0)
    resolved = models.TimeField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['creator']),
            models.Index(fields=['assignee']),
            models.Index(fields=['name']),
            models.Index(fields=['status']),
            models.Index(fields=['created']),
            models.Index(fields=['issue_type'])
        ]
