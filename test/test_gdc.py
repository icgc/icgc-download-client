import unittest
from lib.cli import icgc_download_client
from argparse import Namespace
import sys, os


class TestGDCMethods(unittest.TestCase):

    myPath = os.path.dirname(os.path.abspath())
    def test_gdc(self):
        args = Namespace(config=config, file=['f483ad78-b092-4d10-9afb-eccacec9d9dc'], manifest=None,output=data_dir,
                         repo='gdc')
        icgc_download_client.call_client(args)
        file_info = os.stat(data_dir +
                            'f483ad78-b092-4d10-9afb-eccacec9d9dc/TCGA-CH-5763-01A-11D-1572-02_AC1JWAACXX' +
                            '---TCGA-CH-5763-11A-01D-1572-02_AC1JWAACXX---Segment.tsv')
        self.assertTrue(os.path.isfile(data_dir + 'f483ad78-b092-4d10-9afb-eccacec9d9dc/annotations.txt') and
                        file_info.st_size == 1000)

    def test_gdc_double(self):
        args = Namespace(config=config,
                         file=['2c759eb8-7ee0-43f5-a008-de4317ab8c70 a6b2f1ff-5c71-493c-b65d-e344ed29b7bb'],
                         manifest=None, output=data_dir, repo='gdc')
        icgc_download_client.call_client(args)
        self.assertTrue(os.path.isfile(data_dir + '48016dd8-6033-4d73-8c85-f6eb1896e465/annotations.txt') and
                        os.path.isfile(data_dir + '48016dd8-6033-4d73-8c85-f6eb1896e465/annotations.txt'))

    def test_GDC_manifest(self):
        args = Namespace(config=config, file=None, manifest='/Users/GavinWilson/git/icgc-download-client/test/' +
                                                            'gdc_manifest_1677e1a1e443d44e301239c10c7dc5d29c7f2658.txt',
                         output=data_dir, repo='gdc')
        icgc_download_client.call_client(args)

        self.assertTrue(os.path.isfile(data_dir +
                                       '48016dd8-6033-4d73-8c85-f6eb1896e465/14-3-3_beta-R-V_GBL11066140.txt') and
                        os.path.isfile(data_dir +
                                       '71014f3d-6c29-4977-a5fa-568cbcbf8787/14-3-3_beta-R-V_GBL1114584.tif') and
                        os.path.isfile(data_dir +
                                       'cf1f6b6b-d6d8-4b0b-9ace-a344e088875e/14-3-3_beta-R-V_GBL1114584.txt'))


if __name__ == '__main__':
    config = '/Users/GavinWilson/git/icgc-download-client/config_dev.yaml'
    data_dir = '/Users/GavinWilson/git/icgc-download-client/mnt/downloads/'
    unittest.main()
