import unittest
from ..cli import icgc_download_client
from argparse import Namespace
import os


class TestCGHubMethods(unittest.TestCase):

    def test_icgc(self):
        args = Namespace(config='/Users/GavinWilson/git/icgc-download-client/config_dev.yaml',
                         file='a5a6d87b-e599-528b-aea0-73f5084205d5', manifest=None,
                         output='/Users/GavinWilson/git/icgc-download-client/mnt/downloads', repo='collab')
        icgc_download_client.call_client(args)
        file_info = os.stat('/Users/GavinWilson/git/icgc-download-client/mnt/downloads/' +
                            'a337c425-4314-40c6-a40a-a444781bd1b7/G28034.MDA-MB-361.1.bam')
        self.assertAlmostEqual(file_info.st_size, 5159984257, places=4)

    def test_icgc_manifest(self):
        args = Namespace(config='/Users/GavinWilson/git/icgc-download-client/config_dev.yaml',
                         file=None, manifest='/Users/GavinWilson/git/icgc-download-client/lib/utils' +
                         'manifest.collaboratory.1461082640538.txt',
                         output='/Users/GavinWilson/git/icgc-download-client/mnt/downloads', repo='collab')
        icgc_download_client.call_client(args)
        file_info = os.stat('/Users/GavinWilson/git/icgc-download-client/mnt/downloads/' +
                            'a337c425-4314-40c6-a40a-a444781bd1b7/G28034.MDA-MB-361.1.bam')
        self.assertAlmostEqual(file_info.st_size, 5159984257, places=4)

if __name__ == '__main__':
    unittest.main()
