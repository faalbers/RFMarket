import requests, config
from lxml import html
import json as js
from bs4 import BeautifulSoup as bs
from pprint import pp
from datetime import datetime 

class Request():
    def printResponse(self, verbose=None, verboseContent=None, verboseOpenHTML=None):
        if self.__response == None: return
        if verbose == None: verbose = self.__verbose
        if verboseContent == None: verboseContent = self.__verboseContent
        if verboseOpenHTML == None: verboseOpenHTML = self.__verboseOpenHTML
        if not verbose: return
        indent = ' '*2
        print('\n*** REQUEST ***')
        print('\nurl   : %s' % self.__response.request.url)
        print('path url: %s' % self.__response.request.path_url)
        print('method: %s' % self.__response.request.method)
        print('\nheaders:')
        for name, value in self.__response.request.headers.items():
            print('%s%s: %s' % (indent, name, value))
        cookieHeader = self.__response.request.headers.get('cookie')
        if cookieHeader != None:
            print('\ncookies:')
            cookies = {}
            for cookieElem in cookieHeader.split('; '):
                elems = cookieElem.split('=')
                cookies[elems[0]] = elems[1]
            pp(cookies)

        if verboseContent:
            contentType = self.__response.request.headers.get('content-type')
            if contentType != None:
                print('\ncontent:')
                contentElems = contentType.split(';')
                type = contentElems[0].strip()
                params = {}
                print('content type  : %s' % type)
                if len(contentElems) > 1:
                    for param in contentElems[1:]:
                        paramElems = param.strip().split('=')
                        params[paramElems[0]] = paramElems[1].strip()
                print('content params: %s\n' % params)
                if type == 'multipart/form-data':
                    print('body: bytes')
                    print(self.__response.request.body)
                elif type == 'application/x-www-form-urlencoded' or type == 'text/plain':
                    print('body: text')
                    print(self.__response.request.body)
                elif type == 'application/json':
                    print('body: binary json')
                    pp(js.loads(self.__response.request.body.decode('utf-8')))
                else:
                    print('unknow content type: %s' % type)
        print("-" * 20)
        
        mytest = 'https://financialmodelingprep.com/api/v3/stock/list?apikey=5fnCoFYnujpfmldsHKPRKeLHWQCKBFLK'
        print('\n*** RESPONSE ***')
        print('\nurl   : %s' % self.__response.url)
        print('\nurl   : %s' % mytest)
        print('status_code: %s: %s' % (self.__response.status_code, config.STATUS_CODES[self.__response.status_code]['short']))
        for name, value in self.__response.headers.items():
            print('%s%s: %s' % (indent, name, value))

        if len(self.__response.cookies):
            print('\ncookies:')
        for cookie in self.__response.cookies:
            print('%s%s:' % (indent, cookie.name))
            print('%svalue: %s' % (indent*2, cookie.value))
            if cookie.expires != None:
                print('%sexpires: %s' % (indent*2, datetime.fromtimestamp(cookie.expires)))
            if cookie.domain != None:
                print('%sdomain: %s' % (indent*2, cookie.domain))
            if cookie.path != None:
                print('%sspath: %s' % (indent*2, cookie.path))
            if cookie.secure != None:
                print('%ssecure: %s' % (indent*2, cookie.secure))
            if cookie.has_nonstandard_attr(('HttpOnly')):
                print('%sHttpOnly: True' % (indent*2))
            if cookie.has_nonstandard_attr(('SameSite')):
                print('%sSameSite: %s' % (indent*2, cookie.get_nonstandard_attr(('SameSite'))))
        
        if verboseContent:
            contentType = self.__response.headers.get('content-type')
            if contentType != None:
                print('\ncontent:')
                contentElems = contentType.split(';')
                type = contentElems[0]
                params = {}
                print('content type  : %s' % type)
                if len(contentElems) > 1:
                    for param in contentElems[1:]:
                        paramElems = param.strip().split('=')
                        params[paramElems[0]] = paramElems[1].strip()
                print('content params: %s\n' % params)
                if type == 'text/html':
                    if verboseOpenHTML:
                        html.open_in_browser(html.fromstring(self.__response.text))
                    else:
                        print(bs(self.__response.text, features='lxml').prettify())
                elif type == 'application/json':
                    pp(self.__response.json())
                elif type == 'text/plain':
                    print(self.__response.text)
                else:
                    print('unknow content type: %s' % type)
        
        print()
        print("-" * 20)
    
    def __init__(self, params={}, headers={}, cookies={}, verbose=False, verboseContent=False, verboseOpenHTML=False):
        self.__session = requests.Session()
        # add persisting cookies, params and headers
        self.__session.cookies.update(cookies)
        self.__session.params.update(params)
        self.__session.headers.update(headers)
        self.__response = None
        self.__verbose = verbose
        self.__verboseContent = verboseContent
        self.__verboseOpenHTML = verboseOpenHTML

    def get(self, url=None,
            params=None, headers=None, cookies=None, auth=None, proxies=None, timeout=None, allow_redirects=False,
            verbose=None, verboseContent=None, verboseOpenHTML=None):
        self.__response = self.__session.get(url, 
                                             params=params, headers=headers, cookies=cookies, auth=auth,
                                             proxies=proxies, timeout=timeout, allow_redirects=allow_redirects)
        self.printResponse(verbose, verboseContent, verboseOpenHTML)
        return self.__response

    def post(self, url,
            params=None, headers=None, cookies=None, auth=None,
            data=None, files=None, json=None,
            verbose=None, verboseContent=None, verboseOpenHTML=None):
        self.__response = self.__session.post(url, params=params, headers=headers, cookies=cookies, auth=auth,
                                              data=data, files=files, json=json,)
        self.printResponse(verbose, verboseContent, verboseOpenHTML)


