from lib.scrape.fmp import FMP
from lib.scrape.polygon import Polygon
from lib.scrape.saved import Saved
from lib.tools import storage
from copy import deepcopy
from pprint import pp
import numpy as np
from datetime import datetime

class Scrape():
    # symbol template
    __symbol = {
        'name': None,
        'price': None,
        'cik': None,
        'exchange': {
            'MIC': None,
            'acronym': None,
            'name': None,
            'category': None,
            'country': None,
            'city': None,
        },
        'type': {
            'code': None,
            'description': None,
            'assetClass': None,
            'locale': None,
        },
        'currency': {
            'name': None,
            'symbol': None,
            'nameBase': None,
            'symbolBase': None,
        },
        'timestamps': {
            'fmp': None,
            'polygon': None,
            'price': None,
        },
    }

    def __init__(self):
        pass

    def getData(self,
                refreshFMP=False,
                refreshPolygon=False):
        # get saved data
        savedData = Saved().getData()
        # initialize data
        data = {}
        params = set()

        # gather FMP data
        fmpData = FMP().get(refresh=refreshFMP)
        for symbol, stockData in fmpData['stocklist'].items():
            # params = params.union(stockData.keys())
            if not symbol in data:
                data[symbol] = deepcopy(self.__symbol)
            data[symbol]['timestamps']['fmp'] = stockData['timestamp']
            if stockData['name'] != None:
                data[symbol]['name'] = stockData['name']
            if stockData['price'] != None:
                data[symbol]['price'] = stockData['price']
                data[symbol]['timestamps']['price'] = stockData['timestamp']
            if stockData['type'] != None:
                data[symbol]['type']['code'] = stockData['type'].upper()
            if stockData['exchange'] != None:
                data[symbol]['exchange']['acronym'] = stockData['exchangeShortName'].upper()
                data[symbol]['exchange']['name'] = stockData['exchange']
        
        # gather Polygon data
        polygonData = Polygon().get(refresh=refreshPolygon)
        for symbol, tickerData in polygonData['tickers'].items():
            if not symbol in data:
                data[symbol] = deepcopy(self.__symbol)
            params = params.union(tickerData.keys())
            if symbol == 'AAPL':
                pp(tickerData)
            
            if 'last_updated_utc' in tickerData:
                if '.' in tickerData['last_updated_utc']:
                    dateFormat = '%Y-%m-%dT%H:%M:%S.%fZ'
                else:
                    dateFormat = '%Y-%m-%dT%H:%M:%SZ'
                utcDate = datetime.strptime(tickerData['last_updated_utc'], dateFormat)
                pstDate = int((utcDate - (datetime.utcnow() - datetime.now())).timestamp())
                data[symbol]['timestamps']['polygon'] = pstDate
            else:
                data[symbol]['timestamps']['polygon'] = tickerData['timestamp']            
            if 'name' in tickerData:
                if data[symbol]['name'] == None or len(tickerData['name']) > len(data[symbol]['name']):
                    data[symbol]['name'] = tickerData['name']
            if 'cik' in tickerData:
                data[symbol]['cik'] = tickerData['cik']
            if 'type' in tickerData:
                data[symbol]['type']['code'] = tickerData['type']
                if tickerData['type'] in polygonData['tickerTypes']:
                    tickerTypeData = polygonData['tickerTypes'][tickerData['type']]
                    data[symbol]['type']['description'] = tickerTypeData['description']
                    data[symbol]['type']['assetClass'] = tickerTypeData['asset_class']
                    data[symbol]['type']['locale'] = tickerTypeData['locale'].upper()
            else:
                if 'market' in tickerData:
                    data[symbol]['type']['assetClass'] = tickerData['market']
                if 'locale' in tickerData:
                    data[symbol]['type']['locale'] = tickerData['locale'].upper()

            if 'primary_exchange' in tickerData:
                exchangeData = savedData['MIC']['data'][tickerData['primary_exchange']]
                data[symbol]['exchange']['MIC'] = tickerData['primary_exchange']
                data[symbol]['exchange']['acronym'] = exchangeData['ACRONYM']
                data[symbol]['exchange']['name'] = exchangeData['MARKET NAME-INSTITUTION DESCRIPTION']
                data[symbol]['exchange']['category'] = exchangeData['MARKET CATEGORY CODE']
                data[symbol]['exchange']['country'] = savedData['country']['data'][exchangeData['ISO COUNTRY CODE (ISO 3166)']]['Name']
                data[symbol]['exchange']['city'] = exchangeData['CITY']
            
            if 'currency_name' in tickerData:
                if tickerData['currency_name'].upper() == 'USD':
                    tickerData['currency_name'] = 'United States Dollar'
                data[symbol]['currency']['name'] = tickerData['currency_name']
            if 'currency_symbol' in tickerData:
                data[symbol]['currency']['symbol'] = tickerData['currency_symbol'].upper()
            else:
                if data[symbol]['currency']['name'] == 'United States Dollar':
                    data[symbol]['currency']['symbol'] = 'USD'
            if 'base_currency_name' in tickerData:
                data[symbol]['currency']['nameBase'] = tickerData['base_currency_name']
            if 'base_currency_symbol' in tickerData:
                data[symbol]['currency']['symbolBase'] = tickerData['base_currency_symbol'].upper()
            
        params = list(params)
        params.sort()
        print(params)

        return data
        