from cryptography.fernet import Fernet, InvalidToken
import bcrypt
import base64
CHATAI_API_KEY_ENCRYPTION_KEY = 'sDgR_PM7H4EJ95V4mZL5Wyywkp5qR3DqS4azg5Pytgw='
encryption_key = CHATAI_API_KEY_ENCRYPTION_KEY
api_key_cipher = Fernet(encryption_key.encode())
class Key: 
    def checkpw_bcrypt(self,str1:str,str2:str) -> bool:
        return bcrypt.checkpw(str1, str2)
    
    def string_to_bcrypt_hash(self,str:str)-> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(str.encode(), salt)
    
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
        
    def img_bytes_to_base64(self,bytes:bytes)->str:
        return base64.b64encode(bytes).decode("ascii")
    
    def string_to_base64(self,text: str) -> str:
        utf8_bytes = text.encode('utf-8')
        base64_bytes = base64.b64encode(utf8_bytes)
        return base64_bytes.decode('utf-8')
    
    def base64_to_string(self,base64_str: str) -> str:
        try:
            utf8_bytes = base64.b64decode(base64_str)
            return utf8_bytes.decode('utf-8')
        except Exception as e:
            return ""
key = Key()