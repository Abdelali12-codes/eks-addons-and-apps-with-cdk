import boto3
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

# Initialize KMS client
kms = boto3.client('kms', region_name='us-east-1')

# Replace with your KMS key ID or ARN
KMS_KEY_ID = 'arn:aws:kms:us-east-1:111122223333:key/abcd-1234-efgh-5678-ijkl9012mnop'

# ---------------------------------------------------------------------
# 1️⃣ Generate a data key from KMS
# ---------------------------------------------------------------------
response = kms.generate_data_key(KeyId=KMS_KEY_ID, KeySpec='AES_256')

plaintext_data_key = response['Plaintext']
encrypted_data_key = response['CiphertextBlob']

print("Generated data key and encrypted copy from KMS")

# ---------------------------------------------------------------------
# 2️⃣ Encrypt data locally using the plaintext data key
# ---------------------------------------------------------------------
data_to_encrypt = b"Hello Ali, this is a secret message from KMS demo!"
iv = os.urandom(16)  # Initialization Vector for AES CBC mode

cipher = Cipher(algorithms.AES(plaintext_data_key), modes.CBC(iv), backend=default_backend())
encryptor = cipher.encryptor()

# Pad data to be multiple of 16 bytes
pad_length = 16 - len(data_to_encrypt) % 16
padded_data = data_to_encrypt + bytes([pad_length] * pad_length)

ciphertext = encryptor.update(padded_data) + encryptor.finalize()

print("Data encrypted locally with AES-256.")

# Now discard the plaintext data key from memory (important for security)
del plaintext_data_key

# ---------------------------------------------------------------------
# 3️⃣ Store ciphertext + encrypted data key
# ---------------------------------------------------------------------
# In a real app, you'd store these in a database or S3
stored_encrypted_data = {
    "iv": base64.b64encode(iv).decode(),
    "ciphertext": base64.b64encode(ciphertext).decode(),
    "encrypted_data_key": base64.b64encode(encrypted_data_key).decode()
}

print("Stored encrypted data and encrypted key.\n")

# ---------------------------------------------------------------------
# 4️⃣ Decrypt process
# ---------------------------------------------------------------------
print("Now decrypting...")

# Decode the encrypted data key
encrypted_data_key_bytes = base64.b64decode(stored_encrypted_data['encrypted_data_key'])

# Decrypt the data key using KMS
decrypt_response = kms.decrypt(CiphertextBlob=encrypted_data_key_bytes)
decrypted_data_key = decrypt_response['Plaintext']

# Decrypt the ciphertext using the decrypted data key
iv = base64.b64decode(stored_encrypted_data['iv'])
ciphertext = base64.b64decode(stored_encrypted_data['ciphertext'])

cipher = Cipher(algorithms.AES(decrypted_data_key), modes.CBC(iv), backend=default_backend())
decryptor = cipher.decryptor()

decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()
pad_length = decrypted_padded_data[-1]
decrypted_data = decrypted_padded_data[:-pad_length]

print("Decrypted message:", decrypted_data.decode())

# Clean up key
del decrypted_data_key
