from django import forms
from django.contrib.auth.models import User  # Import User model
from django.contrib.auth.forms import UserCreationForm 
from django.core.validators import EmailValidator, RegexValidator

from .models import (
    Event,  Notification,  UserProfile, Donation, CommunityLeader, SocialIssuesGroup, GroupConversation, 

)
from django.contrib.auth.forms import PasswordChangeForm
class PasswordUpdateForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')




class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'date', 'location', 'description', 'organizer','image_url', 'max_participants', 'rsvp_deadline', 'type']


class UserRegistrationForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords must match.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hash the password
        if commit:
            user.save()
        return user




class ProfileEditForm(forms.ModelForm):  # This should be correct
    class Meta:
        model = UserProfile
        fields = ['location', 'interests']

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture.size > 5 * 1024 * 1024:  # Limit size to 5 MB
            raise forms.ValidationError("Image file too large ( > 5 MB )")
        return profile_picture

class ProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

class NotificationPreferencesForm(forms.ModelForm):
    email_notifications = forms.BooleanField(required=False, label="Receive email notifications")
    sms_notifications = forms.BooleanField(required=False, label="Receive SMS notifications")
    push_notifications = forms.BooleanField(required=False, label="Receive push notifications")
    phone_number = forms.CharField(max_length=15, required=False, label="Phone Number")  # Include phone number

    class Meta:
        model = UserProfile
        fields = ['email_notifications', 'sms_notifications', 'push_notifications', 'phone_number']  # Add phone number to fields

    def save(self, commit=True):
        user_profile = super().save(commit=False)  # Save but don't commit to the database yet
        user_profile.email_notifications = self.cleaned_data['email_notifications']
        user_profile.sms_notifications = self.cleaned_data['sms_notifications']
        user_profile.push_notifications = self.cleaned_data['push_notifications']
        user_profile.phone_number = self.cleaned_data['phone_number']  # Save the phone number
        
        if commit:
            user_profile.save()  # Commit to the database
        return user_profile  # Return the saved instance



class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'first_name',
            'last_name',
            'email',  # Including email for updates
            'bio',
            'location',
            'interests',
            'profile_picture',
            'phone_number',
            'email_verified',  # Track if the user's email is verified
            'email_notifications',
            'sms_notifications',
            'push_notifications',
            'country',
            'state',
            'language',
            'dob',
            'gender',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'custom-file-input'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
        }


class DonationForm(forms.Form):
    # The name of the donor
    name = forms.CharField(
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'Enter your name'})
    )

    # The email of the donor
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'})
    )

    # The phone number of the donor
    phone_number = forms.CharField(
        max_length=15, 
        required=False,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Enter a valid phone number.")],
        widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number'})
    )

    # The street address of the donor
    street_address = forms.CharField(
        max_length=255, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Street Address'})
    )

    # The city where the donor resides
    city = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'City'})
    )

    # The state of the donor
    state = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'State'})
    )

    # The zip code for the donor's address
    zip_code = forms.CharField(
        max_length=10, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'ZIP Code'})
    )

    # The payment method chosen by the donor
    payment_method = forms.ChoiceField(
        choices=[
            ('upi', 'UPI'),
            ('bank_transfer', 'Bank Transfer'),
            # Add more payment methods as needed
        ], 
        required=True,
        widget=forms.Select(attrs={'placeholder': 'Select Payment Method'})
    )

    # The payment details (e.g., UPI ID, bank account number)
    payment_details = forms.CharField(
        max_length=255, 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter payment details (UPI ID/Account Number)'})
    )

    # File field for identity proof
    identity_proof = forms.FileField(
        required=True,
        label='Identity Proof',
        help_text='Upload your identity proof (e.g., Aadhar, Passport).'
    )

    # Optional field for images related to the donation
    images = forms.ImageField(
        required=False, 
        label='Additional Images',
        help_text='Upload any additional images (optional).'
    )

    # Hidden field for username (fetched from User profile)
    username = forms.CharField(
        max_length=150, 
        widget=forms.HiddenInput(), 
        required=False
    )

    def __init__(self, *args, **kwargs):
        # This allows you to set the username dynamically
        username = kwargs.pop('username', None)
        super(DonationForm, self).__init__(*args, **kwargs)
        if username:
            self.fields['username'].initial = username

class CommunityLeaderForm(forms.ModelForm):
    class Meta:
        model = CommunityLeader
        fields = ['name', 'community', 'description', 'image']  # Included 'image' field
        labels = {
            'name': 'Leader Name',
            'community': 'Community Name',
            'description': 'Description',
            'image': 'Image URL',
        }
        help_texts = {
            'description': 'Provide a brief description of the leader and their contributions.',
            'image': 'Optional: Provide an image URL representing the community leader.',
        }


class SocialIssuesGroupForm(forms.ModelForm):
    class Meta:
        model = SocialIssuesGroup
        fields = ['name', 'topic', 'description', 'image']  # Included 'image' field
        labels = {
            'name': 'Group Name',
            'topic': 'Topic',
            'description': 'Description',
            'image': 'Image URL',
        }
        help_texts = {
            'description': 'Provide a brief description of the group and its purpose.',
            'image': 'Optional: Provide an image URL representing the group.',
        }

class GroupConversationForm(forms.ModelForm):
    attachment = forms.FileField(required=False)

    class Meta:
        model = GroupConversation
        fields = ['message', 'attachment']  # Include both message and attachment fields
        
def clean_attachment(self):
    file = self.cleaned_data.get('attachment')
    if file and file.size > 10 * 1024 * 1024:  # 10MB size limit
        raise forms.ValidationError('File size exceeds 10MB')
    return file

