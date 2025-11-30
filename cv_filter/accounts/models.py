import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model that stores a UUID as the primary key.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
