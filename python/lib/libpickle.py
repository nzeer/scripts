import pickle
import os

GLOBAL_CONFIG = { 
    'pickle_file': './.cache/._pickle',
    'pickle_obj_db': {},
}

def get_pickle_config() -> dict:
    return GLOBAL_CONFIG

def set_pickle_config(db_file: str, *, db: dict) -> None:
    GLOBAL_CONFIG['pickle_file'] = db_file
    GLOBAL_CONFIG['pickle_obj_db'] = db
    
def set_pickle_file(db_file: str) -> None:
    GLOBAL_CONFIG['pickle_file'] = db_file

def get_pickle_file() -> str:
    return GLOBAL_CONFIG['pickle_file']
    
def set_pickle_obj_db(db: dict) -> None:
    GLOBAL_CONFIG['pickle_obj_db'] = db
    
def get_pickle_obj_db() -> dict:
    return GLOBAL_CONFIG['pickle_obj_db']

def store_data(pickle_file: str, db: dict = {})-> bool:
    is_good_write = False
    
    for keys in db:
            print('\t\t', keys, '=>', db[keys])
    
    pickle_file_directory = os.path.dirname(pickle_file)
    if not os.path.exists(pickle_file_directory):
        os.makedirs(pickle_file_directory)
    
    # Its important to use binary mode
    with open(pickle_file, 'ab') as db_file:
        # source, destination
        pickle.dump(db, db_file)
        is_good_write = True
    return is_good_write

def load_data(pickle_file: str)-> bool:
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
    db = get_pickle_obj_db()
    db['Omkar'] = Omkar
    db['Jagdish'] = Jagdish
    
    pickle_file = get_pickle_file()
    
    print("\nUsing picklefile: ", pickle_file, "\n")
    if store_data(pickle_file, get_pickle_obj_db()):
        print('\nData stored successfully\n')
    
    print("\nUsing picklefile: ", pickle_file, "\n")
    if load_data(pickle_file):
        print('\nData loaded successfully')