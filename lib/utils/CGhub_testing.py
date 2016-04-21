import unittest
from ..cli import icgc_download_client
from argparse import Namespace
import os


class TestCGHubMethods(unittest.TestCase):

    def test_CGHub(self):
        args = Namespace(config='/Users/GavinWilson/git/icgc-download-client/config_dev.yaml',
                         file='a337c425-4314-40c6-a40a-a444781bd1b7', manifest=None,
                         output='/Users/GavinWilson/git/icgc-download-client/mnt/downloads', repo='cghub')
        icgc_download_client.call_client(args)
        file_info = os.stat('/Users/GavinWilson/git/icgc-download-client/mnt/downloads/' +
                            'a337c425-4314-40c6-a40a-a444781bd1b7/G28034.MDA-MB-361.1.bam')
        self.assertAlmostEqual(file_info.st_size, 5159984257, places=4)

    def test_CGHub_double(self):
        args = Namespace(config='/Users/GavinWilson/git/icgc-download-client/config_dev.yaml',
                         file='a452b625-74f6-40b5-90f8-7fe6f32b89bd a105a6ec-7cc3-4c3b-a99f-af29de8a7caa',
                         manifest=None, output='/Users/GavinWilson/git/icgc-download-client/mnt/downloads',
                         repo='collab')
        icgc_download_client.call_client(args)
        self.assertTrue(os.path.isfile('/Users/GavinWilson/git/icgc-download-client/mnt/downloads/' +
                                       'a105a6ec-7cc3-4c3b-a99f-af29de8a7caa/C836.BICR_18.2.bam') and
                        os.path.isfile('/Users/GavinWilson/git/icgc-download-client/mnt/downloads/' +
                                       'a452b625-74f6-40b5-90f8-7fe6f32b89bd/C836.PEER.1.bam'))

def test_CGHub_manifest(self):
    args = Namespace(config='/Users/GavinWilson/git/icgc-download-client/config_dev.yaml',
                     file=None, manifest='/Users/GavinWilson/git/icgc-download-client/lib/utils/manifest.xml',
                     output='/Users/GavinWilson/git/icgc-download-client/mnt/downloads', repo='collab')
    icgc_download_client.call_client(args)
    file_info = os.stat('/Users/GavinWilson/git/icgc-download-client/mnt/downloads/' +
                        'a337c425-4314-40c6-a40a-a444781bd1b7/G28034.MDA-MB-361.1.bam')
    self.assertAlmostEqual(file_info.st_size, 5159984257, places=4)

if __name__ == '__main__':
    unittest.main()
