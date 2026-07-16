from cryptography.fernet import Fernet, InvalidToken
CHATAI_API_KEY_ENCRYPTION_KEY = 'sDgR_PM7H4EJ95V4mZL5Wyywkp5qR3DqS4azg5Pytgw='
encryption_key = CHATAI_API_KEY_ENCRYPTION_KEY
api_key_cipher = Fernet(encryption_key.encode())
class Key: 
    def encrypt_api_key(self,raw_api_key: str) -> str:
        return api_key_cipher.encrypt(
            raw_api_key.encode("utf-8")
        ).decode("utf-8")

    def decrypt_api_key(self,encrypted_api_key: str) -> str:
        try:
            return api_key_cipher.decrypt(
                encrypted_api_key.encode("utf-8")
            ).decode("utf-8")
        except InvalidToken as exc:
           print("API Key 解密失败或密文已被修改")
           return ''
key = Key()