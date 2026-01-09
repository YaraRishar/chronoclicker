import base64
import os
import pathlib
from cryptography.exceptions import InvalidKey
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_hash(master_password: str) -> bytes:
    salt = os.urandom(32)
    key = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=32_000)
    key_material = key.derive(master_password.encode("utf-8"))
    fernet_key = base64.urlsafe_b64encode(key_material)
    true_hash = base64.b64encode(salt + fernet_key)
    return true_hash


def verify_password(provided_password: str) -> bool:
    true_hash = get_stored_master_hash()
    master_hash = get_hash(provided_password)
    if true_hash is None:
        store_master_hash(master_hash)
        return True

    true_hash = base64.b64decode(true_hash)
    salt = true_hash[:32]
    fernet_key = true_hash[32:]
    stored_key = base64.urlsafe_b64decode(fernet_key)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(),
                     length=32,
                     salt=salt,
                     iterations=32_000)
    try:
        key.verify(provided_password.encode("utf-8"), stored_key)
        return True
    except InvalidKey:
        return False


def get_fernet_key(true_hash: bytes) -> Fernet:
    true_hash = base64.b64decode(true_hash)
    fernet_key = true_hash[32:]
    return Fernet(fernet_key)


def store_master_hash(true_hash: bytes):
    path_to_storage = pathlib.Path("character_tokens/master_hash.txt")
    if path_to_storage.is_file():
        return
    with open(path_to_storage, "bw") as file:
        file.write(true_hash)


def get_stored_master_hash() -> bytes | None:
    path_to_storage = pathlib.Path("character_tokens/master_hash.txt")
    if not path_to_storage.is_file():
        return None
    with open(path_to_storage, "rb") as file:
        true_hash = file.readline()
    return true_hash


def save_new_creds(mail: str, password: str, filename) -> str:
    true_hash = get_stored_master_hash()
    fernet_key = get_fernet_key(true_hash)

    path_to_storage = pathlib.Path("character_tokens")
    filename = f"{filename}.txt"
    path_to_token = path_to_storage.joinpath(filename)

    encrypted_password = fernet_key.encrypt(password.encode("utf-8"))
    encrypted_mail = fernet_key.encrypt(mail.encode("utf-8"))
    with open(path_to_token, "bw") as file:
        file.writelines([encrypted_mail, b' ', encrypted_password])
    return str(path_to_token.absolute())


def get_creds(filename: str) -> (str, str):
    true_hash = get_stored_master_hash()
    path_to_storage = pathlib.Path("character_tokens")
    path_to_token = path_to_storage.joinpath(f"{filename}.txt")
    with open(path_to_token, "rb") as file:
        line = file.readline().decode("utf-8")
        encrypted_mail, encrypted_password = line.split(" ")
    encrypted_mail = bytes(encrypted_mail.encode("utf-8"))
    encrypted_password = bytes(encrypted_password.encode("utf-8"))

    fernet_key = get_fernet_key(true_hash)
    mail = fernet_key.decrypt(encrypted_mail)
    password = fernet_key.decrypt(encrypted_password)
    return mail.decode("utf-8"), password.decode("utf-8")


def purge_all_creds() -> list:
    path_to_storage = pathlib.Path("character_tokens")
    files = os.listdir(path_to_storage)
    for file in files:
        os.remove(path_to_storage.joinpath(file))
    files.remove("master_hash.txt")
    files = [i.replace(".txt", "") for i in files]
    return files


def get_token_str() -> str:
    path_to_storage = pathlib.Path("character_tokens")
    files = os.listdir(path_to_storage)
    if "master_hash.txt" in files:
        files.remove("master_hash.txt")

    char_names = [i.replace(".txt", "") for i in files]
    char_names = ", ".join(char_names)
    if not char_names:
        return "нет."
    return char_names