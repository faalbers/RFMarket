from .. import api
from ..tools import storage, log
from datetime import datetime

class Polygon():
    def __init__(self):
        self.__dataPath = 'data/scrape/polygon'
    
    def get(self, refresh=False):
        if not refresh:
            log.info('Retrieve Polygon data from storage')
            return storage.get(self.__dataPath)
        
        data = {}
        polygon = api.Polygon()
        data['tickers'] = polygon.getTickers()
        data['tickerTypes'] = polygon.getTickerTypes()
        
        storage.backup(self.__dataPath)
        storage.save(self.__dataPath, data)
        
        return data
    