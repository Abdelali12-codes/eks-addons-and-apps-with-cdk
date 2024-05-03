import string
import random
import boto3
import json

def generate_password(length):
    lowercase_letters = string.ascii_lowercase
    uppercase_letters = string.ascii_uppercase
    digits = string.digits
    special_characters = string.punctuation

    # Ensure at least one character of each type
    password = [random.choice(lowercase_letters),
                random.choice(uppercase_letters),
                random.choice(digits),
                random.choice(special_characters)]

    # Fill the remaining length with random characters
    password.extend(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(length - 4))

    # Shuffle the password
    random.shuffle(password)

    return ''.join(password)

def create_secret(secret_name, username, password):
    client = boto3.client('secretsmanager')

    secret_string = {
        'username': username,
        'password': password
    }

    response = client.create_secret(
        Name=secret_name,
        SecretString=json.dumps(secret_string)
    )

    return response

def handler(event, context):
    # Generate a password of length 12
    password = generate_password(10)

    # Set the username
    username = event['username']

    # Create a secret in AWS Secrets Manager
    secret_name = event['secretname']
    response = create_secret(secret_name, username, password)

    # Log the response
    print("Secret created successfully:", response)

    return {
        'statusCode': 200,
        'body': "Secret created successfully"
    }
