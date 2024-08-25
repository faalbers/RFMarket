import os, pickle

def get(name):
    fileName = name+'.pickle'
    if not os.path.exists(fileName):
        print('File not found: %s' % fileName)
        return None
    with open(fileName, 'rb') as f:
        data = pickle.load(f)
    f.close()
    return data

def save(name, data):
    fileName = name+'.pickle'
    with open(fileName, 'wb') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
    f.close()