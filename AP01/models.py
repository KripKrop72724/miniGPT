from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class Conversation(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Prompt(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='prompts', on_delete=models.CASCADE)
    text = models.TextField()
    response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='files/', null=True, blank=True)

    def __str__(self):
        return f"Prompt in {self.conversation.name}"


class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
