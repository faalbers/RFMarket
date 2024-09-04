from .. import api
from ..tools import storage, log
from datetime import datetime

# retrieve data from Financial Modeling Prep API

class FMP():
    def __init__(self):
        self.__dataPath = 'data/scrape/fmp'
    
    def get(self, refresh=False):
        if not refresh:
            # return already scraped data
            log.info('Retrieve FMP data from storage')
            return storage.get(self.__dataPath)
        
        data = {}
        # retrieve data from API
        fmp = api.FMP()
        data['stocklist'] = fmp.getStocklist()
        
        # macke a backup and save newly retrieved FMP data
        storage.backup(self.__dataPath)
        storage.save(self.__dataPath, data)
        
        return data
    