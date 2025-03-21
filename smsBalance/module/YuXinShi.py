from module.smsInterface import SMS
import requests

class YuXinShi (SMS) :

    def __init__(self, account: str, token: str):
        super().__init__(account, token)
        self.url = f'http://api.sms.cn/sms/?ac=number&uid={account}&pwd={token}'

    def SMSQuery( self ) -> str :
        SMS_rquest = requests.get(f'{self.url}').json()
        status_code = SMS_rquest['stat']
        status_message = SMS_rquest['message']

        match (status_code, status_message):
            case ('100', '成功'):
                return SMS_rquest['number']
            case ('101', '验证失败'):
                raise Exception(f"短信商:雲信使 帳號:{self.account} 帳號或密碼錯誤")
            case _:
                raise Exception(f"短信商:雲信使 帳號:{self.account} 未知錯誤，錯誤狀態碼為:{status_code} ，請至官網查詢 https://www.sms.cn/smsapi.html")