#!/usr/bin/env python3
import os
import socket
import re
import json
import subprocess
import requests
from datetime import datetime
import glob
import time

"""
    type 1 = nginx 
    1.6.9 : 最初版本
    1.7.0 : 修正 json 格式
    1.7.1 : 修正 timezone UTC+8 -> UTC0
    1.7.2 : 1. 新增 post data 欄位 type:1
            2. 修正 server block 同時出現 listen 80  443 ssl 時 , 80 port 也會被加上 ssl
            3. 新增 get_nginx_path 方法 , 避免 nginx 路徑寫死 , 路徑在不同地方出錯

    1.7.3 : 修正路徑的蠢問題 108行改用 os.path.join 方式拼接路徑
    1.7.4 : 修正 get_nginx_path() nginx -t 有時會有錯誤訊息，需要跑回圈找出正確路徑
"""
version = "1.7.4"
type = 1 

def get_hostname() -> str:

    # Linux 抓取主機名
    return socket.gethostname()
    
def get_current_time() -> str :

    utc8_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    utc0_time = time.strftime("%Y-%m-%d %H:%M:%S", 
              time.gmtime(time.mktime(time.strptime(f"{utc8_time}", "%Y-%m-%d %H:%M:%S"))))

    return utc0_time

def get_ip_addresses() -> list :

    ip_addresses = []
    try:
        # 在Linux上執行子程序 ，執行 ip -4 addr 的指令，來找出當前主機IP ，此指令需要 python 3.8以上才能執行
        result = subprocess.run(["ip", "-4", "addr"], capture_output=True, text=True, check=True)
        # 確保 stdout 輸出非空值
        if result.stdout:
            # 以行進行切割放入 array ，這樣就能逐行判斷
            lines = result.stdout.splitlines()
            for line in lines:
                # d = [0-9] , ( 匹配數字直到.出現 ) 抓出合理的 IPv4 
                match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                if match :
                    if match.group(1) != '127.0.0.1':
                        ip_addresses.append(match.group(1))
    except Exception as e:
        print(f"無法獲取 IP 地址: {e}")

    return ip_addresses

def get_nginx_path() -> str :

    # 在Linux上執行子程序 ，執行 nginx -t 的指令 找出 nginx 路徑
    result = subprocess.run(["nginx", "-t" ], capture_output=True, text=True, check=True)
    if result.stderr:
        lines = result.stderr.splitlines()
        for line in lines:
            match = re.search(r'(\/.+\/)', line)
            if match :
                return match.group(1)

def find_nginx_include ( nginx_conf_dir ) -> list :
    """
    處理 Nginx 配置中的 include 檔案，返回包含路徑和域名的清單
    """

    # 移動到目錄
    os.chdir(nginx_conf_dir)

    # 搜尋 nginx.conf 裡面的 include *.conf 位置
    with open( f'nginx.conf', 'r') as f:
        content = f.read()

        include_is_conf = re.findall(r'^\s*include\s([\/|a-z|0-9|*.]+.conf)', content, re.M+re.I )

    return include_is_conf

def parse_nginx_include( nginx_conf_dir ) -> json :

    # 取得 includes path -> array
    nginx_include_path = find_nginx_include(nginx_conf_dir)

    contents = []

    for include_path in nginx_include_path:
        try:

            # 如果 nginx.conf include 有 * 萬用字元另外處理 ， 因為都會放在 array 中
            conf_paths = glob.glob(include_path, recursive=True) if '*' in include_path else [include_path]
            for conf_path in conf_paths:

                """
                處理 Nginx 配置中的 includes 返回路徑 
                    1. 設定檔的 includes 有些是 "完整路徑" , 有些是 "相對路徑" 他媽的
                    2. 若寫 完整路徑 /usr/local/nginx/conf 直徑套用裡面找出來的路徑
                    3. 若寫 相對路徑 前面再加上 /usr/local/nginx/conf 加上相對路徑
                """
                if nginx_conf_dir in conf_path:
                    nginx_path=f'{conf_path}'
                else:
                    nginx_path=os.path.join(nginx_conf_dir, conf_path)
                    #nginx_path=f'{nginx_conf_dir}/{conf_path}'

                # 初始化 存放 path、domains 的表
                config_data = {"Path": nginx_path, "domains": []}

                # 讀取 conf 檔案
                with open( conf_path , 'r') as conf:
                    config_file = conf.read()

                    # 匹配 一個conf當中的 server 在 {} 區塊的檔案
                    server_blocks = re.findall(r'server\s*\{(.*?)\}', config_file, re.S)
                    for block in server_blocks:
                        
                        # default
                        listen_default_server = re.findall(r'^\s*listen.+(default_server)', block , re.M+re.I)
                        servername_Wildcard = re.findall(r'^\s*server_name.+(_)', block , re.M+re.I )

                        # default 判斷 Server_name 是否有 _ ，以及 listen 有沒有 default_server
                        default = "true" if '_' in servername_Wildcard or 'default_server' in listen_default_server else False

                        # 80 or 443
                        listen_port = re.findall(r'^\s*listen\s*(\d+)', block , re.M+re.I )

                        # 若 server_name 一條以上 ，正則匹配為 'test1.com test2.com' ，需要split空白切割為 'test1.com' 'test2.com' ->  split 將結果存為二維陣列 [] []        
                        filtered_domain = re.findall(r'^\s*server_name\s+([^;]+);', block , re.M+re.I )
                        filtered_domain = [domain.split() for domain in filtered_domain]
                        
                        # listen 443 <ssl> 是否有+上 ssl
                        ssl_on=re.findall(r'^\s*listen\s+\d.*(ssl)', block , re.M+re.I)
                        

                        """
                            同一個 server block 中可能會配置 80 或 443
                            1. 假設配置中 同時存在 80 443 但沒ssl 
                                listen 80 
                                listen 443 
                                server_name test.com  以 port 號迴圈來判斷 test.com:80 及 test.com:443

                            2. 假設配置中 同時存在 80 443 有 ssl 
                                listen 80 
                                listen 443 ssl
                                server_name test2.com  
                                ssl_on 會為 true  所以 test2.com:80  test2.com:443 的 ssl都會為true 代表有配置證書
                        """
                        for port in listen_port:
                            for r1 in range(0, len(filtered_domain)):
                                for r2 in range(0, len(filtered_domain[r1])):
                                    if not default :
                                        config_data["domains"].append({
                                            "domain": filtered_domain[r1][r2],
                                            "port": int(port),
                                            "ssl": "ssl" in ssl_on and int(port) == 443
                                        })
                                    else :
                                        config_data["domains"].append({
                                            "domain": filtered_domain[r1][r2],
                                            "port": int(port),
                                            "ssl": "ssl" in ssl_on and int(port) == 443,
                                            "default": default
                                        })
                    # 判斷 "domains": []  確保 includ 的 conf 有 server_name <domain> 才會被加入
                    if config_data["domains"]:
                        contents.append(config_data)

        except Exception as e:
                print(f"無法讀取文件 {include_path} {e}")

    return  contents

def post_data( json_data ) -> bool :
    
    url = ""
    
    session = requests.Session()
    session.auth = ('', '')

    response = session.post(url , data=json_data, headers={"Content-Type":"application/json"})
    if response.status_code == 200:
        print("File Post to n8n successfully!")
        return True
    
    else:
        print("Failed to send file.")
        print(response.text)
        return False

def main():

    nginx_path = get_nginx_path()

    data = {
        "hostname": get_hostname(),
        "time" :  get_current_time(),
        "version": version ,
        "type" : type ,
        "IPAddresses": get_ip_addresses(),
        "contents": parse_nginx_include(nginx_path)
    }
    
    # 將結果輸出為 JSON 格式 , indent=4 會讓 JSON 資料帶 4個空格 進行縮排
    output = json.dumps(data, indent=4)
    # 印出來方便 debug
    print(output)

    post_data(output)

if __name__ == "__main__":
    main()