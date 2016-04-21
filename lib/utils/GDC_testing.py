import unittest
from ..cli import icgc_download_client
from argparse import Namespace
import os


class TestGDCMethods(unittest.TestCase):

    def test_gdc(self):
        args = Namespace(config='/Users/GavinWilson/git/icgc-download-client/config_dev.yaml',
                         file='f483ad78-b092-4d10-9afb-eccacec9d9dc', manifest=None,
                         output='/Users/GavinWilson/git/icgc-download-client/mnt/downloads', repo='gdc')
        icgc_download_client.call_client(args)
        file_info = os.stat('/Users/GavinWilson/git/icgc-download-client/mnt/downloads/' +
                            'f483ad78-b092-4d10-9afb-eccacec9d9dc/TCGA-CH-5763-01A-11D-1572-02_AC1JWAACXX' +
                            '---TCGA-CH-5763-11A-01D-1572-02_AC1JWAACXX---Segment.tsv')
        self.assertTrue(os.path.isfile('/Users/GavinWilson/git/icgc-download-client/mnt/downloads' +
                                       'f483ad78-b092-4d10-9afb-eccacec9d9dc/annotations.txt') and
                        file_info.st_size == 1000)

    def test_gdc_double(self):
        args = Namespace(config='/Users/GavinWilson/git/icgc-download-client/config_dev.yaml',
                         file='2c759eb8-7ee0-43f5-a008-de4317ab8c70 a6b2f1ff-5c71-493c-b65d-e344ed29b7bb',
                         manifest=None, output='/Users/GavinWilson/git/icgc-download-client/mnt/downloads', repo='ega')
        icgc_download_client.call_client(args)
        self.assertTrue(os.path.isfile('/Users/GavinWilson/git/icgc-download-client/mnt/downloads' +
                                       '48016dd8-6033-4d73-8c85-f6eb1896e465/annotations.txt') and
                        os.path.isfile('/Users/GavinWilson/git/icgc-download-client/mnt/downloads' +
                                       '48016dd8-6033-4d73-8c85-f6eb1896e465/annotations.txt'))

def test_GDC_manifest(self):
    args = Namespace(config='/Users/GavinWilson/git/icgc-download-client/config_dev.yaml',
                     file=None, manifest='/Users/GavinWilson/git/icgc-download-client/lib/utils' +
                                         'gdc_manifest_1677e1a1e443d44e301239c10c7dc5d29c7f2658.txt',
                     output='/Users/GavinWilson/git/icgc-download-client/mnt/downloads', repo='collab')
    icgc_download_client.call_client(args)
    file_info = os.stat('/Users/GavinWilson/git/icgc-download-client/mnt/downloads/' +
                        'a337c425-4314-40c6-a40a-a444781bd1b7/G28034.MDA-MB-361.1.bam')
    self.assertAlmostEqual(file_info.st_size, 5159984257, places=4)


if __name__ == '__main__':
    unittest.main()
