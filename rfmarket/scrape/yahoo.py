from .. import api
from ..tools import storage, log

class Yahoo():
    def __init__(self):
        self.__dataPath = 'data/scrape/yahoo'
        self.__dataPathFull = 'data/scrape/yahoo_full'
    
    def get(self, symbols, refresh=False, fullData=False):
        if not refresh:
            log.info('scrape.Yahoo retrieve data from storage')
            if fullData:
                return storage.get(self.__dataPathFull)
            return storage.get(self.__dataPath)
        
        data = {}

        yh = api.Yahoo()
        modules = api.Yahoo().getQuoteSummaryModules()
        data['quotes'] = yh.getQuoteSummary(symbols, modules)

        storage.backup(self.__dataPath)
        storage.save(self.__dataPath, data)

        data['charts'] = yh.getCharts(symbols, '5y', '1d')
        
        # sve full data for if needed later
        storage.save(self.__dataPathFull, data)
        
        # removing indicators, it's too much data
        for symbol, symbolData in data['charts'].items():
            if 'indicators' in symbolData:
                symbolData.pop('indicators')

        storage.backup(self.__dataPath)
        storage.save(self.__dataPath, data)
        
        return data
    