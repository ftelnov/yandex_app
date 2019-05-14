import hashlib


def sha256(some_string):
    encoder = hashlib.sha3_256()
    encoder.update(bytes(some_string, encoding='utf-8'))
    return encoder.hexdigest()


def get_token(login, password):
    return sha256(login + ';' + password)


if __name__ == '__main__':
    print(sha256('123'))
