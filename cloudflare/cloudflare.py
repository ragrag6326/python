import requests
import json
import os
import socket
import time
import re


class Cloudflare():

    day = time.strftime('%m-%d')
    _zone = {}
    _records_id = {}
    _records_list =[]
    _domain_record = []

    URL = {
        "domains" : "https://api.cloudflare.com/client/v4/zones",
    }

    def __init__ (self , cf_token , cf_email):


        self.headers = {
            'Content-Type': 'application/json' ,
            'X-Auth-Key' : f'{cf_token}',
            'X-Auth-Email' : f'{cf_email}'
        }

    def domain_list(self) :
        resp = self._check_api( self.URL['domains'] , self.headers)
        zone_page = resp['result_info']['total_count']
        zone_resp = self._check_api( self.URL['domains']+f'?per_page={zone_page}', headers=self.headers )

        zones = zone_resp['result']
        zone_list = []

        for zone in zones:
            name = zone['name']
            
            zone_list.append(name)
            
        return zone_list

    def _check_api(self, domain, headers):  # 使用get_api這個 funtion 必須先傳入domian 加上 header(也就是key跟secret)
        resp = requests.get(domain, headers = headers)
 
        if resp.status_code == 200:    # 使用 requests.status_code  網頁有正常就會回傳200給我們
            return resp.json()
        else:                               
            raise Exception ('請求失敗, 請稍後再嘗試')  
             
    def _get_zone_id (self , domain):     # 1. 內部呼叫取得 zone_id , 需要用迴圈來執行這個函試 
        
        result = self._zone.get(domain)
        if result:
            return result

        resp = self._check_api( self.URL['domains'] , self.headers)   # 先取得 CF api 的回應200才回傳
        zone_page = resp['result_info']['total_count']                # cloudflare 是以頁來計算 , 一頁最多回傳20筆域名 , 所以先找到 page總頁數 
        zone_resp = self._check_api( self.URL['domains']+f'?per_page={zone_page}', headers=self.headers ) # 把page有幾頁 傳給api 就能回傳所有domain給我們

        
        zones = zone_resp['result']
        for zone in zones:          # 以迴圈方式來取得 zone 的內容  裡面會包含所有 ( domian 跟 domain 的 zone_id )
            self._zone.update({zone['name']: zone['id']})  # 把 domain 跟: 該domain 的 zone_id 用 {全域變數字典} 存起來
        
        return self._zone.get(domain)   # 最後 dict.get 方式 使用者傳哪條domain就來 , 有找到 key 就回傳 value 回去

    def _record( self , domains ):  # 2 內部呼叫取得該域名 record 所有A紀錄 
         
        records_list = []
        
        for domain in domains :
            
            zone_id =  self._get_zone_id(domain) # 要拿到 16c.com 裡面有什麼 record 的話 就需要有 zone_id
            dns_records = self._check_api(self.URL['domains']+f'/{zone_id}/dns_records' , self.headers) # 傳給api 來取得 dns_records

            for record in dns_records['result']:
                if record['type'] == 'A' :
                   records_list.append(record)   # 把是 A紀錄的record資料,存入列表
            
        return records_list

    def _get_records_name_id ( self , dead_ip , domains):  # 3 把 紀錄用list存起來  還有把該紀錄的 id 用 dict 存起來
       
        domain_record = []
        
        record = self._record(domains)
        long = len(record)     # 取回來的list 來判斷總共有多長
        
        for i in range(long):
            #     if record[i]['content'] == dead_ip:
                domain_record.append(record[i]['name'])  # 會把所有 domain 的 ( @ * www )record 全部放入list中  如: ['*.16c43.com', '16c43.com', 'www.16c43.com']
                self._records_id.update({record[i]['name'] : record[i]['id']})  # 把 所有 domain 的 ( @ * www )record 放入全域變數dict中 

        return domain_record

    def _get_records_id(self , domains , name ):  # 內部呼叫 , 需要用迴圈來執行這個函試
        tmp = (domains,)

        for domain in tmp:

            zone_id =  self._get_zone_id(domain)
            dns_records = self._check_api(self.URL['domains']+f'/{zone_id}/dns_records' , self.headers)

            try:
                for record in dns_records['result'] :
                    if name == '@' :                        # 如果A紀錄解析是 @ 的話 , 就需要另外判斷
                        if record['name'] == f'{domain}' :  # @ = exmple.com
                            return record['id']
                    elif record['name'] == f'{name}.{domain}' :  # 非 @ 就需加入前綴判斷 www.exmple.com
                            return record['id']       # 該紀錄的 id , 該域名有紀錄的話才能使用 CF的api 來 update 紀錄 , 如果沒紀錄直接新增就好 不需要拿到 record id
            except:
                raise ValueError(f'{domain} 無此紀錄')

    def auto_update( self , dead_ip , alive_ip , domains): # 4 api自動更新 Cloudflare 
        
        self.domain = domains  # 放所有域名列表 (用來取 zone_id 的值)
        
        domain_list = self._get_records_name_id(dead_ip , domains) # 讀取所有的( @ * www ) domain的A紀錄 列表
        
        times = 0

        for domain in domain_list :
            compare_name = domain.split(".")[0]+'.'  # 如果name 是 ( * www ) 等三級域名
            filter = domain.split('.')[0:]   # 用 . 來切割域名 判斷域名是幾節域名  如 ['07786l', 'com']
            if 2 >= len(filter) :
                compare_name = ''
                name = '@'
            else:
                name = domain.split(".")[0]

            compare = compare_name+self.domain[times]  # self.domain[0~n]為傳入的 [domains]list , 用來判斷當傳來的 (域名16c.com) 跟 正規抓回來的 *.16c22.com  

            if domain != compare :             # 如果 兩者不一樣  self.domain[0] 就會 +1 , +1域名就會換成 16c22.com 因為 16c.com的所有(A紀錄)已經更新完
                times += 1

            record_id = self._records_id.get(domain)        # 由於會先呼叫 (_get_records_name_id)這個function會先把 records name 跟 id 放到 {全域變數dict} 這邊只需要放入 domain的record 就能取到 record_id
            zone_id = self._get_zone_id(self.domain[times]) # 前面已先判斷過需不需要+1 變成讀取下個域名

            dns_data = {
                'type': 'A',
                'name': name,
                'content': alive_ip,
                'ttl': '1',
                'proxied': False
            }

            try :
                update = requests.put(self.URL["domains"]+f'/{zone_id}/dns_records/{record_id}', headers=self.headers ,json=dns_data ).json()
                if update['success'] == True:
                    print(f'{domain} update 成功')

            except:
                raise ValueError ( f'{domain} update 失敗')
           
    def manual_update( self  , alive_ip , domains): # 3
        
        self.domain = domains  # 放所有域名列表 (用來取 zone_id 的值)
        
        domain_list = self._get_records_name_id(dead_ip=None , domains=self.domain) # 讀取所有的( @ * www ) domain的A紀錄 列表
        
        times = 0
        for domain in domain_list :

            compare_name = domain.split(".")[0]+'.'
            filter = domain.split('.')[0:]
            if 2 >= len(filter) :
                compare_name = ''
                name = '@'
            else:
                name = domain.split(".")[0]

            compare = compare_name+self.domain[times]

            if domain != compare :
                times += 1


            record_id = self._records_id.get(domain)
            zone_id = self._get_zone_id(self.domain[times])

            dns_data = {
                'type': 'A',
                'name': name,
                'content': alive_ip,
                'ttl': '1',
                'proxied': False
            }

            try :
                update = requests.put(self.URL["domains"]+f'/{zone_id}/dns_records/{record_id}', headers=self.headers ,json=dns_data ).json()
                if update['success'] == True:
                    print(f'{domain} update 成功')

            except:
                raise ValueError ( f'{domain} update 失敗')

    def get_type(self , domains , type):   # 取得該域名 類型type 的紀錄值

        for domain in domains :
            zone_id = self._get_zone_id(domain)
            dns_records = self._check_api(self.URL['domains']+f'/{zone_id}/dns_records' , self.headers)

            for record in dns_records['result']:
                types = (record['type'])
                if types == f'{type}':
                    print (record['name'] , record['content'] )
            print('\n')           

    def add(self , domains, type, name, content):
        dns_data = {
            'type': type, 
            'name': name, 
            'content': content, 
            'ttl': '1', 
            'proxied': False
        }
        
        for domain in domains :
            zone_id =  self._get_zone_id(domain)
            
            add = requests.post(self.URL["domains"]+f'/{zone_id}/dns_records', headers=self.headers ,json=dns_data ).json()

            if add['success'] == True:
                name = add['result']['name']
                print(f'{name} 添加成功')
            else:
                print('紀錄添加失敗')
                raise ValueError ( f'{domain} update 失敗')

    def delete(self , domains, name ):
        
        self.name = name  # 需要帶入全域變數 , 不然回全圈執行過一遍就會不見
        #domain_list = self._get_records_name_id(dead_ip=None , domains=self.domain) 

        for domain in domains :
            zone_id =  self._get_zone_id(domain)
            record_id = self._get_records_id(domain , self.name )
            #record_id = self._records_id.get(domain)

            resp = requests.delete(self.URL["domains"]+f'/{zone_id}/dns_records/{record_id}', headers=self.headers ).json()

            if resp['success'] == True:
                if name == '@':
                    name = f'{domain}'
                    print(f'{name} 刪除成功')
                else:
                    name = f'{self.name}.{domain}'
                    print(f'{name} 刪除成功')
            else:
                print('紀錄添加失敗')
                raise ValueError ( f'{domain} delete 失敗')

    def add_domain (self , domains):
        resp = self._check_api( self.URL['domains'] , self.headers)

        for i in resp['result']:
            account_id = (i['account']['id'])
            break
        
        for domain in domains:
            data = {"account": 
                    {"id": account_id} , 
                    "name": domain ,
                    "jump_start": True 
                }
            
            add_domain = requests.post(self.URL["domains"], headers=self.headers ,json=data ).json()
            if add_domain['success'] == True:
                print(domain+'添加完成')
            elif add_domain['success'] == False:
                error_list = add_domain['errors']
                for i in range(len(error_list)):
                    print('添加失敗: '+error_list[i]['message'])   


    def tg_send (self , message ,chat_id , bottoken):
        text = (f"{self.day} - {message}")
        send_text = requests.post(f'https://api.telegram.org/bot{bottoken}/sendMessage?chat_id={chat_id}&&parse_mode=Markdown&text={text}')
        print(send_text.status_code)


