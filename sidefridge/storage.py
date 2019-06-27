import argparse
import json
import uuid
import os
from os import path

TMP_STORE = '/tmp/sidefridge_storage_path'


def get_storage_path():
    """ If no storage is setup it will get initialized """
    if not path.isfile(TMP_STORE):
        with open(TMP_STORE, 'w') as f:
            f.write(str(uuid.uuid4()))

    with open(TMP_STORE) as f:
        store_name = f.read()

    store_path = path.join('/tmp', store_name)

    # recreate empty file if missing
    if not path.isfile(store_path):
        with open(store_path, 'w') as f:
            f.write('{}')

    return store_path


def clear_storage():
    """ Remove all storage components """
    if not path.isfile(TMP_STORE):
        return

    with open(TMP_STORE) as f:
        store_name = f.read()

    store_path = path.join('/tmp', store_name)

    # removing files
    os.remove(store_path)
    os.remove(TMP_STORE)


def load_dict():
    """ Returns dictionary stored on disk """
    with open(get_storage_path(), 'r') as f:
        return json.load(f)


def store_dict(dict_data):
    """ Writes dictionary to disk """
    with open(get_storage_path(), 'w') as f:
        json.dump(dict_data, f)


def store_var():
    """ Stores the first argument as key and the second argument as value """
    parser = argparse.ArgumentParser(
        description='Utility to store values for usage between scripts'
    )
    parser.add_argument(
        'key', type=str,
        help='the key where to store the value'
    )
    parser.add_argument(
        'value', type=str,
        help='the value to be stored'
    )

    arguments = parser.parse_args()

    data_dict = load_dict()
    data_dict[arguments.key] = arguments.value
    store_dict(data_dict)


def load_var():
    """ Searches for the first argument to load """
    parser = argparse.ArgumentParser(
        description='Utility to load values for usage between scripts'
    )
    parser.add_argument(
        'key', type=str,
        help='the key where to store the value'
    )
    parser.add_argument(
        'default', nargs='?', type=str, default='',
        help='optional value if key is not found'
    )

    arguments = parser.parse_args()

    data_dict = load_dict()
    return data_dict.get(arguments.key, arguments.default)
