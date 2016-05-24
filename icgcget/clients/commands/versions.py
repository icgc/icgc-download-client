import logging
from ..ega.ega_client import EgaDownloadClient
from ..gdc.gdc_client import GdcDownloadClient
from ..gnos.gnos_client import GnosDownloadClient
from ..icgc.storage_client import StorageClient


def versions(cghub_path, ega_access, ega_path, gdc_path, icgc_path, version_num):
    logger = logging.getLogger()
    gdc_client = GdcDownloadClient()
    ega_client = EgaDownloadClient()
    gt_client = GnosDownloadClient()
    icgc_client = StorageClient()
    gdc_client.version_check(gdc_path)
    ega_client.version_check(ega_path, ega_access)
    gt_client.version_check(cghub_path)
    icgc_client.version_check(icgc_path)
    logger.info("ICGC-Get Version: {}".format(version_num))
