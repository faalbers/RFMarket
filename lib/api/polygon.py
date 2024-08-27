import config, requests
from datetime import datetime
from time import sleep

# Polygon API wrapper

class Polygon():
    def __request(self, endpoint, params={}):
        nextUrl = self.__urlMain+endpoint
        params['apikey'] = config.KEYS['POLYGON']['KEY']

        reqCount = 0
        plgData = []
        while nextUrl != None:
            if reqCount >= 5:
                print('Polygon: 60 sec sleep after 5 request calls')
                sleep(60)
                reqCount = 0
            result = requests.get(nextUrl, params=params)
            reqCount += 1
            if result.status_code == 200:
                result = result.json()
            else:
                print('Polygon: Data request failed: %s' % nextUrl)
                if result.status_code == 403:
                    print('Error Message: %s' % result.json()['Error Message'])
                    return None
            plgData.append(result)
            nextUrl = None
            if 'next_url' in result:
                nextUrl = result['next_url']
        return plgData
        
    def __init__(self):
        self.__urlMain = 'https://api.polygon.io/'

    def getTickers(self):
        result = self.__request('v3/reference/tickers', params={'limit': 1000})
        tickers = {}
        if result == None:
            return result
        timestamp = int(datetime.now().timestamp())
        for block in result:
            for item in block['results']:
                ticker = item.pop('ticker')
                item['timestamp'] = timestamp
                tickers[ticker] = item

        return tickers
    
    def getTickerTypes(self):
        result = self.__request('/v3/reference/tickers/types')
        data = {}
        for block in result:
            for tickerTypeData in block['results']:
                tickerType = tickerTypeData.pop('code')
                data[tickerType] = tickerTypeData
        return data
    
