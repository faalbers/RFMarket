from .. import api
from ..tools import storage

class Yahoo():
    def __init__(self):
        self.__dataPath = 'data/scrape/yahoo'
    
    def get(self, symbols, refresh=False):
        if not refresh:
            return storage.get(self.__dataPath)
        
        data = {}

        yh = api.Yahoo()
        # modules = api.Yahoo().getQuoteSummaryModules()
        # data['quotes'] = api.Yahoo().getQuoteSummary(symbols, modules, verbose=True)
        data['charts'] = yh.getCharts5y(symbols)
        
        storage.backup(self.__dataPath)
        storage.save(self.__dataPath, data)
        
        return data
    