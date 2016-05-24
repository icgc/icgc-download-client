import logging

import click
import psutil

from command_utils import api_error_catch, filter_manifest_ids, check_access
from ..utils import calculate_size, convert_size
from .. import portal_client
from ..ega.ega_client import EgaDownloadClient
from ..gdc.gdc_client import GdcDownloadClient
from ..gnos.gnos_client import GnosDownloadClient
from ..icgc.storage_client import StorageClient

REPOS = ['collaboratory', 'aws-virginia', 'ega', 'gdc', 'cghub']


class Download:
    def __init__(self):
        self.logger = logging.getLogger("__log__")
        self.gdc_client = GdcDownloadClient()
        self.ega_client = EgaDownloadClient()
        self.gt_client = GnosDownloadClient()
        self.icgc_client = StorageClient()

    def download_manifest(self, repos, file_ids, manifest, output, yes_to_all, api_url):
        if manifest:
            if len(file_ids) > 1:
                self.logger.warning("For download from manifest files, multiple manifest id arguments is not supported")
                raise click.BadArgumentUsage("Multiple manifest files specified.")
            portal = portal_client.IcgcPortalClient()
            manifest_json = api_error_catch(self, portal.get_manifest_id, file_ids[0], api_url, repos)
        else:
            portal = portal_client.IcgcPortalClient()
            manifest_json = api_error_catch(self, portal.get_manifest, file_ids, api_url, repos)

        if not manifest_json["unique"] or len(manifest_json["entries"]) != 1:
            filter_manifest_ids(self, manifest_json)
        size, object_ids = calculate_size(manifest_json)

        self.size_check(size, yes_to_all, output)
        return object_ids

    def download(self, object_ids, output,
                 cghub_access, cghub_path, cghub_transport_parallel,
                 ega_access, ega_path, ega_transport_parallel, ega_udt,
                 gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
                 icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_parallel):
        if 'cghub' in object_ids and object_ids['cghub']:
            check_access(self, cghub_access, 'cghub')
            return_code = self.gt_client.download(object_ids['cghub'], cghub_access, cghub_path, output,
                                                  cghub_transport_parallel)
            self.check_code('Cghub', return_code)

        if 'aws-virginia' in object_ids and object_ids['aws-virginia']:
            check_access(self, icgc_access, 'icgc')
            return_code = self.icgc_client.download(object_ids['aws-virginia'], icgc_access, icgc_path, output,
                                                    icgc_transport_parallel, file_from=icgc_transport_file_from,
                                                    repo='aws')
            self.check_code('Icgc', return_code)

        if 'ega' in object_ids and object_ids['ega']:
            check_access(self, ega_access, 'ega')
            if ega_transport_parallel != '1':
                self.logger.warning("Parallel streams on the ega client may cause reliability issues and failed " +
                                    "downloads.  This option is not recommended.")
            return_code = self.ega_client.download(object_ids['ega'], ega_access, ega_path, output,
                                                   ega_transport_parallel, ega_udt)
            self.check_code('Ega', return_code)

        if 'collaboratory' in object_ids and object_ids['collaboratory']:
            check_access(self, icgc_access, 'icgc')
            return_code = self.icgc_client.download(object_ids['collaboratory'], icgc_access, icgc_path, output,
                                                    icgc_transport_parallel, file_from=icgc_transport_file_from,
                                                    repo='collab')
            self.check_code('Icgc', return_code)

        if 'gdc' in object_ids and object_ids['gdc']:
            check_access(self, gdc_access, 'gdc')
            return_code = self.gdc_client.download(object_ids['gdc'], gdc_access, gdc_path, output,
                                                   gdc_transport_parallel, gdc_udt)
            self.check_code('Gdc', return_code)

    def check_code(self, client, code):
        if code != 0:
            self.logger.error("{} client exited with a nonzero error code {}.".format(client, code))
            raise click.ClickException("Please check client output for error messages")

    def size_check(self, size, override, output):
        free = psutil.disk_usage(output)[2]
        if free > size and not override:
            if not click.confirm("Ok to download {0}s of files?  ".format(''.join(convert_size(size))) +
                                 "There is {}s of free space in {}".format(''.join(convert_size(free)), output)):
                self.logger.info("User aborted download")
                raise click.Abort
        elif free <= size:
            self.logger.error("Not enough space detected for download of {0}.".format(''.join(convert_size(size))) +
                              "{} of space in {}".format(''.join(convert_size(free)), output))
