from .scrape import *
from .tools import log, storage

class RFMarket():
    mcalls = 1
    mperiod = 1

    def __init__(self,
                refreshFMP=False,
                refreshPolygon=False,
                refreshYahoo=False,
                logLevel=log.WARNING):
        
        self.__dataPath = 'data/work/data'
        log.initLogger(logLevel=logLevel)
        if refreshFMP or refreshPolygon or refreshYahoo:
            self.__data = Scrape().getData(
                    refreshFMP=refreshFMP,
                    refreshPolygon=refreshPolygon,
                    refreshYahoo=refreshYahoo)
            storage.backup(self.__dataPath)
            storage.save(self.__dataPath, self.__data)

        else:
            self.__data = storage.get(self.__dataPath)
    
    def getData(self):
        return self.__data
    
    def getSymbolData(self, symbol):
        symbol = symbol.upper()
        if not symbol in self.__data: return None
        return self.__data[symbol]

    @log.indent_decorator
    def logTest(self, a, b, c):
        log.info('BLAAHHH')
    
