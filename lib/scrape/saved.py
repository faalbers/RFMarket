import os
import pandas as pd
from pprint import pp

class Saved():
    def __getCSVB(self, name, keyName, fileName):
        filePath = 'data/saved/'+fileName+'.csv'
        if os.path.exists(filePath):
            self.__data[name] = {}
            self.__data[name]['timeStamp'] = int(os.path.getmtime(filePath))
            data = pd.read_csv(filePath)
            dataDict = data.T.to_dict()
            self.__data[name]['data'] = {}
            for index, data in dataDict.items():
                key = data.pop(keyName)
                self.__data[name]['data'][key] = data
        else:
            print('scrape.Saved: File does not exist: %s' % filePath)
            self.__data[name] = None

    def __getCSV(self, name, keyName, fileName):
        filePath = 'data/saved/'+fileName+'.csv'
        if os.path.exists(filePath):
            self.__data[name] = {}
            self.__data[name]['timeStamp'] = int(os.path.getmtime(filePath))
            data = pd.read_csv(filePath)
            dataDict = data.T.to_dict()
            self.__data[name]['data'] = {}
            for index, data in dataDict.items():
                key = data.pop(keyName)
                if not key in self.__data[name]['data']:
                    self.__data[name]['data'][key] = []
                self.__data[name]['data'][key].append(data)
        else:
            print('scrape.Saved: File does not exist: %s' % filePath)
            self.__data[name] = None

    def __init__(self):
        self.__data = {}
        self.__getCSVB('MIC', 'MIC', 'ISO10383_MIC')
        self.__getCSVB('country', 'Code', 'ISO3166-1')
    
    def getData(self):
        return self.__data

