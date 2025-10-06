import os
import boto3
import psycopg2
from botocore.exceptions import ClientError

# Lambda handler
def lambda_handler(event, context):
    secret_name = os.environ['SECRET_NAME']
    region_name = os.environ.get('AWS_REGION', 'us-east-2')

    # Get secret from Secrets Manager
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        secret_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise e

    secret = eval(secret_response['SecretString'])  # Example: {"username": "admin", "password": "pass", "host": "mydb.example.com", "port": 5432}
    db_host = secret['host']
    db_user = secret['username']
    db_password = secret['password']
    db_port = secret.get('port', 5432)

    # Connect to the default database (usually 'postgres' for PostgreSQL)
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()
    except Exception as e:
        print(f"Unable to connect to RDS: {e}")
        raise e

    # Databases and users to create
    db_users = [
        {"db": "airflow", "user": "airflow"},
        {"db": "openmetadata", "user": "openmetadata"}
    ]

    for entry in db_users:
        db_name = entry['db']
        user_name = entry['user']

        try:
            # Create database
            cursor.execute(f"CREATE DATABASE {db_name};")
            print(f"Database '{db_name}' created.")
        except psycopg2.errors.DuplicateDatabase:
            print(f"Database '{db_name}' already exists.")

        try:
            # Create user with the same password as secret
            cursor.execute(f"CREATE USER {user_name} WITH PASSWORD '{db_password}';")
            print(f"User '{user_name}' created.")
        except psycopg2.errors.DuplicateObject:
            print(f"User '{user_name}' already exists.")

        try:
            # Grant ownership to the user
            cursor.execute(f"ALTER DATABASE {db_name} OWNER TO {user_name};")
            print(f"User '{user_name}' is now owner of database '{db_name}'.")
        except Exception as e:
            print(f"Error changing ownership: {e}")

    cursor.close()
    conn.close()

    return {
        "statusCode": 200,
        "body": "Databases and users created successfully."
    }
