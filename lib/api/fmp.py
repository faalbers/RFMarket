import config, requests

# Financial Modeling Prep API wrapper

class FMP():
    def __request(self, endpoint, params={}):
        reqUrl = self.__urlMain+endpoint
        params['apikey'] = config.KEYS['FMP']['KEY']
        result = requests.get(reqUrl, params)
        result = result.json()
        if 'Error Message' in result:
            print('FMP: ERROR: %s' % result['Error Message'])
            return None
        return result
        
    def __init__(self):
        self.__urlMain = 'https://financialmodelingprep.com/api/'

    def getStockList(self):
        result = self.__request('v3/stock/list')
        stockList = {}
        if result == None:
            return result
        for item in result:
            symbol = item['symbol']
            item.pop('symbol')
            stockList[symbol] = item
        return stockList