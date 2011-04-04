'''Simple data loader module.

Loads data files from the "data" directory shipped with a game.
'''

import os


data_py = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.normpath(os.path.join(data_py, '..', 'data'))


def filepath(filename, subdir=None):
    '''Determine the path to a file in the data directory.
    '''
    if subdir:
        return os.path.join(data_dir, subdir, filename)
    else:
        return os.path.join(data_dir, filename)


def load(filename, mode='rb'):
    '''Open a file in the data directory.

    "mode" is passed as the second arg to open().
    '''
    return open(os.path.join(data_dir, filename), mode)
