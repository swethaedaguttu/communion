# create_user_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from events.models import UserProfile

class Command(BaseCommand):
    help = 'Create UserProfile for all existing users'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        for user in users:
            # Check if UserProfile already exists
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Profile created for user: {user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'Profile already exists for user: {user.username}'))
