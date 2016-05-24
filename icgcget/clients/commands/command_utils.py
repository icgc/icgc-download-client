import click
from ..errors import ApiError
REPOS = ['collaboratory', 'aws-virginia', 'ega', 'gdc', 'cghub']


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


def check_access(self, access, name):
    if access is None:
        self.logger.error("No credentials provided for the {} repository".format(name))
        raise click.BadParameter("Please provide credentials for {}".format(name))


def api_error_catch(self, func, *args):
    try:
        return func(*args)
    except ApiError as e:
        self.logger.error(e.message)
        raise click.Abort
