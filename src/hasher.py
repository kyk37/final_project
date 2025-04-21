import bcrypt

# class Hasher:
#     @staticmethod
#     def verify_password(plain_password, hashed_password):
#         # Ensure plain_password is bytes
#         if isinstance(plain_password, str):
#             plain_password = plain_password.encode('utf-8')
#         # hashed_password should already be bytes from storage
#         return bcrypt.checkpw(plain_password, hashed_password)

#     @staticmethod
#     def get_password_hash(password):
#         # Ensure password is bytes
#         if isinstance(password, str):
#             password = password.encode('utf-8')
#         # Generate a salt and hash the password
#         salt = bcrypt.gensalt(rounds=12)  # 12 is a common default; adjust as needed
#         return bcrypt.hashpw(password, salt)

class Hasher:
    @staticmethod
    def verify_password(plain_password, hashed_password):
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password):
        if isinstance(password, str):
            password = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password, salt)
        return hashed.decode('utf-8')  # decode before saving to DB