from argparse import Namespace
import unittest
import os
import lib.cli.icgc_download_client
from lib.cli import icgc_download_client


class TestEGAMethods():

    def test_ega(self, config, data_dir):
        args = Namespace(config=config, file=['EGAD00001001847'], manifest=None, output=data_dir, repo='ega')
        # icgc_download_client.call_client(args)
        assert (os.path.isfile(data_dir +
                               '_EGAR00001385154_4Cseq_single-end_HD-MB03_TGFBR1_sequence.fastq.gz') and
                os.path.isfile(data_dir + '_EGAR00001385153_4Cseq_single-end_HD-MB03_SMAD9_sequence.fastq.gz'))

    def test_ega_file(self, config, data_dir):
        args = Namespace(config=config, file=['EGAF00000112559'], manifest=None, output=data_dir, repo='ega')
        # icgc_download_client.call_client(args)
        assert (os.path.isfile(data_dir + '_methylationCEL_CLL-174.CEL'))


