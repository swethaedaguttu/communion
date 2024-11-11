# events/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.core.files.storage import FileSystemStorage
from django.core.management.base import BaseCommand
from .models import (
    Event,
    Notification,
    UserProfile,
    Donation, HelpAlert,  CommunityLeader, SocialIssuesGroup, GroupConversation, Message, Attachment


 # Import your UserProfile model correctly
)

from .forms import  EventForm, UserRegistrationForm,  ProfileUpdateForm, ProfileEditForm, PasswordUpdateForm, NotificationPreferencesForm, ProfilePictureForm, DonationForm, CommunityLeaderForm, SocialIssuesGroupForm, GroupConversationForm


 # Import your forms
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required  # Import login_required
from django.contrib.auth.views import LoginView
from django.utils import timezone
from django.core.paginator import Paginator
from django_otp.decorators import otp_required
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import IntegrityError
from django.contrib.auth.models import User  # Import the User model
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.views import View
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import generics
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django.http import JsonResponse
import json

import logging

logger = logging.getLogger(__name__)


import openai  # Assuming OpenAI API is used for AI-powered features
import random


def index(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    events = Event.objects.all()[:4]
    leaders = CommunityLeader.objects.all()[:4]
    groups = SocialIssuesGroup.objects.all()[:4]
    help_alerts = HelpAlert.objects.all().order_by('-created_at')[:4]  # Optional: Order by creation date

    search_query = request.GET.get('search', '')
    if search_query:
        communities = communities.filter(name__icontains=search_query)
        events = events.filter(title__icontains=search_query)


    context = {
        'events': events,
        'user_profile': user_profile,
        'leaders': leaders,
        'groups': groups,
        'help_alerts': help_alerts,

    }
    return render(request, 'events/index.html', context)

# Authentication Views

# Custom login view
class CustomLoginView(LoginView):
    template_name = 'events/login.html'  # Your login template

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password.')
        return super().form_invalid(form)

# Registration view
def register(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        # Check for empty fields
        if not uname or not email or not pass1 or not pass2:
            messages.error(request, "All fields are required.")
            return redirect('register')

        # Check if the username already exists
        if User.objects.filter(username=uname).exists():
            messages.error(request, "Username already exists. Please choose a different one.")
            return redirect('register')

        # Check if the email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists. Please choose a different one.")
            return redirect('register')

        # Check if passwords match
        if pass1 != pass2:
            messages.error(request, "Your password and confirm password do not match!")
            return redirect('register')

        # Create the user
        try:
            my_user = User.objects.create_user(username=uname, email=email, password=pass1)
            my_user.save()

            # Do not manually create the UserProfile, the post_save signal will handle it
            
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('login')
        except Exception as e:
            print(f"Error occurred during user registration: {e}")
            messages.error(request, "An error occurred during registration. Please try again.")
            return redirect('register')

    return render(request, 'events/register.html')
# Login view (use Django's built-in view or customize this)

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')  # Ensure this matches the input name in the form

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return HttpResponse("Username or Password is incorrect!!!")

    return render(request, 'events/login.html')


# Logout view
def user_logout(request):
    logout(request)
    return redirect('login')

# Command to create UserProfiles for existing users

# Community Views
@login_required
def about_us(request):
    return render(request, 'events/about_us.html')  # Adjust the template name as necessary
@login_required
def contact(request):
    return render(request, 'events/contact.html')  # Adjust the template name as necessary
@login_required
def profile(request):
    return render(request, 'profile.html')  # Make sure this template exists

 # Ensure only logged-in users can create communities
# Event Views

  # Ensure only logged-in users can view events
# View to list all events
def event_list_view(request):
    events = Event.objects.all()  # Get all events
    return render(request, 'events/event_list.html', {'events': events})

# View to show event details
def event_details_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)  # Get the event or return 404
    return render(request, 'events/event_details.html', {'event': event})

def join_event(request, event_id):
    # Get the event by ID
    event = get_object_or_404(Event, id=event_id)

    # Check if there is space for more participants
    if event.members_count < event.max_participants:
        # Increment the member count
        event.members_count += 1
        event.save()
        messages.success(request, f'You have successfully joined the event: {event.title}')
    else:
        messages.error(request, 'Sorry, this event is full.')

    # Redirect to the event details page or any other page
    return redirect('event_details', event_id=event.id)


# View to create a new event
def event_create_view(request):
    if request.method == 'POST':
        form = EventForm(request.POST)  # Create form instance with POST data only
        if form.is_valid():
            event = form.save(commit=False)  # Create event instance but don't save to DB yet
            event.created_by = request.user  # Assign the logged-in user

            # Ensure image URL is provided if it’s required
            if not event.image_url:
                form.add_error('image_url', 'Please provide a valid image URL.')
            else:
                try:
                    event.clean()  # Call the clean method to validate
                    event.save()  # Save the event to the database
                    messages.success(request, f'Event "{event.title}" created successfully!')
                    return redirect('event_list')  # Redirect to event list after creation
                except ValidationError as e:
                    form.add_error(None, e)  # Add validation error to form
                except Exception as e:
                    messages.error(request, 'An unexpected error occurred. Please try again.')
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = EventForm()  # Create an empty form for GET request

    return render(request, 'events/event_form.html', {'form': form})  # Render the form for creating events
            
@login_required
def create_event_view(request):
    communities = Community.objects.all()  # Fetch all communities

    if request.method == 'POST':
        # Handle form submission with some validation checks
        try:
            title = request.POST['title']
            community_id = request.POST['community']
            location = request.POST['location']
            date = request.POST['date']
            description = request.POST['description']
            organizer = request.user.username  # Organizer is the logged-in user

            # Fetch selected community, raise 404 if not found
            community = Community.objects.get(id=community_id)

            # Convert the date string to datetime if necessary
            try:
                date = timezone.make_aware(timezone.datetime.strptime(date, '%Y-%m-%dT%H:%M'))
            except ValueError:
                messages.error(request, 'Invalid date format. Please try again.')
                return render(request, 'events/event_form.html', {'communities': communities})

            # Create the new event and save it
            event = Event(title=title, location=location, date=date, description=description, organizer=organizer, community=community)
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('event_detail', event_id=event.id)

        except Community.DoesNotExist:
            messages.error(request, 'Community does not exist.')
            return render(request, 'events/event_form.html', {'communities': communities})

    return render(request, 'events/create_event.html', {'communities': communities})


@login_required
def profile_edit(request):
    user_profile = request.user.userprofile  # Assuming one-to-one relationship with User model

    if request.method == 'POST':
        try:
            # Check if the request is for updating the profile picture
            if 'profile_picture' in request.FILES:
                update_profile_picture(request, user_profile)
                messages.success(request, "Profile picture updated successfully!")
            else:
                # Update personal information
                update_personal_info(request, user_profile)
                messages.success(request, "Personal information updated successfully!")

            return redirect('profile_view')  # Redirect to a profile view after successful update
        except Exception as e:
            messages.error(request, f"Error updating profile: {e}")

    # GET request: Render the profile edit form
    return render(request, 'events/profile_edit.html', {'user_profile': user_profile})

@csrf_exempt
def update_profile_picture(request):
    if request.method == 'POST':
        try:
            if request.user.is_authenticated:
                user_profile = request.user.userprofile  # Access UserProfile instead of Profile
                if 'profile_picture' in request.FILES:
                    user_profile.profile_picture = request.FILES['profile_picture']
                else:
                    user_profile.profile_picture = 'profile_pictures/default.jpg'  # Default picture if not provided
                user_profile.save()
                return JsonResponse({'success': True, 'message': 'Profile picture updated successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'User is not authenticated'}, status=403)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def update_personal_info(request):
    if request.method == 'POST':
        user_profile = get_object_or_404(UserProfile, user=request.user)

        try:
            # Update the profile fields
            user_profile.first_name = request.POST.get('first_name', user_profile.first_name)
            user_profile.last_name = request.POST.get('last_name', user_profile.last_name)
            user_profile.bio = request.POST.get('bio', user_profile.bio)
            user_profile.location = request.POST.get('location', user_profile.location)
            user_profile.country = request.POST.get('country', user_profile.country)
            user_profile.state = request.POST.get('state', user_profile.state)
            user_profile.faith_background = request.POST.get('faith_background', user_profile.faith_background)
            user_profile.language = request.POST.get('language', user_profile.language)

            # Handle date of birth (ensure it's a valid date format before assigning)
            dob = request.POST.get('dob')
            if dob:
                user_profile.dob = dob  # Assign the date as a string

            user_profile.gender = request.POST.get('gender', user_profile.gender)

            # Update the username
            new_username = request.POST.get('username', '').strip()
            if new_username and new_username != request.user.username:
                if not User.objects.filter(username=new_username).exists():
                    request.user.username = new_username
                    request.user.save()
                else:
                    return JsonResponse({'success': False, 'message': 'Username already exists.'}, status=400)

            # Save the updated profile
            user_profile.save()

            return JsonResponse({'success': True, 'message': 'Personal information updated successfully!'})
        except Exception as e:
            logger.error(f"Error updating personal info: {e}")
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

def notification_center(request):
    # Query all notifications for the logged-in user, ordered by most recent first
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'events/notifications.html', {
        'notifications': notifications
    })


# View to mark a notification as read (AJAX call)

def mark_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)

# View to delete a notification (AJAX call)

def delete_notification(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.delete()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)


@login_required
def settings_view(request):
    user_profile = UserProfile.objects.get(user=request.user)

    # Initialize forms for rendering
    password_form = PasswordChangeForm(request.user)
    notification_form = NotificationPreferencesForm(instance=user_profile)

    if request.method == 'POST':
        # Check which form was submitted based on a specific identifier
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Keep the user logged in
                messages.success(request, 'Password changed successfully!')
                return redirect('settings')  # Redirect to refresh the page
            else:
                # Collect all error messages from the password change form
                for error in password_form.errors.values():
                    messages.error(request, ' '.join(error))

        elif 'update_notifications' in request.POST:
            notification_form = NotificationPreferencesForm(request.POST, instance=user_profile)
            if notification_form.is_valid():
                # Check if SMS notifications are enabled and if the phone number is provided
                if notification_form.cleaned_data['sms_notifications'] and not notification_form.cleaned_data['phone_number']:
                    messages.error(request, 'Please add a phone number to receive SMS notifications.')
                else:
                    notification_form.save()
                    messages.success(request, 'Notification preferences updated!')
                    return redirect('settings')  # Redirect to refresh the page
            else:
                # Collect all error messages from the notification preferences form
                for error in notification_form.errors.values():
                    messages.error(request, ' '.join(error))

    # Render the settings page with the forms
    return render(request, 'events/settings.html', {
        'user_profile': user_profile,
        'password_form': password_form,
        'notification_form': notification_form
    })


@login_required
def profile_view(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)

    context = {
        'user_profile': user_profile,
    }

    return render(request, 'events/profile.html', context)


# View for editing user profile


# View for adding an activity
# Function to validate UPI ID format
def validate_upi(upi_id):
    return re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+$', upi_id)

@login_required  # Ensure the user is logged in
def donation_page(request):
    if request.method == 'POST':
        form = DonationForm(request.POST, request.FILES)

        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            payment_details = form.cleaned_data['payment_details']

            # Validate UPI ID format if payment method is UPI
            if payment_method == 'upi' and not validate_upi(payment_details):
                return JsonResponse({'success': False, 'message': 'Invalid UPI ID format.'}, status=400)

            # Handle identity proof file upload securely
            identity_proof = request.FILES.get('identity_proof')
            if identity_proof:
                fs = FileSystemStorage()
                filename = fs.save(identity_proof.name, identity_proof)
                uploaded_file_url = fs.url(filename)

                # Create the donation request instance
                donation = Donation(
                    name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'],
                    phone_number=form.cleaned_data['phone_number'],
                    street_address=form.cleaned_data['street_address'],
                    city=form.cleaned_data['city'],
                    state=form.cleaned_data['state'],
                    zip_code=form.cleaned_data['zip_code'],
                    payment_method=payment_method,
                    payment_details=payment_details,
                    identity_proof=uploaded_file_url,
                    user=request.user,  # Associate with authenticated user
                    status='pending'
                )
                donation.save()  # Save the donation request to the database

                # Respond with success message and donation ID for AJAX
                return JsonResponse({'success': True, 'message': 'Donation request submitted successfully!', 'donation_id': donation.id})

            else:
                return JsonResponse({'success': False, 'message': 'Please upload an identity proof.'}, status=400)

    else:
        form = DonationForm()

    # Render the donation form for GET requests
    return render(request, 'events/donation_page.html', {'form': form})

@login_required
def donation_success(request, donation_id):
    try:
        donation = Donation.objects.get(id=donation_id)  # Retrieve the donation request details
    except Donation.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Donation request not found.'}, status=404)

    return render(request, 'events\donation_success.html', {'donation': donation})  # Render a success template with donation request details

@login_required
def donation_list(request):
    donations = Donation.objects.filter(user=request.user)  # Fetch donation requests for the logged-in user
    return render(request, 'events\donation_list.html', {'donations': donations})  # Render the donation list template

# View to handle all charitable initiatives

@csrf_exempt  # Only if you are sure about CSRF token handling
def help_alert(request):
    if request.method == "POST":
        # Handle form submission, including image upload
        image = request.FILES.get('image')  # Retrieve the uploaded image
        help_request = HelpAlert.objects.create(  # Corrected model name
            username=request.POST['username'],
            need_help=request.POST['needHelp'],
            description=request.POST['description'],
            contact_details=request.POST['contactDetails'],
            image=image  # Make sure the image file is included
        )
        
        # Return JSON response with the new help request data
        return JsonResponse({
            'status': 'success',
            'request': {
                'username': help_request.username,
                'need_help': help_request.need_help,
                'description': help_request.description,
                'contact_details': help_request.contact_details,
                'created_at': help_request.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'image_url': help_request.image.url if help_request.image else None  # Provide image URL if available
            }
        })

    # For GET requests, render the existing help requests
    help_requests = HelpAlert.objects.all()  # Ensure the correct model is used
    return render(request, 'events/help_alert.html', {'help_requests': help_requests})

# Display a specific help alert's details
def help_alert_details(request, id):
    help_alert = get_object_or_404(HelpAlert, id=id)  # Get the specific help alert or 404 if not found
    context = {
        'help_alert': help_alert
    }
    return render(request, 'events/help_alert_deatils.html', context)  # Corrected template name




def submit_help_alert(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data['username']
        need_help = data['needHelp']
        description = data['description']
        contact_details = data['contactDetails']

        # Create a new help request
        help_alert = HelpAlert.objects.create(
            username=username,
            need_help=need_help,
            description=description,
            contact_details=contact_details
        )

        # Create notification message
        notification_message = f"{username} needs help: {need_help}. Description: {description}."

        # Notify other users
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'notifications_group',  # Same group name used in the consumer
            {
                'type': 'send_notification',
                'message': notification_message
            }
        )

        return JsonResponse({'status': 'success', 'message': 'Help Alert submitted.'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)

# Function to generate a unique identity symbol
def generate_identity_symbol(name, prefix="LEADER_"):
    """
    Generates an identity symbol for a community leader.
    The identity symbol will be the prefix followed by the leader's name formatted as uppercase
    and with spaces replaced by underscores. If the name is not provided, a default symbol is returned.
    """
    if not name:  # Return a default symbol if no name is provided
        return "LEADER_DEFAULT"
    
    base_symbol = name.replace(" ", "_").upper()  # Format the name
    return f"{prefix}{base_symbol}"

# View for listing community leaders
def community_leaders_list(request):
    leaders = CommunityLeader.objects.all()  # Fetch all leaders
    return render(request, 'events/community_leaders_list.html', {'leaders': leaders})

# View for creating a new leader
def create_community_leader(request):
    if request.method == 'POST':
        form = CommunityLeaderForm(request.POST)
        if form.is_valid():  # Validate form data
            form.save()  # Save data to the database
            return redirect('community_leaders_list')
    else:
        form = CommunityLeaderForm()
    return render(request, 'events/create_community_leader.html', {'form': form})

# View for leader details
def community_leader_detail(request, identity_symbol):
    leader = get_object_or_404(CommunityLeader, identity_symbol=identity_symbol)
    return render(request, 'events/community_leader_detail.html', {'leader': leader})

# View for listing social issues groups
def social_issues_groups_list(request):
    groups = SocialIssuesGroup.objects.all()  # Fetch all groups
    return render(request, 'events/social_issues_groups_list.html', {'groups': groups})

# View for creating a new discussion group
def create_social_issues_group(request):
    if request.method == 'POST':
        form = SocialIssuesGroupForm(request.POST)
        if form.is_valid():  # Validate form data
            form.save()  # Save data to the database
            return redirect('social_issues_groups_list')
    else:
        form = SocialIssuesGroupForm()
    return render(request, 'events/create_social_issues_group.html', {'form': form})

# View for group conversation details
def group_conversation_detail(request, group_id):
    # Fetch the group and related conversations
    group = get_object_or_404(SocialIssuesGroup, id=group_id)
    conversations = group.conversations.all()
    user_profile = request.user.userprofile

    if request.method == 'POST':
        form = GroupConversationForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the conversation with additional fields
            conversation = form.save(commit=False)
            conversation.group = group
            conversation.user_profile = user_profile
            conversation.save()

            # Handle attachments if uploaded
            attachments = request.FILES.getlist('attachment')
            if attachments:
                for file in attachments:
                    Attachment.objects.create(conversation=conversation, file=file)

            messages.success(request, 'Your message has been sent successfully!')
            return redirect('group_conversation_detail', group_id=group.id)
        else:
            messages.error(request, 'There was an error sending your message. Please try again.')
    else:
        form = GroupConversationForm()

    # Render the conversation page with form and data
    return render(request, 'events/group_conversation_detail.html', {
        'group': group,
        'conversations': conversations,
        'form': form
    })

def send_message(request, leader_id):
    if request.method == 'POST':
        message_content = request.POST.get('message')  # Get the message content from the request
        leader = get_object_or_404(CommunityLeader, id=leader_id)  # Get the community leader instance

        # Create a new message
        Message.objects.create(content=message_content, leader=leader, sender=request.user)  # Set the sender to the current user

        # Add a success message
        messages.success(request, 'Message sent successfully!')  # Add success message

        # Return a success response
        return JsonResponse({'success': True, 'message': 'Message sent successfully!'})

    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

