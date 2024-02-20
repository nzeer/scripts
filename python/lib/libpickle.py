import pickle
import os

GLOBAL_CONFIG = { 
    'pickle_file_path': './.cache/._pickle',
    'pickle_obj_db': {},
}

def get_pickle_config() -> dict:
    return GLOBAL_CONFIG

def set_pickle_config(pickle_file_path: str, *, pickle_obj_db: dict) -> None:
    set_pickle_file(pickle_file_path)
    set_pickle_obj_db(pickle_obj_db)
    
def set_pickle_file(pickle_file: str) -> None:
    get_pickle_config()['pickle_file_path'] = pickle_file

def get_pickle_file_path() -> str:
    return get_pickle_config()['pickle_file_path']
    
def set_pickle_obj_db(pickle_obj_db: dict) -> None:
    get_pickle_config()['pickle_obj_db'] = pickle_obj_db
    
def get_pickle_obj_db() -> dict:
    return get_pickle_config()['pickle_obj_db']

def get_pickle_obj_db_keys() -> list:
    return list(get_pickle_obj_db().keys())

def store_data(pickle_file_path: str, pickle_obj_db: dict = {})-> bool:
    is_good_write = False
    
    for keys in pickle_obj_db:
            print('\t\t', keys, '=>', pickle_obj_db[keys])
    
    pickle_file_directory = os.path.dirname(pickle_file_path)
    if not os.path.exists(pickle_file_directory):
        os.makedirs(pickle_file_directory)
    
    # Its important to use binary mode
    with open(pickle_file_path, 'ab') as db_file:
        # source, destination
        pickle.dump(pickle_obj_db, db_file)
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
    
    pickle_file_path = get_pickle_file_path()
    
    print("\nUsing picklefile: ", pickle_file_path, "\n")
    if store_data(pickle_file_path, get_pickle_obj_db()):
        print('\nData stored successfully\n')
    
    print("\nUsing picklefile: ", pickle_file_path, "\n")
    if load_data(pickle_file_path):
        print('\nData loaded successfully')