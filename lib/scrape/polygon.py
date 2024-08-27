from lib import api
from lib.tools import storage
from datetime import datetime

class Polygon():
    def __init__(self):
        self.__dataPath = 'data/scrape/polygon'
    
    def get(self, refresh=False):
        if not refresh:
            return storage.get(self.__dataPath)
        
        data = {}
        data['tickers'] = api.Polygon().getTickers()
        data['tickerTypes'] = api.Polygon().getTickerTypes()
        
        storage.backup(self.__dataPath)
        storage.save(self.__dataPath, data)
        
        return data
    