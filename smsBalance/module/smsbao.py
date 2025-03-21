from module.smsInterface import SMS
import requests


class Smsbao(SMS) :
    
    def __init__(self, account: str, token: str):
        self.url = f'https://www.smsbao.com/query?u={account}&p={token}'
        super().__init__(account, token)
        
    def SMSQuery(self):

        SMS_rquest = requests.get(f'{self.url}').text
        text = SMS_rquest.split(',')
        status_code = text[0].replace('\n0', '')
            
        if status_code[0] == '0' :
            SMS_Remaining = text[1]
            return SMS_Remaining
        
        match status_code:
            case '30':
                raise Exception(f"短信商:短信寶 帳號:{self.account} 帳號或密碼錯誤")
            case '40':
                raise Exception(f"短信商:短信寶 帳號:{self.account} 帳號或密碼錯誤")
            case '41':
                raise Exception(f"短信商:短信寶 帳號:{self.account} 餘額不足")
            case _:
                raise Exception(f"短信商:短信寶 帳號:{self.account} 未知錯誤，錯誤狀態碼為:{status_code} ，請至官網查詢 https://www.smsbao.com/openapi/213.html")