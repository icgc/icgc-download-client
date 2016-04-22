import pytest


@pytest.fixture(scope="session")
def config():
    conf = '/Users/GavinWilson/git/icgc-download-client/config_dev.yaml'
    return conf


@pytest.fixture(scope="session")
def data_dir():
    dir = '/Users/GavinWilson/git/icgc-download-client/mnt/downloads/'
    return dir