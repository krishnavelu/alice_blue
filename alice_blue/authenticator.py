from abc import ABC, abstractmethod


class Autheticator(ABC):
    '''
    Enables custom implementation for get_password and get_twoFA
    '''
    def __init__(self, username, api_secret, app_id):
        self.username = username
        self.api_secret = api_secret
        self.app_id = app_id

    @abstractmethod
    def get_password(self) -> str:
        pass

    @abstractmethod
    def get_twoFA(self, queries:[]) -> list:
        '''
        Accepts list of questions and
        returns answers to those queries as list
        '''
        pass
