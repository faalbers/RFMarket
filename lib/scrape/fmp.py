from lib import api
from lib.tools import storage
from datetime import datetime

# retrieve data from Financial Modeling Prep API

class FMP():
    def __init__(self):
        self.__dataPath = 'data/scrape/fmp'
    
    def get(self, refresh=False):
        if not refresh:
            # return already scraped data
            return storage.get(self.__dataPath)
        
        data = {}
        # retrieve data from API
        data['stocklist'] = api.FMP().getStocklist()
        
        # macke a backup and save newly retrieved FMP data
        storage.backup(self.__dataPath)
        storage.save(self.__dataPath, data)
        
        return data
    