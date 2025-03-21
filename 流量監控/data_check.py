from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
import requests
import os
import json
from win32com.client import Dispatch
import subprocess
import re

# 流量超過才告警 (float 浮點數) 可帶入小數點
data_alert = 5.0

# --------- 取得現在使用的 driver 的版本號 -------------
def get_now_chromedriver_version(driver_path):
    try:
        # 執行命令來獲取ChromeDriver的版本信息
        result = subprocess.run([driver_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 提取版本號
        version_match = re.search(r"ChromeDriver (\d+\.\d+\.\d+\.\d+)", result.stdout)
        if version_match:
            return version_match.group(1)
        else:
            return None
    except Exception as e:
        print("Error occurred:", e)
        return None

def get_uj_cdn_Used_data (account , password , feature):
    try :
        options = webdriver.ChromeOptions()
        # options = webdriver.EdgeOptions()
        options.add_experimental_option('detach', True) 
        options.add_argument('--start-maximized') 

        # driver=webdriver.Edge(options=options)
        driver=webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 10)

    except Exception:
        paths = "C:\Program Files\Google\Chrome\Application\chrome.exe"
        parser = Dispatch("Scripting.FileSystemObject")
        version = parser.GetFileVersion(paths)

        current_dir = os.getcwd()
        DRIVER_PATH = f'{current_dir}/chromedriver.exe'
        now_driver_version = get_now_chromedriver_version(DRIVER_PATH)

        raise ConnectionRefusedError (f"現在使用的 chromedriver 版本: This version of ChromeDriver only supports Chrome version {now_driver_version}\nCurrent browser version is : {version}")

    try :
        driver.get("https://console.ujcdn.com/")
        username = wait.until(lambda driver: driver.find_element(By.NAME , 'username'))
        username.clear()
        username.send_keys(account)

        passwd = wait.until(lambda driver: driver.find_element(By.NAME , 'password'))
        passwd.clear()
        passwd.send_keys(password)

        login = wait.until(lambda driver: driver.find_element(By.NAME , 'login'))
        login.click()

        time.sleep(3)

        used_data = wait.until(lambda driver: driver.find_element(By.XPATH , '/html/body/div[1]/div/div/main/div/div[2]/div[1]/div[3]/div/div[2]/div[1]/div[1]'))
        used_data_text = wait.until(lambda driver: driver.find_element(By.XPATH , '/html/body/div[1]/div/div/main/div/div[2]/div[1]/div[3]/div/div[2]/div[1]/div[2]'))

        available_data = wait.until(lambda driver: driver.find_element(By.XPATH , '/html/body/div[1]/div/div/main/div/div[2]/div[1]/div[3]/div/div[2]/div[3]/div[1]'))
        available_data_text =  wait.until(lambda driver: driver.find_element(By.XPATH , '/html/body/div[1]/div/div/main/div/div[2]/div[1]/div[3]/div/div[2]/div[3]/div[2]'))

        today = time.strftime('%m-%d')
        message = (f'查詢時間:{today}\n{account} 帳號 ({feature}) \n總{available_data_text.text} : {available_data.text} , {used_data_text.text}: {used_data.text}')
        
        used_data_str = used_data.text
        used_data_num = float(used_data_str.split(' ')[0])
        unit = used_data_str.split(' ')[1]

        driver.quit()
            
        if used_data_num > data_alert and unit == 'TB' :
            return message
        else:
            return None

    except Exception :
        raise Exception (f"帳號:{account} 獲取優加CDN流量失敗 。") 

def CHECK_TG_CONF ( conf_name , group_name ) :
    current_dir = os.getcwd()
    try :
        with open(f'{current_dir}/{conf_name}', 'r') as tg_file :
            tg_conf = json.load(tg_file)
        
            try:
                bot = tg_conf[f'{group_name}']
            except :
                raise Exception(f"找不到 {group_name} 群組名稱")

    except FileNotFoundError:
        raise FileNotFoundError (f"路徑 {current_dir} , 找不到 {conf_name}")

def TG_SEND ( group_name , methods , document=None , photo=None , text=None ) :
    current_dir = os.getcwd()

    with open(f'{current_dir}/Telegram.conf', 'r') as tg_file :
        tg_conf = json.load(tg_file)

        try:
            bot = tg_conf[f'{group_name}']
            bot_token = bot['bot_token']
            chat_id = bot['chat_id']
            thread_id = bot['thread_id']
        
        except :
            tg_group = []
            for group_id , group_data in tg_conf.items():
                tg_group.append(group_id)

            result = ' | '.join(tg_group)
            raise Exception (f"無此 {group_name} 群組 , 目前僅只有 [ {result} ]")

        else:
            url = f"https://api.telegram.org/bot{bot_token}/"

            if methods == 'file' :
                method = 'sendDocument?'
                documents = {'document' : open(f'{document}', 'rb')}
                response = requests.post(url + method , data={'chat_id': chat_id , 'message_thread_id' : thread_id} , files=documents)

                if response.status_code == 200:
                    print("File sent successfully!")

                else:
                    print("Failed to send file.")
                    print(response.text)

            elif methods == 'photo' :
                method = 'sendPhoto?'
                photos = {'photo' : open(photo , 'rb')}
                response = requests.post(url + method, data={'chat_id': chat_id , 'message_thread_id' : thread_id}, files=photos)

                if response.status_code == 200:
                    print("Photo sent successfully!")

                else:
                    print("Failed to send Photo.")
                    print(response.text)

            elif methods == 'message' :
                method = 'sendMessage?'

                if thread_id == "" :
                    send_text = requests.post(f'https://api.telegram.org/bot{bot_token}/{method}chat_id={chat_id}&&parse_mode=Markdown&text={text}')
                else:
                    send_text = requests.post(url + method , data={'chat_id': chat_id , 'message_thread_id' : thread_id , 'text': text } )
                    print(send_text.status_code)
            else:
                raise Exception (f"目前沒有提供此 {methods} 方法 , 目前僅支援發送 [ file | photo | message ] 等功能")


if __name__ == '__main__':

    ACCOUNT_CONF = a{
        'account1' :
            {
                'account' : '',
                'password' : '',
                'feature' : ''
            },

        'account2' :
            {
                'account' : '',
                'password' : '',
                'feature' : ''
            }
    }

    try:
        CHECK_TG_CONF('Telegram.conf' , 'hengyi_ltz')

        for i in range(1,len(ACCOUNT_CONF)+1):
        
            account = (ACCOUNT_CONF[f'account{i}']['account'])
            
            password = (ACCOUNT_CONF[f'account{i}']['password'])
            feature = (ACCOUNT_CONF[f'account{i}']['feature'])
            Used_data = get_uj_cdn_Used_data( account , password , feature)

            # 返回值為 None 的話為正常
            if Used_data != None :
                TG_SEND( group_name='hengyi_ltz' , methods='message' , text=Used_data)
                time.sleep(2)
            else:
                print(f"優加CDN帳號 :{account} , 未超過告警流量{data_alert} TB")

    except ConnectionRefusedError as err :
        error_message=f'優加CDN帳號 {account} 查詢失敗 , 失敗原因:\n{err}。'
        TG_SEND( group_name='hengyi_ltz' , methods='message' , text=error_message)


    except Exception as err:
        print(err)
        TG_SEND( group_name='hengyi_ltz' , methods='message' , text=err)
