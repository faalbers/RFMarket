from lib import api
from lib.tools import storage
from datetime import datetime

class FMP():
    def __init__(self):
        self.__dataPath = 'data/scrape/fmp'
    
    def get(self, refresh=False):
        if not refresh:
            return storage.get(self.__dataPath)
        
        data = {}
        data['stocklist'] = api.FMP().getStocklist()
        
        storage.backup(self.__dataPath)
        storage.save(self.__dataPath, data)
        
        return data
    