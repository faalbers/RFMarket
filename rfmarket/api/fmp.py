import config
from rfmarket.api.request import Request
from datetime import datetime
from pprint import pp
from ..tools import log

# Financial Modeling Prep API wrapper

class FMP():
    def __initRequest(self):
        params = {'apikey': config.KEYS['FMP']['KEY']}
        self.__request = Request(params=params)
        
    def __init__(self):
        self.__initRequest()
        self.__urlMain = 'https://financialmodelingprep.com/api/'

    def getStocklist(self):
        log.info('Retrieve stock list from FMP')
        result = self.__request.get(self.__urlMain+'v3/stock/list')
        if result.status_code == 200:
            type =  result.headers.get('content-Type')
            if type.startswith('application/json'):
                result = result.json()
                stockList = {}
                timestamp = int(datetime.now().timestamp())
                for item in result:
                    symbol = item['symbol'].upper()
                    item.pop('symbol')
                    item['timestamp'] = timestamp
                    stockList[symbol] = item
                log.info('Found %s stocks' % len(stockList))
                return stockList
        return None
