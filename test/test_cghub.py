import unittest
from lib.cli import icgc_download_client
from argparse import Namespace
import os


class TestCGHubMethods(unittest.TestCase):

    def test_CGHub(self):
        args = Namespace(config=conf, file=['a337c425-4314-40c6-a40a-a444781bd1b7'], manifest=None, output=data_dir,
                         repo='cghub')
        icgc_download_client.call_client(args)
        file_info = os.stat(data_dir + 'a337c425-4314-40c6-a40a-a444781bd1b7/G28034.MDA-MB-361.1.bam')
        self.assertAlmostEqual(file_info.st_size, 5159984257, places=4)

    def test_CGHub_double(self):
        args = Namespace(config=conf,
                         file=['a452b625-74f6-40b5-90f8-7fe6f32b89bd a105a6ec-7cc3-4c3b-a99f-af29de8a7caa'],
                         manifest=None, output=data_dir,repo='cghub')
        icgc_download_client.call_client(args)
        self.assertTrue(os.path.isfile(data_dir + 'a105a6ec-7cc3-4c3b-a99f-af29de8a7caa/C836.BICR_18.2.bam') and
                        os.path.isfile(data_dir + 'a452b625-74f6-40b5-90f8-7fe6f32b89bd/C836.PEER.1.bam'))

    def test_GDC_manifest(self):
        args = Namespace(config=conf, file=None,
                         manifest=manifest_dir + 'gdc_manifest_1677e1a1e443d44e301239c10c7dc5d29c7f2658.txt',
                         output=data_dir, repo='cghub')
        icgc_download_client.call_client(args)

        self.assertTrue(os.path.isfile(data_dir +
                                       '48016dd8-6033-4d73-8c85-f6eb1896e465/14-3-3_beta-R-V_GBL11066140.txt') and
                        os.path.isfile(data_dir +
                                       '71014f3d-6c29-4977-a5fa-568cbcbf8787/14-3-3_beta-R-V_GBL1114584.tif') and
                        os.path.isfile(data_dir +
                                       'cf1f6b6b-d6d8-4b0b-9ace-a344e088875e/14-3-3_beta-R-V_GBL1114584.txt'))

if __name__ == '__main__':
    data_dir = '/Users/GavinWilson/git/icgc-download-client/mnt/downloads/'
    manifest_dir = '/Users/GavinWilson/git/icgc-download-client/lib/utils'
    conf = '/Users/GavinWilson/git/icgc-download-client/config_dev.yaml'
    unittest.main()
