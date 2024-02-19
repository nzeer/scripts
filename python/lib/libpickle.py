import pickle

GLOBAL_CONFIG = { 
    'dbfile': 'examplePickle',
}
 
def store_data(pickle_file: str, db: dict = {})-> bool:
    is_good_write = False
    # Its important to use binary mode
    with open(pickle_file, 'ab') as db_file:
        # source, destination
        pickle.dump(db, db_file)
        is_good_write = True
    return is_good_write

def load_data(pickle_file:str)-> bool:
    is_good_read = False    
    # for reading also binary mode is important
    with open(pickle_file, 'rb') as db_file:
        db = pickle.load(db_file)
        for keys in db:
            print('\t\t', keys, '=>', db[keys])
        is_good_read = True
    return is_good_read 

if __name__ == '__main__':
    # initializing data to be stored in db
    Omkar = {'key' : 'Omkar', 'name' : 'Omkar Pathak',
    'age' : 21, 'pay' : 40000}
    Jagdish = {'key' : 'Jagdish', 'name' : 'Jagdish Pathak',
    'age' : 50, 'pay' : 50000}
 
    # database
    db = {}
    db['Omkar'] = Omkar
    db['Jagdish'] = Jagdish
    
    if store_data(GLOBAL_CONFIG['dbfile'], db):
        print('Data stored successfully\n')
    if load_data(GLOBAL_CONFIG['dbfile']):
        print('\nData loaded successfully')