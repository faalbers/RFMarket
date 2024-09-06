import config, sys
from rfmarket.api.request import Request
from datetime import datetime, timedelta
from rfmarket.tools import storage
from pprint import pp
from ratelimit import limits, sleep_and_retry
from time import sleep
from ..tools import log

# Financial Modeling Prep API wrapper

# consts
class Yahoo():
    def __requestCall(self, requestArgs):
        try:
            response = self.__request.get(**requestArgs)
        except Exception:
            log.exception('__requestCall')
            return None

        return response

    @sleep_and_retry
    @limits(calls=150, period=60)
    def __requestCallLimited(self, requestArgs):
        return self.__requestCall(requestArgs)

    def __testValue(self):
        requestArgs = {
            'url': 'https://query2.finance.yahoo.com/v8/finance/chart/BBD',
            'params': {
                'range': '5y',
                'interval': '1d',
                'events': 'div,splits,capitalGains',
            },
            'timeout': 30,
        }
        log.debug('**** run test ****')
        response = self.__requestCallLimited(requestArgs)
        if response != None:
            status_code = response.status_code
            if response.status_code == 200 and response.headers.get('content-type').startswith('application/json'):
                return len(response.json()['chart']['result'][0]['events']['dividends'])
        log.debug('test did not return valid value')
        return None
    
    def __multiRequest(self, requestArgsList, blockSize=50, limited=True):
        data = [None]*len(requestArgsList)
        retryReqArgsIndices = range(len(requestArgsList))
        sleepTime = 60
        # check test value to make sure data is consistent
        testValue = self.__testValue()
        if testValue < 65:
            log.error('Initial test failed: No data returned')
            return None
        newTestValue = testValue
        while len(retryReqArgsIndices) != 0:
            reqArgsIndices = retryReqArgsIndices
            retryReqArgsIndices = []
            lastBlockReqArgsIndices = []
            reqArgsIndicesCount = len(reqArgsIndices)
            rangeCount = reqArgsIndicesCount / blockSize
            for x in range(int(rangeCount) + ((rangeCount) > int(rangeCount))):
                blockReqArgsIndices = reqArgsIndices[x*blockSize:(x+1)*blockSize]
                sleepTotal = 0
                while newTestValue < testValue:
                    log.debug('Test Failed: wait %s seconds and retry' % sleepTime)
                    sleepTotal += sleepTime
                    sleep(sleepTime)
                    newTestValue = self.__testValue()
                if sleepTotal > 0:
                    log.debug('Test OK: Continued after %s seconds total wait' % sleepTotal)
                    # Turn last blocks data back to None since they might be compromised and retry them later
                    for noneReqArgsIndex in lastBlockReqArgsIndices:
                        retryReqArgsIndices.append(noneReqArgsIndex)
                        data[noneReqArgsIndex] = None
                lastBlockReqArgsIndices = []
                statusCodes = {}
                log.debug('Still %s requests to do ...' % reqArgsIndicesCount)
                for reqArgsIndex in blockReqArgsIndices:
                    if limited:
                        response = self.__requestCallLimited(requestArgsList[reqArgsIndex])
                    else:
                        response = self.__requestCall(requestArgsList[reqArgsIndex])
                    reqArgsIndicesCount -= 1
                    if not response.status_code in statusCodes:
                        statusCodes[response.status_code] = 0
                    statusCodes[response.status_code] += 1
                    if response.status_code == 200 and response.headers.get('content-type').startswith('application/json'):
                        data[reqArgsIndex] = response.json()
                    lastBlockReqArgsIndices.append(reqArgsIndex)
                for statusCode, scCount in statusCodes.items():
                    log.debug('got %s requests with status code: %s: %s' % (scCount, statusCode, config.STATUS_CODES[statusCode]['short']))
                # check test value after each block to make sure data is consistent
                newTestValue = self.__testValue()
            if len(retryReqArgsIndices) > 0:
                log.debug('Retrying %s more requests that did not pass the test ...' % len(retryReqArgsIndices))
        return data

    def __initRequest(self):
        yconfig = storage.get('config/yahoo')
        configRefresh = True
        if yconfig != None:
            # refresh cookie and crumb one month before it expires
            configRefresh = (datetime.now()+timedelta(days=30)).timestamp() > yconfig['cookie'].expires
        if configRefresh:
            req = Request(headers={'User-Agent': config.YAHOO_USER_AGENT})
            
            # get authorization cookie
            requestArgs = {
                'url': 'https://fc.yahoo.com',
                'timeout': 30,
                'proxies': None,
                'allow_redirects': True,
            }
            result = req.get(**requestArgs)
            cookie = list(result.cookies)
            if len(cookie) == 0:
                self.__session = None
            cookie = cookie[0]

            # get authorization crumb
            requestArgs['url'] = 'https://query1.finance.yahoo.com/v1/test/getcrumb'
            result = req.get(**requestArgs)
            crumb = result.text
             
            # create config variable and save it
            yconfig = {'cookie': cookie, 'crumb': crumb}
            storage.save('config/yahoo', yconfig)

        # create session with auth cookie
        cookies = {yconfig['cookie'].name: yconfig['cookie'].value}
        params = {'crumb': yconfig['crumb']}
        headers = {'User-Agent': config.YAHOO_USER_AGENT}
        # self.__request = Request(cookies=cookies, verbose=True, verboseContent=True,verboseOpenHTML=True)
        self.__request = Request(params=params, cookies=cookies, headers=headers)

    def __init__(self):
        self.__initRequest()
    
    def getQuoteSummaryModules(self):
        return config.YAHOO_QUOTE_SUMMARY_MODULES

    def getQuoteSummary(self, symbols, modules):
        log.info('Running getQuoteSummary on %s symbols' % len(symbols))
        modules = list(set(modules).intersection(config.YAHOO_QUOTE_SUMMARY_MODULES))
        if len(modules) == 0:
            log.error('Yahoo.getQuoteSummary: No valid modules selected. Use Yahoo.getQuoteSummaryModules for valid ones.')
            return {}
        modules = ','.join(modules)
        requestArgsList = []
        for symbol in symbols:
                    requestArgs = {
                        'url': 'https://query2.finance.yahoo.com/v10/finance/quoteSummary/'+symbol.upper(),
                        'params': {
                            'modules': modules,
                            'corsDomain': 'finance.yahoo.com',
                            'formatted': 'false',
                        },
                        'timeout': 30,
                    }
                    requestArgsList.append(requestArgs)
        responseDataList = self.__multiRequest(requestArgsList, blockSize=100)

        # create user data
        data = {}
        if responseDataList == None: return data
        index = 0
        for symbol in symbols:
            symbolData = responseDataList[index]
            index += 1
            if symbolData == None:
                continue
            symbolData = symbolData['quoteSummary']
            if symbolData['result'] == None: continue
            symbolData = symbolData['result'][0]
            data[symbol] = symbolData
            data[symbol]['timestamp'] = int(datetime.now().timestamp())
        
        return data

    def getChartsTimePeriods():
        return config.YAHOO_TIME_PERIODS

    def getCharts(self,symbols, range, interval):
        log.info('Running getCharts with range %s on intervals of %s with %s symbols' % (range, interval, len(symbols)))
        requestArgsList = []
        for symbol in symbols:
                    requestArgs = {
                        'url': 'https://query2.finance.yahoo.com/v8/finance/chart/'+symbol.upper(),
                        'params': {
                            'range': range,
                            'interval': interval,
                            'events': 'div,splits,capitalGains',
                        },
                        'timeout': 30,
                    }
                    requestArgsList.append(requestArgs)
        responseDataList = self.__multiRequest(requestArgsList, blockSize=50)
        
        # create user data
        data = {}
        if responseDataList == None: return data
        indexSymbol = 0
        for symbol in symbols:
            symbolData = responseDataList[indexSymbol]
            indexSymbol += 1
            if symbolData == None:
                continue
            symbolData = symbolData['chart']
            if symbolData['result'] == None: continue
            symbolData = symbolData['result'][0]
            data[symbol] = {}
            data[symbol]['timestamp'] = int(datetime.now().timestamp())
            data[symbol]['meta'] = symbolData.pop('meta')
            if 'timestamp' in symbolData:
                timestamps = symbolData.pop('timestamp')
                if 'indicators' in symbolData:
                    indicators = symbolData.pop('indicators')
                    data[symbol]['indicators'] = {}
                    for indicator, indicatorDataList in indicators.items():
                        data[symbol]['indicators'][indicator] = {}
                        indexTimestamp = 0
                        for timestamp in timestamps:
                            data[symbol]['indicators'][indicator][timestamp] = {}
                            for indicatorData in indicatorDataList:
                                for element, elementData in indicatorData.items():
                                    data[symbol]['indicators'][indicator][timestamp][element] = elementData[indexTimestamp]
                            indexTimestamp += 1
            if 'events' in symbolData:
                events = symbolData.pop('events')
                data[symbol]['events'] = {}
                for event, eventData in events.items():
                    data[symbol]['events'][event] = {}
                    for key, eventEntry in eventData.items():
                        data[symbol]['events'][event][eventEntry['date']] = {}
                        for element, value in eventEntry.items():
                            if element == 'date': continue
                            data[symbol]['events'][event][eventEntry['date']][element] = value

        return data
    def getFundamentalTypesFinancials(self):
        return config.YAHOO_FUNDAMENTALS_KEYS['financials']
    
    def getFundamentalTypesBalanceSheet(self):
        return config.YAHOO_FUNDAMENTALS_KEYS['balance-sheet']
    
    def getFundamentalTypesCashFlow(self):
        return config.YAHOO_FUNDAMENTALS_KEYS['cash-flow']
    
    def getFundamentals(self,symbols, fundamentalTypes, periodTypes):
        log.info('Running getFundamentals on %s symbols' % len(symbols))
        allFundamentalTypes = set(
            config.YAHOO_FUNDAMENTALS_KEYS['financials']).union(set(
                config.YAHOO_FUNDAMENTALS_KEYS['balance-sheet'])).union(set(
                    config.YAHOO_FUNDAMENTALS_KEYS['cash-flow']))
        fundamentalTypes = list(set(fundamentalTypes).intersection(allFundamentalTypes))
        periodTypes = list(set(periodTypes).intersection(set(config.YAHOO_FUNDAMENTALS_PERIODTYPES)))
        if len(fundamentalTypes) == 0:
            log.error('getFundamentals: no valid fundamental types given')
            return {}
        if len(periodTypes) == 0:
            log.error('getFundamentals: no valid period types given')
            return {}
        types = []
        for periodType in periodTypes:
            for fundamentalType in fundamentalTypes:
                types.append(periodType+fundamentalType)
        types = ','.join(types)

        (datetime.now()-timedelta(days=365*10)).timestamp()
        now = datetime.now()
        period1 = int(datetime(year=now.year-10, month=now.month, day=now.day).timestamp())
        period2 = int(now.timestamp())

        requestArgsList = []
        for symbol in symbols:
                    requestArgs = {
                        # 'url': 'https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/'+symbol.upper(),
                        'url': 'https://query2.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/'+symbol.upper(),
                        'params': {
                            'type': types,
                            'period1': period1,
                            'period2': period2,
                        },
                        'timeout': 30,
                    }
                    requestArgsList.append(requestArgs)
        
        responseDataList = self.__multiRequest(requestArgsList, blockSize=50)
        
        # create user data
        data = {}
        if responseDataList == None: return data
        index = 0
        for symbol in symbols:
            symbolData = responseDataList[index]
            index += 1
            if symbolData == None:
                continue
            symbolData = symbolData['timeseries']
            if symbolData['error'] != None:
                log.error('Error: %s' % symbolData['error'])
            if symbolData['result'] == None: continue
            for symbolData in symbolData['result']:
                if not 'timestamp' in symbolData: continue
                if not symbol in data:
                    data[symbol] = {'timestamp': int(datetime.now().timestamp()), 'fundamentals': {}}
                fundamentalsData = data[symbol]['fundamentals']
                for type in symbolData['meta']['type']:
                    fundamentalsData[type] = {}
                    index = 0
                    for timestamp in symbolData['timestamp']:
                        fundamentalsData[type][timestamp] = symbolData[type][index]
                        index += 1
        return data
    
    def search(self, symbol):
        requestArgs = {
            'url': 'https://query2.finance.yahoo.com/v1/finance/search',
            'params': {
                'q': symbol.upper(),
                'corsDomain': 'finance.yahoo.com',
                # 'formatted': 'false',
            },
            }
        result = self.__request.get(**requestArgs)
        data = {}
        data['status_code'] = result.status_code
        contentType = result.headers.get('content-type')
        if contentType != None:
            if contentType.startswith('application/json'):
                data['data'] = result.json()
            else:
                data['data'] = result.text
        return data
            
