from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import EmailValidator, RegexValidator


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    interests = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='default.jpg')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    email = models.EmailField(max_length=254, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    email_notifications = models.BooleanField(default=False)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=False)
    community = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    

    # New fields added
    language = models.CharField(max_length=50, blank=True, null=True)  # Language preference
    dob = models.DateField(blank=True, null=True)  # Date of birth
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True, null=True)  # Gender options

    def __str__(self):
        return f'{self.user.username} Profile'


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            email=instance.email,
            first_name=instance.first_name,
            last_name=instance.last_name
        )
    else:
        user_profile = instance.userprofile
        user_profile.email = instance.email
        user_profile.first_name = instance.first_name
        user_profile.last_name = instance.last_name
        user_profile.save()



class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('interfaith', 'Interfaith'),
    ]

    title = models.CharField(max_length=200)
    date = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200)
    description = models.TextField()
    organizer = models.CharField(max_length=100)
    members_count = models.IntegerField(default=0)  # Field to track the number of members
    image_url = models.URLField(blank=True, null=True)  # Ensure this field is correctly defined
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    rsvp_deadline = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=EVENT_TYPE_CHOICES, default='public')

    def clean(self):
        if self.date and self.date < timezone.now():
            raise ValidationError('Event date cannot be in the past.')
        if self.rsvp_deadline and self.date and self.rsvp_deadline >= self.date:
            raise ValidationError('RSVP deadline must be before the event date.')

    def __str__(self):
        return f"{self.title} ({self.type})"  # Updated string representation


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255, default="Untitled")
    message = models.TextField()
    notification_type = models.CharField(max_length=50, default='General')  # Type of notification
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification for {self.user.username}: {self.title}'


class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message from {self.name}'

class Donation(models.Model):
    # The name of the person or organization requesting the donation
    name = models.CharField(max_length=100)

    # The email of the requester, using Django's built-in EmailValidator for added security
    email = models.EmailField(validators=[EmailValidator()])

    # The phone number of the requester with basic validation for format
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Enter a valid phone number.")],
        blank=True
    )

    # The street address of the requester
    street_address = models.CharField(max_length=255, blank=True)

    # The city where the requester resides
    city = models.CharField(max_length=100, blank=True)

    # The state of the requester
    state = models.CharField(max_length=100, blank=True)

    # The zip code for the requester's address
    zip_code = models.CharField(max_length=10, blank=True)

    # The payment method chosen by the requester (if applicable)
    payment_method = models.CharField(max_length=20, choices=[
        ('upi', 'UPI'),
        ('bank_transfer', 'Bank Transfer'),
        # Additional payment methods can be added here
    ], blank=True)

    # The payment details (e.g., UPI ID, bank account number)
    payment_details = models.CharField(max_length=255, blank=True)

    # URL to the uploaded identity proof
    identity_proof = models.URLField()

    # Field to store image uploads related to the donation request
    images = models.ImageField(upload_to='donation_images/', blank=True, null=True)

    # Reference to the User model for the requester
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Associate with the User model

    # Timestamp for when the donation request was made
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional: Status of the donation request (pending, verified, rejected)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ])

    def __str__(self):
        return f"Donation Request by {self.name} ({self.email}) on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"


class HelpAlert(models.Model):
    username = models.CharField(max_length=100)
    need_help = models.CharField(max_length=255)
    description = models.TextField()
    contact_details = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='help_alerts/', blank=True, null=True)  # Add ImageField

    def __str__(self):
        return f"{self.username} - {self.need_help}"



# Model for Community Leader

class CommunityLeader(models.Model):
    name = models.CharField(max_length=100)
    community = models.CharField(max_length=100)
    description = models.TextField()
    identity_symbol = models.CharField(max_length=150, unique=True, blank=True)  # Unique identity symbol
    image = models.URLField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Automatically generate identity symbol if not set
        if not self.identity_symbol:
            self.identity_symbol = f"LEADER_{self.name.replace(' ', '_').upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.identity_symbol} - {self.name} ({self.community})'


class SocialIssuesGroup(models.Model):
    name = models.CharField(max_length=100)
    topic = models.CharField(max_length=100)
    description = models.TextField()
    image = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


from django.db import models

class GroupConversation(models.Model):
    group = models.ForeignKey(SocialIssuesGroup, on_delete=models.CASCADE, related_name='conversations')
    user_profile = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user_profile.user.username} - {self.group.name}'

class Attachment(models.Model):
    conversation = models.ForeignKey(GroupConversation, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Attachment for {self.conversation}'



class Message(models.Model):
    content = models.TextField()  # To store the message content
    leader = models.ForeignKey(CommunityLeader, on_delete=models.CASCADE)  # Link to the Leader model
    sender = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the User model (the sender)
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set the timestamp when the message is created

    def __str__(self):
        return f"Message from {self.sender.username} to {self.leader.name} at {self.created_at}"

    class Meta:
        ordering = ['-created_at']  # Optional: order messages by created time descending
