import pandas as pd
from pprint import pp
from datetime import datetime

class HTML():
    def __getHTML(self, name, keyName, url, index=0):
        data = pd.read_html(url)
        if len(data) > 0:
            dataDict = data[index].T.to_dict()
            self.__data[name] = {}
            self.__data[name]['timeStamp'] = int(datetime.now().timestamp())
            self.__data[name]['data'] = {}
            for index, data in dataDict.items():
                key = data.pop(keyName)
                if not key in self.__data[name]['data']:
                    self.__data[name]['data'][key] = []
                self.__data[name]['data'][key].append(data)
        else:
            print('scrape.HTML: URL could not be read: %s' % url)
            self.__data[name] = None

    def __init__(self):
        self.__data = {}
        self.__getHTML('currency', 'Code', 'https://www.iban.com/currency-codes')
    
    def getData(self):
        return self.__data

