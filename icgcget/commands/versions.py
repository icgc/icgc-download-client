import logging
from icgcget.clients.ega.ega_client import EgaDownloadClient
from icgcget.clients.gdc.gdc_client import GdcDownloadClient
from icgcget.clients.gnos.gnos_client import GnosDownloadClient
from icgcget.clients.icgc.storage_client import StorageClient
from icgcget.clients.pdc.pdc_client import PdcDownloadClient


def versions_command(cghub_path, ega_access, ega_path, gdc_path, icgc_path, pdc_path, version_num):
    logger = logging.getLogger()
    PdcDownloadClient().version_check(pdc_path)
    GdcDownloadClient().version_check(gdc_path)
    EgaDownloadClient().version_check(ega_path, ega_access)
    GnosDownloadClient().version_check(cghub_path)
    StorageClient().version_check(icgc_path)
    logger.info("ICGC-Get Version: {}".format(version_num))
