import logging

import click
import psutil
import os
import shutil
from command_utils import api_error_catch, filter_manifest_ids, check_access
from ..utils import calculate_size, convert_size
from .. import portal_client
from ..ega.ega_client import EgaDownloadClient
from ..gdc.gdc_client import GdcDownloadClient
from ..gnos.gnos_client import GnosDownloadClient
from ..icgc.storage_client import StorageClient

REPOS = ['collaboratory', 'aws-virginia', 'ega', 'gdc', 'cghub']


class DownloadDispatcher:
    def __init__(self, pickle_path):
        self.logger = logging.getLogger("__log__")
        self.gdc_client = GdcDownloadClient(pickle_path)
        self.ega_client = EgaDownloadClient(pickle_path)
        self.gt_client = GnosDownloadClient(pickle_path)
        self.icgc_client = StorageClient(pickle_path)

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
        if manifest:
            file_ids = []
            for repo in object_ids:
                file_ids.append(object_ids[repo].keys())
        entities = api_error_catch(self, portal.get_metadata_bulk, file_ids, api_url)
        for entity in entities:
            for repo_ids in object_ids:
                if entity['id'] in object_ids[repo_ids]:
                    repo = repo_ids
                    break
            else:
                continue

            filecopies = entity['fileCopies']
            for copy in filecopies:
                if copy['repoCode'] == repo:
                    if copy["fileName"] in os.listdir(output):
                        object_ids[repo].pop(entity['id'])
                        self.logger.warning("File {} found in download directory, skipping".format(entity['id']))
                        break
                    object_ids[repo][entity["id"]]['filename'] = copy["fileName"]
                    if "fileName" in copy["indexFile"]:
                        object_ids[repo][entity["id"]]['index_filename'] = copy["indexFile"]["fileName"]
                        break
        self.size_check(size, yes_to_all, output)
        return object_ids

    def download(self, object_ids, staging, output,
                 cghub_access, cghub_path, cghub_transport_parallel,
                 ega_access, ega_path, ega_transport_parallel, ega_udt,
                 gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
                 icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_parallel):

        if 'cghub' in object_ids and object_ids['cghub']:
            check_access(self, cghub_access, 'cghub')
            self.gt_client.session = object_ids
            uuids = self.get_uuids(object_ids['cghub'])
            return_code = self.gt_client.download(uuids, cghub_access, cghub_path, staging, cghub_transport_parallel)
            object_ids = self.icgc_client.session
            self.check_code('Cghub', return_code)
            self.move_files(staging, output)

        if 'aws-virginia' in object_ids and object_ids['aws-virginia']:
            check_access(self, icgc_access, 'icgc')
            self.icgc_client.session = object_ids
            uuids = self.get_uuids(object_ids['aws-virginia'])
            return_code = self.icgc_client.download(uuids, icgc_access, icgc_path, staging, icgc_transport_parallel,
                                                    file_from=icgc_transport_file_from, repo='aws')
            object_ids = self.icgc_client.session
            self.check_code('Icgc', return_code)
            self.move_files(staging, output)

        if 'ega' in object_ids and object_ids['ega']:
            check_access(self, ega_access, 'ega')
            if ega_transport_parallel != '1':
                self.logger.warning("Parallel streams on the ega client may cause reliability issues and failed " +
                                    "downloads.  This option is not recommended.")
            self.ega_client.session = object_ids
            uuids = self.get_uuids(object_ids['ega'])
            return_code = self.ega_client.download(uuids, ega_access, ega_path, staging, ega_transport_parallel, ega_udt)
            object_ids = self.icgc_client.session
            self.check_code('Ega', return_code)
            self.move_files(staging, output)

        if 'collaboratory' in object_ids and object_ids['collaboratory']:
            check_access(self, icgc_access, 'icgc')
            self.icgc_client.session = object_ids
            uuids = self.get_uuids(object_ids['collaboratory'])
            return_code = self.icgc_client.download(uuids, icgc_access, icgc_path, staging, icgc_transport_parallel,
                                                    file_from=icgc_transport_file_from, repo='collab')
            object_ids = self.icgc_client.session
            self.check_code('Icgc', return_code)
            self.move_files(staging, output)

        if 'gdc' in object_ids and object_ids['gdc']:
            check_access(self, gdc_access, 'gdc')
            uuids = self.get_uuids(object_ids['gdc'])
            self.gdc_client.session = object_ids
            return_code = self.gdc_client.download(uuids, gdc_access, gdc_path, staging, gdc_transport_parallel, gdc_udt)
            self.check_code('Gdc', return_code)
            self.move_files(staging, output)

    def compare(self, current_session, old_session, override):
        updated_session = {}
        for repo in current_session:
            updated_session[repo] = {}
            if repo not in old_session:
                if self.override_prompt(override):
                    return current_session
            for fi_id in current_session[repo]:
                if fi_id in old_session[repo]:
                    if old_session[repo][fi_id]['state'] != "Finished":
                        updated_session[repo][fi_id] = current_session[repo][fi_id]
                else:
                    if self.override_prompt(override):
                        return current_session
        return updated_session

    def check_code(self, client, code):
        if code != 0:
            self.logger.error("{} client exited with a nonzero error code {}.".format(client, code))
            raise click.ClickException("Please check client output for error messages")

    @staticmethod
    def override_prompt(override):
        if override:
            return True
        if click.confirm("Previous session data does not match current command.  Ok to delete previous session info?"):
            return True
        else:
            raise click.Abort

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

    @staticmethod
    def get_uuids(object_ids):
        uuids = []
        for object_id in object_ids:
            uuids.append(object_ids[object_id]['uuid'])
        return uuids

    def move_files(self, staging, output):
        for staged_file in os.listdir(staging):
            if staged_file != "state.pk":
                try:
                    shutil.move(staging + '/' + staged_file, output)
                except shutil.Error:
                    self.logger.warning('File {} already present in download directory'.format(staged_file))