from .scrape import *
from .tools import log

class RFMarket():
    def __init__(self,
                refreshFMP=False,
                refreshPolygon=False,
                refreshYahoo=False,
                logLevel=log.WARNING):
        log.initLogger(logLevel=logLevel)
        self.__data = Scrape().getData(
                refreshFMP=refreshFMP,
                refreshPolygon=refreshPolygon,
                refreshYahoo=refreshYahoo)
    
    @log.indent_decorator
    def logTest(self, a, b, c):
        log.info('BLAAHHH')
