from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend
import os
import base64


"""
    1. 密碼加密用
    2. 自行輸入，或是系統產生 16碼salt ，並保存在系統上
    3. 先透過 salt 將密碼加密
    4. 再透過 salt 來解密密碼
    
    執行加密後你會取得
        1. 16碼 salt  (保存在系統上)
        1. 加密後的密碼

"""

# 可以替換 "89天安門64" 為另一個密鑰字串
secret_key = "89天安門64"

#  DB 加密字串
encrypted_password = 'Updd+/qwdiCMIIZgzcgkpKLj8BtUBZ35Ig4Fc38TxlA='

# 產生密鑰（基於密碼和 salt）
def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=94269,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

# 加密函數
def encrypt(password: str, key: bytes , salt : bytes) -> str:
    # iv = os.urandom(16)  # 初始化向量 (IV)
    iv = salt
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # Padding 原始密碼
    padder = PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(password.encode()) + padder.finalize()
    
    # 加密
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    
    # 返回 base64 編碼的密文 (iv + encrypted_data)
    return base64.b64encode(iv + encrypted).decode()

# 解密函數
def decrypt(encrypted: str, key: bytes) -> str:
    encrypted_data = base64.b64decode(encrypted)
    iv = encrypted_data[:16]  # 取出 IV
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    # 解密
    padded_data = decryptor.update(encrypted_data[16:]) + decryptor.finalize()
    
    # 去除 Padding
    unpadder = PKCS7(algorithms.AES.block_size).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    return data.decode()

# 主程式
def main( ) -> str:
    (f"{'這是密碼加密程式':-^40}\n")


    user_password = input("請輸入需要加密的密碼: ")

    while True:
        salt = input("請輸入16碼 salt: < 直接輸入Enter ，由系統隨機產生16碼> ")
        if salt == "":
            salt = os.urandom(16)
            break

        if len(salt) != 16:
            print("Salt 必須是 16 個字節,請重新輸入.... \n")
        else :
            salt = salt.encode()
            break

    
    with open("salt", "w") as file :
        file.write(salt.hex())

    cur_dir = os.path.abspath(__file__).rsplit("/", 1)[0]


    if os.path.exists("salt"):
        print(f"Salt 檔案已保存到 : {cur_dir}\\salt")
        
    # 密鑰
    key = derive_key( secret_key , salt)  
    
    # 加密
    encrypted_password = encrypt( user_password , key , salt)
    print(f"加密後的密碼: {encrypted_password}")

    # 解密
    decrypted_password = decrypt( encrypted_password , key)
    if decrypted_password == user_password :
        print(f"[成功] 輸入的密碼加密後，與解密後一致")
    else:
        print(f"[失敗] 輸入的密碼加密後，與解密後一致不一致 .... 請重新確認")



# 使用範例
if __name__ == "__main__":
  


    #cur_dir = os.path.abspath(__file__).rsplit("/", 2)[0]
    cur_dir = os.path.abspath(__file__).rsplit("\\", 2)[0]
    with open(f"{cur_dir}/salt", "r") as file :
        salt = file.read()
        salt = bytes.fromhex(salt)

    # 密鑰
    key = derive_key( secret_key , salt ) 

    decrypted_password = decrypt( encrypted_password , key)
    print(f"Salt位置: {cur_dir}/salt")
    print(f"Salt值: {salt}")
    print(f"加密後密碼: {encrypted_password}")
    print(f"解密密碼為: {decrypted_password}")