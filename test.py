from django.contrib.auth.models import User

def create_user(username, password):
    if User.objects.filter(username=username).exists():
        print(f"Username '{username}' is already taken. Please choose another username.")
        return None  # or raise an exception, or return an error message

    # If the username is unique, create the user
    new_user = User.objects.create_user(username=username, password=password)
    return new_user

# Get user input
username = input("Enter a username: ")  # Input for username
password = input("Enter a password: ")    # Input for password

new_user = create_user(username, password)

if new_user:  # Check if the user was created successfully
    print(f"User '{new_user.username}' created successfully!")
