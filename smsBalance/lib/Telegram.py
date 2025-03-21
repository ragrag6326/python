from abc import ABCMeta, abstractmethod
import requests


class ISend(metaclass=ABCMeta):
    @abstractmethod
    def SendMessage(self) -> bool:
        pass

    @abstractmethod
    def SendPhote(self) -> bool:
        pass


class Telegram(ISend):
    
    def __init__(self , bot_token: str , chat_id : str , thread_id=None):
        self.token = bot_token
        self.chat_id = chat_id
        self.thread_id = thread_id
        self.url = f"https://api.telegram.org/bot{bot_token}"


    def SendMessage(self , text : str ) -> bool :
        methon = "sendMessage"
        request_url = f'{self.url}/{methon}'
        
        request_data = {
            'chat_id': self.chat_id,
            'text': text 
        }

        if self.thread_id:
            request_data.update({'message_thread_id' : self.thread_id})

        respone = requests.post(request_url, request_data)

        if respone.ok:
            return True
        else:
            print(respone.text)
            print(respone.status_code)
            return False
    
    def SendPhote(self , photo) -> bool :

        methon = "sendPhoto"
        request_url = f'{self.url}/{methon}'

        photos = {'photo' : open(photo , 'rb')}

        request_data = {
            'chat_id': self.chat_id,
        }

        if self.thread_id:
            request_data.update({'message_thread_id' : self.thread_id})

        respone = requests.post(request_url , request_data , files=photos)
        if respone.ok:
            return True
        else:
            print("Failed to send Photo.")
            print(respone.text)
            print(respone.status_code)
            return False
        
    def SendFile( self , file ) -> bool :
        methon = "sendDocument"
        request_url = f'{self.url}/{methon}'

        documents = {'document' : open(f'{file}', 'rb')}

        request_data = {
            'chat_id': self.chat_id,
        }

        if self.thread_id:
            request_data.update({'message_thread_id' : self.thread_id})

        respone = requests.post(request_url , request_data , files=documents)
        if respone.ok:
            return True
        else:
            print("Failed to send file.")
            print(respone.text)
            print(respone.status_code)
            return False