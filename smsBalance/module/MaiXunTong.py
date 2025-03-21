
from module.smsInterface import SMS
import requests

class Maixunting(SMS) :
    
    def __init__(self , account , token):
    
        super().__init__(account , token)
        self.url = f'http://116.62.212.142/msg/QueryBalance?account={account}&pswd={token}'
    

    def SMSQuery(self):
        
        SMS_rquest = requests.get(f'{self.url}').text
        String_processing = SMS_rquest.split('\n')
        status_code = String_processing[0].split(',')[1]

        match status_code:
            case '101':
                raise Exception(f"短信商:麥訊通 帳號:{self.account} 無此用戶")
            case '102':
                raise Exception(f"短信商:麥訊通 帳號:{self.account} 密碼錯誤")
            case '104':
                raise Exception(f"短信商:麥訊通 帳號:{self.account} 密碼錯誤")
            case '0':
                SMS_Remaining = String_processing[1].split(',')[1]
                return SMS_Remaining
            case _:
                raise Exception(f"短信商:麥訊通 帳號:{self.account} 未知錯誤，錯誤狀態碼為: {status_code}")