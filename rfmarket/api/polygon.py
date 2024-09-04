import config
from rfmarket.api.request import Request
from datetime import datetime
from time import sleep
from pprint import pp
from ..tools import log
from ratelimit import limits, sleep_and_retry

# Polygon API wrapper

class Polygon():
    @sleep_and_retry
    @limits(calls=5, period=60)
    def __requestCall(self, requestArgs):
        try:
            response = self.__request.get(**requestArgs)
        except Exception:
            log.exception('__requestCall')
            return None

        return response
    
    def __initRequest(self):
        params = {'apikey': config.KEYS['POLYGON']['KEY']}
        self.__request = Request(params=params)
        
    def __init__(self):
        self.__initRequest()
        self.__urlMain = 'https://api.polygon.io/'

    def requestOld(self, url=None, params={}, headers={}, cookies={}):
        nextUrl = url
        reqCount = 0
        plgData = []
        while nextUrl != None:
            if reqCount >= 5:
                print('Polygon: 60 sec sleep after 5 request calls')
                sleep(60)
                reqCount = 0
            result = self.__request.get(nextUrl, params=params, headers=headers, cookies=cookies)
            reqCount += 1
            if result.status_code == 200:
                result = result.json()
            else:
                print('Polygon: Data request failed: %s' % nextUrl)
                print('Status Code: %s: %s' % (result.status_code, config.STATUS_CODES[result.status_code]))
                if result.headers.get('content-Type') != None and result.headers.get('content-Type').startswith('application/json'):
                    pp(result.json())
                else:
                    pp(result.text)
                return None
            plgData.append(result)
            nextUrl = None
            if 'next_url' in result:
                nextUrl = result['next_url']
        return plgData

    def getTickers(self):
        log.info('Retrieve tickers from Polygon')
        tickers = {}
        nextReqArgs = {
            'url': self.__urlMain+'v3/reference/tickers',
            'params': {
                'limit': 1000,
            },
        }
        while nextReqArgs != None:
            timestamp = int(datetime.now().timestamp())
            response = self.__requestCall(nextReqArgs)
            if response == None: return tickers
            nextReqArgs = None
            if response.status_code == 200 and response.headers.get('content-type').startswith('application/json'):
                responseData = response.json()
                for item in responseData['results']:
                    ticker = item.pop('ticker').upper()
                    item['timestamp'] = timestamp
                    tickers[ticker] = item
                log.debug('Got %s tickers so far ...' % len(tickers))
                if 'next_url' in responseData:
                    nextReqArgs = {'url': responseData['next_url']}
        
        return tickers
    
    def getTickerTypes(self):
        log.info('Retrieve ticker types from Polygon')
        tickerTypes = {}
        nextReqArgs = {'url': self.__urlMain+'v3/reference/tickers/types'}
        while nextReqArgs != None:
            response = self.__requestCall(nextReqArgs)
            if response == None: return tickerTypes
            nextReqArgs = None
            if response.status_code == 200 and response.headers.get('content-type').startswith('application/json'):
                responseData = response.json()
                for tickerTypeData in responseData['results']:
                    tickerType = tickerTypeData.pop('code').upper()
                    tickerTypes[tickerType] = tickerTypeData
                log.debug('Got %s tickers types so far ...' % len(tickerTypes))
                if 'next_url' in responseData:
                    nextReqArgs = {'url': responseData['next_url']}
        return tickerTypes
    
