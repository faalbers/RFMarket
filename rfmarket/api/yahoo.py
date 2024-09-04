import config, sys
from rfmarket.api.request import Request
from datetime import datetime, timedelta
from rfmarket.tools import storage
from pprint import pp
from ratelimit import limits, sleep_and_retry
from time import sleep


# Financial Modeling Prep API wrapper

# consts
class Yahoo():
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
        return config.YAHOO__QUOTE_SUMMARY_MODULES
    
    def __getQuoteSummary(self, symbol, modules):
        requestArgs = {
            'url': config.YAHOO_URL_MAIN+'v10/finance/quoteSummary/'+symbol.upper(),
            'params': {
                'modules': modules,
                'corsDomain': 'finance.yahoo.com',
                'formatted': 'false',
            },
            'timeout': 30,
            'proxies': None,
            }
        result = self.__request.get(**requestArgs)
        if result.status_code == 200:
            # all OK
            if result.headers.get('content-type').startswith('application/json'):
                return True, result.json()['quoteSummary']
        elif result.status_code == 404:
            # not found
            return True, result.json()['quoteSummary']
        elif result.status_code == 500:
            # server error
            return True, {'error': {'code': 'Server error: status code 500'}}
        
        print('Error: status code: %s' % result.status_code)
        self.__request.printResponse(verbose=True)
        return False , [result.status_code, result]

    def getQuoteSummary(self, symbols, modules, verbose=False):
        modules = list(set(modules).intersection(config.YAHOO__QUOTE_SUMMARY_MODULES))
        if len(modules) == 0:
            print('Yahoo.getQuoteSummary: Error: No valid modules selected. Use Yahoo.getQuoteSummaryModules for valid ones.')
            return None
        modules = ','.join(modules)
        if isinstance(symbols, str):
            symbols = [symbols]
        elif not isinstance(symbols, list):
            print('Yahoo.getQuoteSummary: Error: Symbol(s) parameter of wrong type.')
            return None
        data = {}
        start = datetime.now()
        count = 0
        for symbol in symbols:
            symbol = symbol.upper()
            data[symbol] = {}
            if verbose: print('quoteSummary \t%s: %s' % (count, symbol))
            success, result = self.__getQuoteSummary(symbol, modules)
            count += 1
            if success:
                if 'error' in result and result['error'] != None:
                    print('Error: %s' % result['error']['code'])
                    continue
                elif result['result'] == None:
                    print('Error: result is None')
                    continue
                resultData = result['result'][0]
                resultData['timestamp'] = int(datetime.now().timestamp())
                data[symbol] = resultData
            else:
                print(symbol)
                print('something went wrong')
                print('status code: %s' % result[0])
                result = result[1]
                if result.headers.get('content-type').startswith('application/json'):
                    try:
                        result = result.json()
                        pp(result)
                    except:
                        print('It sais json type , but I crashed. Trying text')
                        print(result.text)
                else:
                    print(result.text)
                print('exec time: %s for %s symbols' % (datetime.now()-start, count))
                return {}
        print('exec time: %s for %s symbols' % (datetime.now()-start, count))
        return data

    def __testValue(self):
        requestArgs = {
            'url': config.YAHOO_URL_MAIN+'v8/finance/chart/BBD',
            'params': {
                'range': '5y',
                'interval': '1d',
                'events': 'div,splits,capitalGains',
            },
            'timeout': 30,
        }
        try:
            print('**** run test ****')
            response = self.__request.get(**requestArgs)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('%s: %s' % (exc_type, exc_value))
            return None
        status_code = response.status_code
        if response.status_code == 200 and response.headers.get('content-type').startswith('application/json'):
            return len(response.json()['chart']['result'][0]['events']['dividends'])
        else:
            print('test did not return valid value')
            return None

    @sleep_and_retry
    @limits(calls=150, period=60)
    def __requestCall(self, requestArgs):
        try:
            response = self.__request.get(**requestArgs)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('Exception: %s: %s' % (exc_type, exc_value))
            return None

        return response
    
    def getTestValue(self):
        return self.__testValue()
    
    def getCharts5y(self, symbols):
        data = {}
        results = set()
        blockSize = 50
        testValue = self.__testValue()
        sleepTime = 60
        if testValue > 65:
            print('Test Failed: Initial test failed')
            return data
        symbolCount = len(symbols)
        rangeCount = symbolCount / blockSize
        lastBlockSymbols = []
        for x in range(int(rangeCount) + ((rangeCount) > int(rangeCount))):
            blockSymbols = symbols[x*blockSize:(x+1)*blockSize]
            newTestValue = self.__testValue()
            sleepTotal = 0
            while newTestValue < testValue:
                print('Test Failed: wait %s seconds and retry' % sleepTime)
                sleep(sleepTime)
                sleepTotal += sleepTime
                newTestValue = self.__testValue()
            if sleepTotal > 0:
                print('Continued after %s seconds wait' % sleepTotal)
            lastBlockSymbols = []
            for symbol in blockSymbols:
                symbol = symbol.upper()
                requestArgs = {
                    'url': config.YAHOO_URL_MAIN+'v8/finance/chart/'+symbol,
                    'params': {
                        'range': '5y',
                        'interval': '1d',
                        'events': 'div,splits,capitalGains',
                    },
                    'timeout': 30,
                }
                response = self.__requestCall(requestArgs)
                symbolCount -= 1
                if response == None:
                    continue
                status_code = response.status_code
                info = '%s: %s: %s' % (status_code, config.STATUS_CODES[status_code]['short'], response.headers.get('content-type'))
                print('%s: %s -> %s' % (symbol, info, symbolCount))
                results.add(info)
                if response.status_code == 200 and response.headers.get('content-type').startswith('application/json'):
                    responseData = response.json()['chart']
                    if responseData['result'] == None:
                        print('**** NO DATA ****')
                        continue
                    data[symbol] = {}
                    responseData = responseData['result'][0]
                    if not 'events' in responseData: continue
                    events = responseData['events']
                    if not 'dividends' in events: continue
                    data[symbol]['dividends'] = {}
                    lastBlockSymbols.append(symbol)
                    for timestamp, divData in events['dividends'].items():
                        data[symbol]['dividends'][divData['date']] = divData['amount']
                    
                    # lists
                    # timestamps = responseData['timestamp']
                    # high = responseData['indicators']['quote'][0]['high']
                    # volume = responseData['indicators']['quote'][0]['volume']
                    # low = responseData['indicators']['quote'][0]['low']
                    # close = responseData['indicators']['quote'][0]['close']
                    # open = responseData['indicators']['quote'][0]['open']
                    # adjclose = responseData['indicators']['adjclose'][0]['adjclose']
                    # print(len(timestamps))
                    # print(len(high))
                    # print(len(volume))
                    # print(len(low))
                    # print(len(close))
                    # print(len(open))
                    # print(len(adjclose))

        pp(results)
        return data


    @sleep_and_retry
    @limits(calls=150, period=60)
    def __testLimitRate(self, symbol):
        requestArgs = {
            'url': config.YAHOO_URL_MAIN+'v8/finance/chart/'+symbol.upper(),
            'params': {
                'range': '5y',
                'interval': '1d',
                'events': 'div,splits,capitalGains',
            },
            'timeout': 30,
        }
        try:
            response = self.__request.get(**requestArgs)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('%s: %s' % (exc_type, exc_value))
            return None

        return response

    def testLimitRate(self,symbols):
        data = {}
        results = set()
        count = 0
        blockSize = 50
        testValue = 0

        response = self.__testLimitRate('BBD')
        count += 1
        status_code = response.status_code
        info = '%s: %s: %s' % (status_code, config.STATUS_CODES[status_code]['short'], response.headers.get('content-type'))
        print('%s: %s' % ('BBDFRANKA', info))
        if response.status_code == 200 and response.headers.get('content-type').startswith('application/json'):
            responseData = response.json()
            data['BBDFRANKA'] = responseData
            testValue = len(responseData['chart']['result'][0]['events']['dividends'])
        results.add(info)
        
        symbolCount = len(symbols)
        rangeCount = symbolCount / blockSize
        for x in range(int(rangeCount) + ((rangeCount) > int(rangeCount))):
            blockSymbols = symbols[x*blockSize:(x+1)*blockSize]
            if self.__testValue() < testValue:
                print('**** test failed ****')
                break
            count += 1
            for symbol in blockSymbols:
                symbol = symbol.upper()
                response = self.__testLimitRate(symbol)
                count += 1
                if response == None:
                    continue
                status_code = response.status_code
                info = '%s: %s: %s' % (status_code, config.STATUS_CODES[status_code]['short'], response.headers.get('content-type'))
                print('%s: %s -> %s' % (symbol, info, count))
                if response.status_code == 200 and response.headers.get('content-type').startswith('application/json'):
                    data[symbol] = response.json()
                results.add(info)

        response = self.__testLimitRate('BBD')
        count += 1
        status_code = response.status_code
        info = '%s: %s: %s' % (status_code, config.STATUS_CODES[status_code]['short'], response.headers.get('content-type'))
        print('%s: %s' % ('BBDFRANKB', info))
        if response.status_code == 200 and response.headers.get('content-type').startswith('application/json'):
            data['BBDFRANKB'] = response.json()
        results.add(info)
        
        print('')
        pp(results)

        return data


    def search(self, symbol):
        requestArgs = {
            'url': config.YAHOO_URL_MAIN+'v1/finance/search',
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
            
