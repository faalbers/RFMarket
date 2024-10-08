# scrape all data to create new user data
from .fmp import FMP
from .polygon import Polygon
from .saved import Saved
from .yahoo import Yahoo
from copy import deepcopy
from datetime import datetime
from pprint import pp
from ..tools import log
__all__ = ['Scrape']

class Scrape():
    # symbol template for scrades user data
    __symbol = {
        'name': None,
        'price': None,
        'cik': None,
        'exchange': {
            'MIC': None,
            'acronym': None,
            'cicode': None,
            'name': None,
            'category': None,
            'country': None,
            'city': None,
        },
        'type': {
            'code': None,
            'assetType': None,
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
        'events': {
            'dividends': None,
            'splits': None,
            'capitalGains': None,
        },
        'timestamps': {
            'fmp': None,
            'polygon': None,
            'yahooQuotes': None,
            'yahooCharts': None,
            'price': None,
        },
    }

    def __init__(self):
        pass

    def getData(self,
                refreshFMP=False,
                refreshPolygon=False,
                refreshYahoo=False):
        
        log.info("Scrape Data from files and API's")

        # initialize user data for creation
        userData = {}
        
        # get data from saved files under data/saved
        # read info.txt on how to retrieve them
        savedData = Saved().getData()

        # gather US market acronyms
        # maybe create later for all countries
        usAcronyms = set()
        for mic, micData in savedData['MIC']['data'].items():
            if micData['ISO COUNTRY CODE (ISO 3166)'] == 'US':
                usAcronyms.add(micData['ACRONYM'])

        # gather FMP data
        fmpData = FMP().get(refresh=refreshFMP)
        log.info('Parse FMP data into user data')
        symbolsNew = set()
        symbolsUpdated = set()
        for symbol, stockData in fmpData['stocklist'].items():
            symbol = symbol.upper()
            # initialze new stock symbol entry in user data
            if not symbol in userData:
                symbolsNew.add(symbol)
                userData[symbol] = deepcopy(self.__symbol)
            
            # retieve FMP data into user data
            userData[symbol]['timestamps']['fmp'] = stockData['timestamp']
            if stockData['name'] != None:
                symbolsUpdated.add(symbol)
                userData[symbol]['name'] = stockData['name']
            if stockData['price'] != None:
                symbolsUpdated.add(symbol)
                userData[symbol]['price'] = stockData['price']
                userData[symbol]['timestamps']['price'] = stockData['timestamp']
            if stockData['type'] != None:
                symbolsUpdated.add(symbol)
                userData[symbol]['type']['code'] = stockData['type'].upper()
            if stockData['exchange'] != None:
                symbolsUpdated.add(symbol)
                userData[symbol]['exchange']['acronym'] = stockData['exchangeShortName'].upper()
                userData[symbol]['exchange']['name'] = stockData['exchange']
                if userData[symbol]['exchange']['acronym'] in usAcronyms:
                    userData[symbol]['exchange']['country'] = 'United States'
        log.info('New symbols added to user data: %s' % len(symbolsNew))
        log.info('Symbols updated in user data  : %s' % len(symbolsUpdated))

        # gather Polygon data
        polygonData = Polygon().get(refresh=refreshPolygon)
        log.info('Parse Polygon data into user data')
        symbolsNew = set()
        symbolsUpdated = set()
        for symbol, tickerData in polygonData['tickers'].items():
            symbol = symbol.upper()
            # initialze new stock symbol entry in user data
            if not symbol in userData:
                symbolsNew.add(symbol)
                userData[symbol] = deepcopy(self.__symbol)
            
            # retieve Polygon data into user data
            userData[symbol]['timestamps']['polygon'] = tickerData['timestamp']
            if 'last_updated_utc' in tickerData:
                if '.' in tickerData['last_updated_utc']:
                    dateFormat = '%Y-%m-%dT%H:%M:%S.%fZ'
                else:
                    dateFormat = '%Y-%m-%dT%H:%M:%SZ'
                utcDate = datetime.strptime(tickerData['last_updated_utc'], dateFormat)
                pstDate = int((utcDate - (datetime.utcnow() - datetime.now())).timestamp())
                symbolsUpdated.add(symbol)
                userData[symbol]['timestamps']['polygon'] = pstDate
            else:
                userData[symbol]['timestamps']['polygon'] = tickerData['timestamp']            
            if 'name' in tickerData:
                if userData[symbol]['name'] == None or (len(tickerData['name']) > len(userData[symbol]['name'])):
                    symbolsUpdated.add(symbol)
                    userData[symbol]['name'] = tickerData['name']
            if 'cik' in tickerData:
                symbolsUpdated.add(symbol)
                userData[symbol]['cik'] = tickerData['cik']
            if 'type' in tickerData:
                symbolsUpdated.add(symbol)
                userData[symbol]['type']['code'] = tickerData['type']
                if tickerData['type'] in polygonData['tickerTypes']:
                    tickerTypeData = polygonData['tickerTypes'][tickerData['type']]
                    userData[symbol]['type']['description'] = tickerTypeData['description']
                    userData[symbol]['type']['assetClass'] = tickerTypeData['asset_class'].upper()
                    userData[symbol]['type']['locale'] = tickerTypeData['locale'].upper()
            else:
                if 'market' in tickerData:
                    symbolsUpdated.add(symbol)
                    userData[symbol]['type']['assetClass'] = tickerData['market'].upper()
                if 'locale' in tickerData:
                    symbolsUpdated.add(symbol)
                    userData[symbol]['type']['locale'] = tickerData['locale'].upper()

            if 'primary_exchange' in tickerData:
                exchangeData = savedData['MIC']['data'][tickerData['primary_exchange']]
                symbolsUpdated.add(symbol)
                userData[symbol]['exchange']['MIC'] = tickerData['primary_exchange']
                userData[symbol]['exchange']['acronym'] = exchangeData['ACRONYM']
                userData[symbol]['exchange']['name'] = exchangeData['MARKET NAME-INSTITUTION DESCRIPTION']
                userData[symbol]['exchange']['category'] = exchangeData['MARKET CATEGORY CODE']
                userData[symbol]['exchange']['country'] = savedData['country']['data'][exchangeData['ISO COUNTRY CODE (ISO 3166)']]['Name']
                userData[symbol]['exchange']['city'] = exchangeData['CITY']
        
            if 'currency_name' in tickerData:
                if tickerData['currency_name'].upper() == 'USD':
                    tickerData['currency_name'] = 'United States Dollar'
                symbolsUpdated.add(symbol)
                userData[symbol]['currency']['name'] = tickerData['currency_name']
            if 'currency_symbol' in tickerData:
                symbolsUpdated.add(symbol)
                userData[symbol]['currency']['symbol'] = tickerData['currency_symbol'].upper()
            else:
                if userData[symbol]['currency']['name'] == 'United States Dollar':
                    symbolsUpdated.add(symbol)
                    userData[symbol]['currency']['symbol'] = 'USD'
            if 'base_currency_name' in tickerData:
                symbolsUpdated.add(symbol)
                userData[symbol]['currency']['nameBase'] = tickerData['base_currency_name']
            if 'base_currency_symbol' in tickerData:
                symbolsUpdated.add(symbol)
                userData[symbol]['currency']['symbolBase'] = tickerData['base_currency_symbol'].upper()
        log.info('New symbols added to user data: %s' % len(symbolsNew))
        log.info('Symbols updated in user data  : %s' % len(symbolsUpdated))

        # limit symbol user data to US stock exchanges
        removeSymbols = set()
        for symbol, stockData in userData.items():
            if stockData['exchange']['country'] != 'United States':
                removeSymbols.add(symbol)
        for symbol in removeSymbols: userData.pop(symbol)
        log.info('User data symbols with United States exchange count: %s' % len(userData))
        
        # gather yahoo data
        symbols = list(userData.keys())
        yahooData = Yahoo().get(symbols, refresh=refreshYahoo)
        log.info('Parse Yahoo data into user data')
        params = set()
        quoteModules = set()
        quoteModulesDone = set()
        for symbol, quoteData in yahooData['quotes'].items():
            modules = set((quoteData.keys()))
            userData[symbol]['timestamps']['yahooQuotes'] = quoteData['timestamp']
            modules.remove('timestamp')
            quoteModules = quoteModules.union(modules)
            if 'quoteType' in quoteData:
                quoteModulesDone.add('quoteType')
                moduleData = quoteData['quoteType']
                if 'exchange' in moduleData and moduleData['exchange'] != None:
                    userData[symbol]['exchange']['cicode'] = moduleData['exchange']
                if 'longName' in moduleData and moduleData['longName'] != None:
                    if userData[symbol]['name'] == None or (len(moduleData['longName']) > len(userData[symbol]['name'])):
                        userData[symbol]['name'] = moduleData['longName']
            if 'price' in quoteData:
                quoteModulesDone.add('price')
                moduleData = quoteData['price']
                priceTime = None
                price = None
                if 'postMarketPrice' in moduleData and moduleData['postMarketPrice'] != None:
                    priceTime = moduleData['postMarketTime']
                    price = moduleData['postMarketPrice']
                elif 'regularMarketPrice' in moduleData and moduleData['regularMarketPrice'] != None:
                    priceTime = moduleData['regularMarketTime']
                    price = moduleData['regularMarketPrice']
                if price != None:
                    if userData[symbol]['timestamps']['price'] == None or (priceTime > userData[symbol]['timestamps']['price']):
                        userData[symbol]['price'] = price
                        userData[symbol]['timestamps']['price'] = priceTime
                if 'quoteType' in moduleData and moduleData['quoteType'] != None:
                    userData[symbol]['type']['assetType'] = moduleData['quoteType'].upper()
                if 'currencySymbol' in moduleData and moduleData['currencySymbol'] != None:
                    userData[symbol]['currency']['symbolBase'] = moduleData['currencySymbol']
                if 'currency' in moduleData and moduleData['currency'] != None:
                    userData[symbol]['currency']['symbol'] = moduleData['currency'].upper()
        # pp(quoteModules.difference(quoteModulesDone))
        chartTypes = set()
        chartTypesDone = set()
        for symbol, chartData in yahooData['charts'].items():
            types = set((chartData.keys()))
            userData[symbol]['timestamps']['yahoo'] = chartData['timestamp']
            types.remove('timestamp')
            chartTypes = chartTypes.union(types)
            if 'events' in chartData:
                chartTypesDone.add('events')
                events = chartData['events']
                # params = params.union(events.keys())
                if 'dividends' in events:
                    userData[symbol]['events']['dividends'] = events['dividends']
                if 'splits' in events:
                    userData[symbol]['events']['splits'] = events['splits']
                if 'capitalGains' in events:
                    userData[symbol]['events']['capitalGains'] = events['capitalGains']

        # pp(chartTypes.difference(chartTypesDone))
        # pp(params)
        
        # pp(userData['ORKA'])
        # pp(userData['MMM'])

        # return created user data
        log.info('Total user data symbols: %s' % len(userData))
        return userData

