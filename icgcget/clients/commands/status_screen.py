import logging
from collections import OrderedDict

import click
from tabulate import tabulate

from command_utils import check_access, api_error_catch, filter_manifest_ids
from ..errors import SubprocessError
from ..utils import convert_size, donor_addition, increment_types
from .. import portal_client
from ..ega.ega_client import EgaDownloadClient
from ..gdc.gdc_client import GdcDownloadClient
from ..gnos.gnos_client import GnosDownloadClient
from ..icgc.storage_client import StorageClient


class StatusScreenDispatcher:
    def __init__(self):
        self.logger = logging.getLogger("__log__")
        self.gdc_client = GdcDownloadClient()
        self.ega_client = EgaDownloadClient()
        self.gt_client = GnosDownloadClient()
        self.icgc_client = StorageClient()

    def status_tables(self, repos, file_ids, manifest, api_url, no_files):
        repo_list = []
        gdc_ids = []
        cghub_ids = []
        repo_sizes = {}
        repo_counts = {}
        repo_donors = {}
        donors = []
        type_donors = {}
        type_sizes = {}
        type_counts = {}
        total_size = 0

        file_table = [["", "Size", "Unit", "File Format", "Data Type", "Repo"]]
        summary_table = [["", "Size", "Unit", "File Count", "Donor_Count"]]
        if manifest:
            if len(file_ids) > 1:
                self.logger.warning("For download from manifest files, multiple manifest id arguments is not supported")
                raise click.BadArgumentUsage("Multiple manifest files specified.")

            portal = portal_client.IcgcPortalClient()
            manifest_json = api_error_catch(self, portal.get_manifest_id, file_ids[0], api_url, repos)
            file_ids = filter_manifest_ids(self, manifest_json)

        if not repos:
            raise click.BadOptionUsage("Must include prioritized repositories")
        for repository in repos:
            repo_sizes[repository] = OrderedDict({"total": 0})
            repo_counts[repository] = {"total": 0}
            repo_donors[repository] = {"total": []}
        portal = portal_client.IcgcPortalClient()
        entities = portal.get_metadata_bulk(file_ids, api_url)
        count = len(entities)
        for entity in entities:
            size = entity["fileCopies"][0]["fileSize"]
            total_size += size
            repository, copy = self.match_repositories(repos, entity)
            data_type = entity["dataCategorization"]["dataType"]
            if data_type not in type_donors:
                type_donors[data_type] = []
                type_counts[data_type] = 0
                type_sizes[data_type] = 0
            if data_type not in repo_donors[repository]:
                repo_donors[repository][data_type] = []
            file_size = convert_size(size)
            if not no_files:
                file_table.append([entity["id"], file_size[0], file_size[1], copy["fileFormat"],
                                   data_type, repository])
            if repository == "gdc":
                gdc_ids.append(entity["dataBundle"]["dataBundleId"])
            if repository == "cghub":
                cghub_ids.append(entity["dataBundle"]["dataBundleId"])
            for donor_info in entity['donors']:
                repo_donors[repository]["total"] = donor_addition(repo_donors[repository]["total"], donor_info)
                repo_donors[repository][data_type] = donor_addition(repo_donors[repository][data_type], donor_info)
                donors = donor_addition(donors, donor_info)
                type_donors[data_type] = donor_addition(type_donors[data_type], donor_info)

            type_sizes[data_type] += size
            repo_sizes, repo_counts = increment_types(data_type, repository, repo_sizes, repo_counts, size)
            type_counts[data_type] += 1

        for repo in repo_sizes:
            for data_type in repo_sizes[repo]:
                file_size = convert_size(repo_sizes[repo][data_type])
                name = repo + ": " + data_type
                summary_table.append([name, file_size[0], file_size[1], repo_counts[repo][data_type],
                                      len(repo_donors[repo][data_type])])
                repo_list.append(repo)

        file_size = convert_size(total_size)
        summary_table.append(["Total", file_size[0], file_size[1], count, len(donors)])
        for data_type in type_sizes:
            file_size = convert_size(type_sizes[data_type])
            summary_table.append([data_type, file_size[0], file_size[1], type_counts[data_type],
                                  len(type_donors[data_type])])
        if not no_files:
            self.logger.info(tabulate(file_table, headers="firstrow", tablefmt="fancy_grid", numalign="right"))
        self.logger.info(tabulate(summary_table, headers="firstrow", tablefmt="fancy_grid", numalign="right"))
        return gdc_ids, cghub_ids, repo_list

    def access_checks(self, repo_list, cghub_access, cghub_path, ega_access, gdc_access, icgc_access, output, api_url,
                      gdc_ids=None, cghub_ids=None):
        if "collaboratory" in repo_list:
            check_access(self, icgc_access, "icgc")
            self.access_response(self.icgc_client.access_check(icgc_access, repo="collab", api_url=api_url),
                                 "Collaboratory.")
        if "aws-virginia" in repo_list:
            check_access(self, icgc_access, "icgc")
            self.access_response(self.icgc_client.access_check(icgc_access, repo="aws", api_url=api_url),
                                 "Amazon Web server.")
        if 'ega' in repo_list:
            check_access(self, ega_access, 'ega')
            self.access_response(self.ega_client.access_check(ega_access), "ega.")
        if 'gdc' in repo_list and gdc_ids:  # We don't get general access credentials to gdc, can't check without files.
            check_access(self, gdc_access, 'gdc')
            gdc_result = api_error_catch(self, self.gdc_client.access_check, gdc_access, gdc_ids)
            self.access_response(gdc_result, "gdc files specified.")
        if 'cghub' in repo_list and cghub_ids:  # as before, can't check cghub permissions without files
            check_access(self, cghub_access, 'cghub')
            try:
                self.access_response(self.gt_client.access_check(cghub_access, cghub_ids, cghub_path, output=output),
                                     "cghub files.")
            except SubprocessError as e:
                self.logger.error(e.message)
                raise click.Abort

    def match_repositories(self, repos, copies):
        for repository in repos:
            for copy in copies["fileCopies"]:
                if repository == copy["repoCode"]:
                    return repository, copy
        self.logger.error("File {} not found on repositories {}".format(copies["id"], repos))
        raise click.Abort

    def access_response(self, result, repo):
        if result:
            self.logger.info("Valid access to the " + repo)
        else:
            self.logger.info("Invalid access to the " + repo)
