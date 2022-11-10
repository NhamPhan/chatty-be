import uuid

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.postgres.fields import ArrayField
from django.db import models

from message.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4(), editable=False)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
        validators=[username_validator],
        error_messages={
            "unique": "A user with that username already exists.",
        },
    )
    first_name = models.CharField(
        verbose_name="first name", max_length=80, blank=True, null=True
    )
    last_name = models.CharField(
        verbose_name="last name", max_length=150, blank=True, null=True
    )
    email = models.EmailField(verbose_name="email address", null=True, blank=True)
    is_active = models.BooleanField(verbose_name="active", default=True)
    is_staff = models.BooleanField(verbose_name="staff status", default=False)
    is_superuser = models.BooleanField(default=False, verbose_name="superuser")

    date_joined = models.DateTimeField(
        verbose_name="date joined", auto_now_add=True, editable=False
    )

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        return True

    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        return True

    def __str__(self):
        return "{} {}".format(self.last_name, self.first_name)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    updated_at = models.DateTimeField(editable=False, auto_now=True)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    created_by = models.UUIDField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)

    remark = models.CharField(max_length=250, blank=True, null=True)
    is_deleted = models.BooleanField(default=False, null=False, blank=False)

    class Meta:
        abstract = True


class UserProfile(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    gender = models.CharField(
        choices=settings.GENDER_CHOICE, max_length=6, blank=True, null=True
    )
    dob = models.DateField(blank=True, null=True)
    avatars = ArrayField(models.TextField(), default=list)
    active_avatar = models.IntegerField(default=0)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def get_avatar(self):
        if not self.avatars:
            return -1
        if self.active_avatar < len(self.avatars):
            return self.avatars[self.active_avatar]

    def __str__(self):  # __unicode__ on Python 2
        return self.user.__str__()


class Thread(BaseModel):
    name = models.CharField(max_length=250, blank=True, null=True)
    members = models.ManyToManyField(User, through="Member")

    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        return self.name


class Message(BaseModel):
    content = models.TextField(blank=False, null=False)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)

    is_sent = models.BooleanField(blank=False, null=False, default=False)
    seen_by = ArrayField(
        models.UUIDField(),
        blank=True,
        null=True,
        default=list,
        verbose_name="Member seen the message",
    )

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return str(self.id)


class Member(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Conversation member"
        verbose_name_plural = "Conversation members"

    def __str__(self):
        return self.user.__str__()


class MemberPreference(BaseModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    member = models.OneToOneField(to=Member, on_delete=models.CASCADE)

    is_creator = models.BooleanField(default=False, null=False, blank=False)
    is_leader = models.BooleanField(default=False, null=False, blank=False)

    class Meta:
        verbose_name = "Member preference"
        verbose_name_plural = "Member preferences"

    def __str__(self):
        return str(self.id)


class Contact(BaseModel):
    user_id = models.UUIDField(null=True, blank=True)
    friend_id = models.UUIDField(null=True, blank=True)

    is_active = models.BooleanField(default=True, null=False, blank=False)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        unique_together = ("user_id", "friend_id")

    def __str__(self):
        return f"{self.user_id}__{self.friend_id}"


class Notification(BaseModel):
    class Type(models.TextChoices):
        FRIEND_REQUEST = "friend_request", "Friend request"
        INCOMING_MESSAGE = "incoming_message", "Incoming message"

        __empty__ = "default"

    notification_type = models.CharField(
        max_length=100,
        choices=Type.choices,
        default=Type.INCOMING_MESSAGE,
    )
    recipient = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    is_pending = models.BooleanField(default=True, null=False, blank=False)
    is_sent = models.BooleanField(default=False, null=False, blank=False)
    is_seen = models.BooleanField(default=False, null=False, blank=False)

    payload = models.JSONField()

    def __str__(self):
        return str(self.id)
