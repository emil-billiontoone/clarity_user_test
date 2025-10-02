import keyring

# Replace these with your actual login info
SERVICE_NAME = "user_tester_app"
USERNAME = "your_username_here"  # Replace with your actual username
PASSWORD = "your_password_here"  # Replace with your actual password

# Store both username and password in macOS Keychain
# Store username using a special key
keyring.set_password(SERVICE_NAME, "USERNAME_KEY", USERNAME)
# Store password using the username as key
keyring.set_password(SERVICE_NAME, USERNAME, PASSWORD)

print("Credentials stored in macOS Keychain")
print(f"   - Username: {USERNAME}")
print(f"   - Password: {'*' * len(PASSWORD)}")

