from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Expose the custom user model in the Django admin using the built-in User admin.
    """

    model = User
