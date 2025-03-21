from module import *
from lib import Telegram
import sys


# chat_id  
# thread_id , 如沒有則會發到 General 群組
TELEGRAM_CONF = {
        "bot_token" : "" ,
        "chat_id" : "" ,
        "thread_id" : ""
}

bot_token = TELEGRAM_CONF['bot_token']
chat_id = TELEGRAM_CONF['chat_id']
thread_id = TELEGRAM_CONF['thread_id']

telegram = Telegram ( bot_token , chat_id , thread_id)


if __name__ == '__main__':

    args = sys.argv[1]
    file_path = args

    for line in open(file_path, 'r', encoding='UTF-8'):
        
        String_processing = line.split(' ')
        
        SMS_provider= String_processing[0]
        Game_name = String_processing[1]
        Account = String_processing[2]
        Token = String_processing[3].replace('\n', '')

        if SMS_provider[0] != '#' :
            SMS_PROVIDER_FUNCTION = {
                '短信宝' : Smsbao (Account , Token),
                '云信使' : YuXinShi (Account , Token),
                '麦讯通' : Maixunting (Account , Token) ,
            }

            SmsProvider = SMS_PROVIDER_FUNCTION.get(SMS_provider)

            if not SmsProvider:
                SmsProvider = '、 '.join(SMS_PROVIDER_FUNCTION.keys())
                print(f'目前只支援 {len(SMS_PROVIDER_FUNCTION.items())}間 , [ {SmsProvider} ] 其他間太爛找不到API')
                continue
            try:
                SMS_Remaining = SmsProvider.SMSQuery()

                if int(SMS_Remaining) < 500 :
                    Emergency_level = '🔥'
                    alter = f'{Emergency_level} ({Game_name}) 簡訊商:{SMS_provider} 帳號:{Account} 剩餘:{SMS_Remaining}條 趕緊請運營儲值不然又要🐶叫了'
                    telegram.SendMessage(alter)

                else:
                    print(f'({Game_name}) 簡訊充足 {SMS_Remaining} ')

            except Exception as err :
                telegram.SendMessage(err)
                print(f'({Game_name}) {err} ')


