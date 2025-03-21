import requests  
import csv 
import time 
from bs4 import BeautifulSoup 
import pandas as pd 
import os 
import gspread 
from google.oauth2.service_account import Credentials 
import pandas as pd


class Googlesheet :

    today = time.strftime('%m-%d')  
    year = time.strftime('%Y') 
    month = time.strftime('%m') 
    month = (month[1]) 
    sheet_work = int(month) - 1 
    master_df = pd.DataFrame() 



    def __init__ (self , project ) :
        self.project = project
        self.merge_path = f'./{self.project}csv_merge'
        self.csvmonth_path = f'./{self.project}csv_merge/{self.year}年{self.month}月'


    def create_dir (self):
        isExists=os.path.exists(self.merge_path)
        if not isExists:
            os.mkdir(self.merge_path)

        isExists=os.path.exists(self.csvmonth_path)    
        if not isExists:
            os.mkdir(self.csvmonth_path)
    
    def delete_csv(self):
        csvdir = os.listdir(f'{self.merge_path}') 
        for fname in csvdir: 
            if fname.endswith(".csv"):
                os.remove(f'{self.merge_path}/{fname}')

    def check_url(self , domainlist):
        try :
            headers  = ['日期'] + domainlist
            tmp = [] 
            with open(f'{self.merge_path}/{self.today}{self.project}.csv', 'w' ,newline='' ,encoding='utf-8-sig') as csvfile:  
                writer = csv.writer(csvfile) 
                writer.writerow(headers) 
                
                for check in domainlist :  
                    url = f'https://www.boce.com/hijack/{check}'  
                    html = requests.get(url)  
                    html.encoding="utf-8"  
                    soup = BeautifulSoup(html.text, 'html.parser') 
                    link2 = soup.find('b', class_='font18 font18s').get_text() 
                    link2 = int(link2)

                    if  link2 != 0 :   
                        link1 = soup.find('span', class_='font18').get_text() 
                        link2 = soup.find('b', class_='font18 font18s').get_text() 
                        link3_tmp = soup.find_all('b', class_='font18') 
                        link3_tmp2 = (link3_tmp[2]) 
                        link3 = (link3_tmp2).get_text() 
                        
                        urlstr =  ''.join(check) 
                        writer = csv.writer(csvfile) 
                        urlno = (f"{link1}\n劫持节点数:{link2}個\n劫持占比:{link3}") 
                        tmp.append(urlno) 
            
                    if link2 == 0 :      
                        urlok = soup.find('span', class_='page10c').get_text() 
                        writer = csv.writer(csvfile)    
                        tmp.append(urlok)

                writer.writerow([f"{self.today}"] + tmp) 
        except :
            raise TypeError (f"{self.project} 劫持檢測發生問題")

    def merge_csv(self): 
        try:
            merge = os.listdir(self.merge_path)  
            month_path = os.listdir(self.csvmonth_path) 
            csv_list = [] 

            for fname in month_path :    
                if fname.endswith(".csv"):  
                    fname = f'{self.csvmonth_path}/{fname}'
                    csv_list.append(pd.read_csv(f'{fname}'))

            for fname in merge :  
                if fname.endswith(".csv"): 
                    fname = f'{self.merge_path}/{fname}'
                    csv_list.append(pd.read_csv(f'{fname}'))


            csv_all = pd.concat(csv_list ,axis = 0 ,join='outer',)  # 0 = row  1 = colume                  
            csv_all.to_csv( f'{self.csvmonth_path}/{self.project}{self.month}月合併.csv' ,index=False , encoding="utf_8_sig" )  

        except:
            raise TypeError (f"{self.project} 合併檔案發生問題")

    def check_cred (self , name):
        gs_cred = os.path.join('./', f'{name}.json')
        if not os.path.isfile(gs_cred):
            current_dir = os.getcwd()
            raise FileNotFoundError (f'未找到 json憑證檔 : 請將{name}.json 放在 此路徑 : {current_dir} ')
            

    def gswrite(self , name , url): 
            
            scope = ['https://www.googleapis.com/auth/spreadsheets'] 
            cred_path = f"./{name}.json" 
            creds = Credentials.from_service_account_file( cred_path, scopes=scope) 
            gs = gspread.authorize(creds) 
            sheet = gs.open_by_url(f'{url}') 
            
            worksheet = sheet.get_worksheet(self.sheet_work) 
            df = pd.read_csv(f'{self.csvmonth_path}/{self.project}{self.month}月合併.csv') 
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())

    def check_csv (self):
        try:
            data = pd.read_csv(f'{self.csvmonth_path}/{self.project}{self.month}月合併.csv')
            date = data['日期'].max()
            if date == self.today :
                raise ValueError (f"{self.project}資料已填寫完成,無須再執行")
            else:
                self.merge_csv()
        
        except FileNotFoundError :
            print ("未找到檔案正在創建中")
            self.merge_csv()

            
    def tg_send(self , message , chat_id , bottoken ):
        text = (f"{self.today} - {message}")
        send_text = requests.post(f'https://api.telegram.org/bot{bottoken}/sendMessage?chat_id={chat_id}&&parse_mode=Markdown&text={text}')
        print(send_text.status_code) 




