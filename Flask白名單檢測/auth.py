from flask import Flask, request, jsonify
import datetime
import mysql.connector
import logging
import os
from datetime import datetime
import time
import socket
import json
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend
import os
import base64
import signal

app = Flask(__name__)

# json格式化紀錄當前 程式版本號
version = "1.7.1"
"""
    1.6.9 : 最初版本
    1.7.0 : DB 密碼加密處理
    1.7.1 : 處理 Log rotation 訊號 SIGHUP 通知 python 重新寫入
"""

# cdn header list
X_Real_IP_list = ['True-Client-Ip' , 'CloudFront-Viewer-Address' , 'X-Real-Ip']

#  DB 解密密鑰字串
secret_key = ""
encrypted_password = ''

def setup_logger(log_path):
    cur_dir = os.path.abspath(__file__).rsplit("/", 1)[0]

    # 創建 log 目錄
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    # 配置 logging
    logger = logging.getLogger(log_path)
    logger.setLevel(logging.DEBUG)

    # 移除舊 Handler（防止重複綁定）
    if logger.hasHandlers():
        logger.handlers.clear()

    # 創建 handler
    debug_Handler = logging.FileHandler(os.path.join(cur_dir, f'{log_path}/debug.log'))
    warning_Handler = logging.FileHandler(os.path.join(cur_dir, f'{log_path}/warning.log'))
    info_Handler = logging.FileHandler(os.path.join(cur_dir, f'{log_path}/info.log'))
    error_Handler = logging.FileHandler(os.path.join(cur_dir, f'{log_path}/error.log'))


    # 配置log級別
    debug_Handler.setLevel(logging.DEBUG)
    warning_Handler.setLevel(logging.WARNING)
    info_Handler.setLevel(logging.INFO)
    error_Handler.setLevel(logging.ERROR)

    # set formatter
    formatter = logging.Formatter('[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # 套用 Formatter
    for handler in [debug_Handler, warning_Handler, info_Handler, error_Handler]:
        handler.setFormatter(formatter)
        # 添加 handler 到 logger
        logger.addHandler(handler)

    return logger

def handle_log_reload(signum, frame):

    merchant_logger = setup_logger('log/merchant')
    bi_logger = setup_logger('log/bi')

    merchant_logger.info("Merchant Log file reopened after SIGHUP")
    bi_logger.info("Bi Log file reopened after SIGHUP")

# 設定 signal 處理函數
signal.signal(signal.SIGHUP, handle_log_reload)

# 產生不同logger
merchant_logger = setup_logger('log/merchant')
bi_logger = setup_logger('log/bi')


def get_hostname() -> str:

    # Linux 抓取主機名
    return socket.gethostname()

def get_current_time() -> str :

    utc8_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    utc0_time = time.strftime("%Y-%m-%d %H:%M:%S", 
              time.gmtime(time.mktime(time.strptime(f"{utc8_time}", "%Y-%m-%d %H:%M:%S"))))

    return utc8_time

@app.route('/withdraw/auth', methods=['GET'])
def auth_merchant():

   # log 紀錄類型
    auth_type="merchant withdraw"

    # 挑選驗證路徑 寫入log 
    request_uri = [ '/api/partner/orders' , '/api/partner/orders-withNotify']

    # log 紀錄開始
    merchant_logger.debug(f"{'merchant log 開始記錄':-^40}")

    status_message , status_code = auth_main( auth_type , request_uri , merchant_logger)
    return status_message , status_code
     

@app.route('/bi/auth', methods=['GET'])
def auth_bi():

    # log 紀錄類型
    auth_type="Bi Center"

    # 挑選驗證路徑 寫入log 
    request_uri = [ '/views/user/login.html' , '/api/admin/login/google' , '/views/']

    # log 紀錄開始
    bi_logger.debug(f"{'bi center log 開始記錄':-^40}")

    status_message , status_code = auth_main( auth_type , request_uri , bi_logger )
    return status_message , status_code

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return "Health Check OK", 200


def auth_main ( auth_type:str , request_uri:list , log) -> tuple[str, int]:


    for header, value in request.headers.items():
        log.debug(f"{header}: {value}")

    try:
        X_Real_IP = None
        XFF_IP = None

        x_real_ip_list_lower = [list_header.lower() for list_header in X_Real_IP_list ]

        for header, value in request.headers.items():
            log.debug(f"{header}: {value}")
            
            # X_Real_IP_list 是否存在於 header 中
            if header.lower() in x_real_ip_list_lower:
                X_Real_IP = value

        # X-Forwarded-For 
        XFF_IP = request.headers.get('X-Forwarded-For')
        if XFF_IP:
            XFF_IP = XFF_IP.split(",")[-1].strip()

        # X-Forwarded-For、X_Real_IP header 兩個都要存在
        if X_Real_IP is None and XFF_IP is None:
            log.error(f"X-Real-Ip and X-Forwarded-For header is missing", exc_info=True)
            return "Forbidden", 403
            #raise ValueError("X-Real-Ip and X-Forwarded-For header is missing")

        # X_Real_IP 存在 但跟 X-Forwarded-For IP來源不同
        if X_Real_IP and XFF_IP and X_Real_IP.split(":")[0] != XFF_IP.split(":")[0]:
            log.warning(f"X-Real-Ip: {X_Real_IP} and X-Forwarded-For: {XFF_IP} is not match", exc_info=True)

        # 驗證是 後台 還是 商的白名單
        client_ip = (X_Real_IP if X_Real_IP else XFF_IP).split(":")[0]

        if auth_type == "merchant withdraw":
            allow_ip = DB_query_merchant_allow_withdrawal_ip (client_ip)
        elif auth_type == "Bi Center":
            allow_ip = DB_query_bi_allow_ip (client_ip)

        # nginx 上 proxy_set_header 設定用於紀錄 log用 
        host = request.headers.get('Host')

        #original_uri = request.headers.get('X-Original-Uri')
        original_uri = request.headers.get('X-Original-Uri', 'N/A')
        log.debug(f"X-Original-Uri: {original_uri}")

        data = {
            "auth_type": auth_type,
            "time" :  get_current_time(),
            "domain": host,
            "request_uri": original_uri ,
            "version": version ,
            "X-Forwarded-For_IP" : XFF_IP,
            "Client_IP": client_ip,
            "result": "allow" if allow_ip else "not allow",
            "message": "白名單驗證通過" if allow_ip else "白名單驗證失敗 , 不在白名單內"
        }


        # 避免紀錄過多log資料
        if any(data['request_uri'].startswith(prefix) for prefix in request_uri):
            # 將 data 轉換 JSON 格式
            log.info(json.dumps(data, ensure_ascii=False))
            log.info(f"{'驗證結束':-^40}\n")


        if allow_ip :
            return "Authorized", 200
        else:
            log.info(json.dumps(data, ensure_ascii=False))
            log.info(f"{'驗證結束,驗證未通過':-^40}\n")
            return "Unauthorized", 401

    except Exception as e:
        log.error(f"Exception in auth route: {e}", exc_info=True)
        return "Internal Server Error", 500

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

def DB_query_merchant_allow_withdrawal_ip (client_ip) -> bool :

    with open("salt", "r") as file :
        salt = file.read()
        salt = bytes.fromhex(salt)

    # 密鑰
    key = derive_key( secret_key , salt ) 

    decrypted_password = decrypt( encrypted_password, key)

    conn = mysql.connector.connect(
            host="",
            user="",
            password = decrypted_password,
            database=""
    )

    cursor = conn.cursor()

    query = f"SELECT allow_withdrawal_ip FROM merchant_user WHERE status = 1 and allow_withdrawal_ip like '%{client_ip}%';"
    cursor.execute(query)

    results = cursor.fetchall()

    if results :
        return True
    else:
        return False

def DB_query_bi_allow_ip (client_ip) -> bool :

    with open("salt", "r") as file :
        salt = file.read()
        salt = bytes.fromhex(salt)

    # 密鑰
    key = derive_key( secret_key , salt ) 

    decrypted_password = decrypt( encrypted_password, key)

    conn = mysql.connector.connect(
            host="",
            user="",
            password= decrypted_password,
            database=""
    )

    cursor = conn.cursor()

    query = f"SELECT allow_ip FROM admin_config WHERE allow_ip like '%{client_ip}%';"
    cursor.execute(query)

    results = cursor.fetchall()

    if results :
        return True
    else:
        return False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080 , debug=True )