import logging
import click
import psutil
from tabulate import tabulate
from clients.errors import ApiError, SubprocessError
from collections import OrderedDict
from clients import portal_client
from clients.ega.ega_client import EgaDownloadClient
from clients.gdc.gdc_client import GdcDownloadClient
from clients.gnos.gnos_client import GnosDownloadClient
from clients.icgc.storage_client import StorageClient
from utils import convert_size, calculate_size, donor_addition, increment_types

REPOS = ['collaboratory', 'aws-virginia', 'ega', 'gdc', 'cghub']


class Dispatcher:
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
            manifest_json = self.api_error_catch(portal.get_manifest_id, file_ids[0], api_url, repos)
        else:
            portal = portal_client.IcgcPortalClient()
            manifest_json = self.api_error_catch(portal.get_manifest, file_ids, api_url, repos)

        if not manifest_json["unique"] or len(manifest_json["entries"]) != 1:
            self.filter_manifest_ids(manifest_json, )
        size, object_ids = calculate_size(manifest_json)

        self.size_check(size, yes_to_all, output)
        return object_ids

    def download(self, object_ids, output,
                 cghub_access, cghub_path, cghub_transport_parallel,
                 ega_access, ega_path, ega_transport_parallel, ega_udt,
                 gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
                 icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_parallel):
        if 'cghub' in object_ids and object_ids['cghub']:
            self.check_access(cghub_access, 'cghub')
            return_code = self.gt_client.download(object_ids['cghub'], cghub_access, cghub_path, output,
                                                  cghub_transport_parallel)
            self.check_code('Cghub', return_code)

        if 'aws-virginia' in object_ids and object_ids['aws-virginia']:
            self.check_access(icgc_access, 'icgc')
            return_code = self.icgc_client.download(object_ids['aws-virginia'], icgc_access, icgc_path, output,
                                                    icgc_transport_parallel, file_from=icgc_transport_file_from,
                                                    repo='aws')
            self.check_code('Icgc', return_code)

        if 'ega' in object_ids and object_ids['ega']:
            self.check_access(ega_access, 'ega')
            if ega_transport_parallel != '1':
                self.logger.warning("Parallel streams on the ega client may cause reliability issues and failed " +
                                    "downloads.  This option is not recommended.")
            return_code = self.ega_client.download(object_ids['ega'], ega_access, ega_path, output,
                                                   ega_transport_parallel, ega_udt)
            self.check_code('Ega', return_code)

        if 'collaboratory' in object_ids and object_ids['collaboratory']:
            self.check_access(icgc_access, 'icgc')
            return_code = self.icgc_client.download(object_ids['collaboratory'], icgc_access, icgc_path, output,
                                                    icgc_transport_parallel, file_from=icgc_transport_file_from,
                                                    repo='collab')
            self.check_code('Icgc', return_code)

        if 'gdc' in object_ids and object_ids['gdc']:
            self.check_access(gdc_access, 'gdc')
            return_code = self.gdc_client.download(object_ids['gdc'], gdc_access, gdc_path, output,
                                                   gdc_transport_parallel, gdc_udt)
            self.check_code('Gdc', return_code)

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
            manifest_json = self.api_error_catch(portal.get_manifest_id, file_ids[0], api_url, repos)
            file_ids = self.filter_manifest_ids(manifest_json)

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
            self.check_access(icgc_access, "icgc")
            self.access_response(self.icgc_client.access_check(icgc_access, repo="collab", api_url=api_url),
                                 "Collaboratory.")
        if "aws-virginia" in repo_list:
            self.check_access(icgc_access, "icgc")
            self.access_response(self.icgc_client.access_check(icgc_access, repo="aws", api_url=api_url),
                                 "Amazon Web server.")
        if 'ega' in repo_list:
            self.check_access(ega_access, 'ega')
            self.access_response(self.ega_client.access_check(ega_access), "ega.")
        if 'gdc' in repo_list and gdc_ids:  # We don't get general access credentials to gdc, can't check without files.
            self.check_access(gdc_access, 'gdc')
            gdc_result = self.api_error_catch(self.gdc_client.access_check, gdc_access, gdc_ids)
            self.access_response(gdc_result, "gdc files specified.")
        if 'cghub' in repo_list and cghub_ids:  # as before, can't check cghub permissions without files
            self.check_access(cghub_access, 'cghub')
            try:
                self.access_response(self.gt_client.access_check(cghub_access, cghub_ids, cghub_path, output=output),
                                     "cghub files.")
            except SubprocessError as e:
                self.logger.error(e.message)
                raise click.Abort

    def version_checks(self, cghub_path, ega_access, ega_path, gdc_path, icgc_path):
        self.gdc_client.version_check(gdc_path)
        self.ega_client.version_check(ega_path, ega_access)
        self.gt_client.version_check(cghub_path)
        self.icgc_client.version_check(icgc_path)

    def match_repositories(self, repos, copies):
        for repository in repos:
            for copy in copies["fileCopies"]:
                if repository == copy["repoCode"]:
                    return repository, copy
        self.logger.error("File {} not found on repositories {}".format(copies["id"], repos))
        raise click.Abort

    def filter_manifest_ids(self, manifest_json):
        fi_ids = []  # Function to return a list of unique  file ids from a manifest.  Throws error if not unique
        for repo_info in manifest_json["entries"]:
            if repo_info["repo"] in REPOS:
                for file_info in repo_info["files"]:
                    if file_info["id"] in fi_ids:
                        self.logger.error("Supplied manifest has repeated file identifiers.  Please specify a " +
                                          "list of repositories to prioritize")
                        raise click.Abort
                    else:
                        fi_ids.append(file_info["id"])
        if not fi_ids:
            self.logger.warning("Files on manifest are not found on specified repositories")
            raise click.Abort
        return fi_ids

    def check_code(self, client, code):
        if code != 0:
            self.logger.error("{} client exited with a nonzero error code {}.".format(client, code))
            raise click.ClickException("Please check client output for error messages")

    def check_access(self, access, name):
        if access is None:
            self.logger.error("No credentials provided for the {} repository".format(name))
            raise click.BadParameter("Please provide credentials for {}".format(name))

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
            raise click.Abort

    def access_response(self, result, repo):
        if result:
            self.logger.info("Valid access to the " + repo)
        else:
            self.logger.info("Invalid access to the " + repo)

    def api_error_catch(self, func, *args):
        try:
            return func(*args)
        except ApiError as e:
            self.logger.error(e.message)
            raise click.Abort
