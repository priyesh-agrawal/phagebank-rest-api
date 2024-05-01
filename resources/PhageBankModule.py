def generate_password():
    import secrets
    import string
    #alphabet = string.ascii_letters + string.digits + string.punctuation
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(15))

    return password
