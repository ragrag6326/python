from sheet import Googlesheet
import os
import requests  
import time 

# tg發送
chat_id = "chatid"
bottoken = "bottoken"

today = time.strftime('%m-%d')  

# google sheet api的token檔案
cred = 'pandas-376711-2c4b5705a13d'

# 在此更換 domain
cloudpay = ["07786kkk.com"]

# google sheet 表單 url
# 1.
six_url = 'https://docs.google.com/spreadsheets/d/1f8DMfBRL_qmfETKdLC7t_EzCXLJwmivQBN7wLDpnxPU/edit#gid=0'
# 2.
cloudpay_url = 'https://docs.google.com/spreadsheets/d/1xRK_Q4Eb_j9qSJEXLi5ERNBsa1MuwhlKJawG2cg6hCg/edit#gid=0'


def check_url (gs , domain):
    try :
        gs.create_dir()
        gs.delete_csv()
    except:
        raise FileNotFoundError (f'找不到指定的路徑 : {gs.csvmonth_path}')
    else:
        gs.check_url(domain)

def check_csv (gs) :
    gs.check_csv()

def check_cred(gs , file) :
    gs.check_cred(file)

def gswrite (gs, file , url):
    gs.gswrite(file , url)

def tg_send( message , chat_id ,bottoken):
    text = (f"{today} - {message}")
    send_text = requests.post(f'https://api.telegram.org/bot{bottoken}/sendMessage?chat_id={chat_id}&&parse_mode=Markdown&text={text}')
    print(send_text.status_code) 


if __name__ == "__main__":


    gs2 = Googlesheet('project')

    try:
        check_cred(gs2 , cred)
        check_url(gs2 , cloudpay)
        check_csv (gs2)
        gswrite(gs2 , cred , cloudpay_url)

    except Exception as err:
        tg_send (f'{err}',f'{chat_id}',bottoken)
        
    else:
        new_url = 'https://docs.google.com/spreadsheets/d/1xRK\_Q4Eb\_j9qSJEXLi5ERNBsa1MuwhlKJawG2cg6hCg/edit#gid=0'
        tg_send (f'{gs2.project} 表單填寫成功\n {new_url}',f'{chat_id}',bottoken)




