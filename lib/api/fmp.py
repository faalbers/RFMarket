import config, requests

# Financial Modeling Prep API wrapper

class FMP():
    __urlMain = 'https://financialmodelingprep.com/api/'
    
    def __init__(self):
        pass

    def getStockList(self):
        reqUrl = self.__urlMain+'v3/stock/list'
        params = {'apikey': config.KEYS['FMP']['KEY']}
        result = requests.get(reqUrl, params)
        result = result.json()
        if 'Error Message' in result:
            print('FMP: ERROR: %s' % result['Error Message'])
            return {}
        return result
    
