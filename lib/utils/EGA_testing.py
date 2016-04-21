import unittest
from ..cli import icgc_download_client
from argparse import Namespace
import os


class TestEGAMethods(unittest.TestCase):

    def test_ega(self):
        args = Namespace(config='/Users/GavinWilson/git/icgc-download-client/config_dev.yaml', file='EGAD00001001847',
                       manifest=None, output='/Users/GavinWilson/git/icgc-download-client/mnt/downloads', repo='ega')
        icgc_download_client.call_client(args)
        self.assertTrue(os.path.isfile('/Users/GavinWilson/git/icgc-download-client/mnt/downloads' +
                                       '_EGAR00001385154_4Cseq_single-end_HD-MB03_TGFBR1_sequence.fastq.gz') and
                        os.path.isfile('/Users/GavinWilson/git/icgc-download-client/mnt/downloads' +
                                       '_EGAR00001385154_4Cseq_single-end_HD-MB03__sequence.fastq.gz'))

    def test_ega_file(self):
        args = Namespace(config='/Users/GavinWilson/git/icgc-download-client/config_dev.yaml', file='EGAF00000112559',
                         manifest=None, output='/Users/GavinWilson/git/icgc-download-client/mnt/downloads', repo='ega')
        icgc_download_client.call_client(args)
        self.assertTrue(os.path.isfile('/Users/GavinWilson/git/icgc-download-client/mnt/downloads' +
                                       '_methylationCEL_CLL-174.CEL'))

if __name__ == '__main__':
    unittest.main()
