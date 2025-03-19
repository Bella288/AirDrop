from cryptography.fernet import Fernet

key = Fernet.generate_key()
print(f"Hard-coded Fernet key: {key}")