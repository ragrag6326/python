from abc import ABCMeta, abstractmethod

class SMS(metaclass=ABCMeta):
    
    def __init__(self , account: str, token: str):
        self.account = account
        self.token = token

    # def get_account(self):
    #     return self.account
    
    # def get_token(self):
    #     return self.token
    
    # def get_url(self):
    #     return 
    
    @abstractmethod
    def SMSQuery(self):
        pass
    