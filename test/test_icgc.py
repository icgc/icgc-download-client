import unittest
import pytest
from lib.cli import icgc_download_client
from argparse import Namespace
import os


class TestCGHubMethods(unittest.TestCase):

    def test_icgc(self):
        args = Namespace(config=conf_dir, file=['a5a6d87b-e599-528b-aea0-73f5084205d5'], manifest=None,output=data_dir,
                         repo='collab')
        icgc_download_client.call_client(args)
        file_info = os.stat(data_dir + 'a337c425-4314-40c6-a40a-a444781bd1b7/G28034.MDA-MB-361.1.bam')
        self.assertAlmostEqual(file_info.st_size, 5159984257, places=4)

    def test_icgc_manifest(self):
        args = Namespace(config=conf_dir, file=None, manifest=manifest_dir + 'manifest.collaboratory.1461082640538.txt',
                         output='/Users/GavinWilson/git/icgc-download-client/mnt/downloads', repo='collab')
        icgc_download_client.call_client(args)
        assert (os.path.isfile(data_dir + 'f37971bd-ec65-4840-8d4f-678692cee695.embl-delly_1-3-0-preFilter.20151106.' +
                               'germline.sv.vcf.gz/ec37ddf9-9ea4-5b8b-ac38-c9e415b302c4') and
                os.path.isfile(data_dir + 'f37971bd-ec65-4840-8d4f-678692cee695.embl-delly_1-3-0-preFilter' +
                               '.20151106.germline.sv.vcf.gz.tbi/6829a356-5204-5948-9505-506443ef4269') and
                os.path.isfile(data_dir + 'c9ad6b1c-baa0-45a7-b7c4-733728505b8a.broad-snowman.20151023' +
                               '.germline.sv.vcf.gz/6e6d420d-fb38-5958-b545-b6a36b52f82f') and
                os.path.isfile(data_dir + 'a78b5788-67ea-4275-931c-421bf76c5a4c.broad-snowman.20151107' +
                               '.germline.sv.vcf.gz/4862d12a-7c48-5adf-939b-be93303d9847') and
                os.path.isfile(data_dir + '6d3551d6-b5f4-4fd1-b8d7-8e5931096c19.broad-snowman.20151023.germline' +
                               '.sv.vcf.gz/965865a6-0b0c-5f83-b2f8-4b16e382b643'))

if __name__ == '__main__':
    data_dir = '/Users/GavinWilson/git/icgc-download-client/mnt/downloads/'
    conf_dir = '/Users/GavinWilson/git/icgc-download-client/config_dev.yaml'
    manifest_dir = '/Users/GavinWilson/git/icgc-download-client/lib/utils'
    unittest.main()
