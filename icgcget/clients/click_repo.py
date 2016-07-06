import click
import os
import tempfile
REPOS = {
         'collaboratory': {'code': 'collaboratory', 'name': 'collab'},
         'aws-virginia': {'code': 'aws-virginia', 'name': 'aws'},
         'ega': {'code': 'ega', 'name': 'european genome association'},
         'gdc': {'code': 'gdc', 'name': 'genomic data commons'},
         'cghub': {'code': 'cghub', 'name': 'cancer genomic hub'},
         'pdc': {'code': 'pdc', 'name': 'bionimbus protected data commons'}
         }


class Logfile(click.ParamType):
    name = 'logfile'

    def convert(self, value, param, ctx):
        if os.path.isdir(value):
            self.fail("Logfile destination '%s' is a directory" % value, param, ctx)
        elif os.path.isfile(value):
            try:
                logfile = open(value, 'a')
                logfile.close()
                return value
            except IOError as ex:
                if not ex.errno == 2:
                    self.fail("Unable to write to logfile '{}'" % value)
        else:
            try:
                directory, logfile = os.path.split(value)
                if os.access(directory, os.W_OK) and directory != tempfile.gettempdir():
                    return value
                else:
                    self.fail("Logfile cannot be made in selected directory '%s'" % directory, param, ctx)
            except ValueError:
                self.fail("Unable to resolve path to logfile '%s'" % value, param, ctx)


class RepoParamType(click.ParamType):
    name = 'repo'

    def convert(self, value, param, ctx):
        try:
            if value in REPOS.keys():
                return value
            else:
                self.fail("Invalid repo '{0}'.  Valid repos are: {1}".format(repo, ' '.join(REPOS)), param, ctx)
        except ValueError:
            self.fail('%s is not a valid repository' % value, param, ctx)


class ReposParamType(click.ParamType):
    name = 'repos'

    def convert(self, value, param, ctx):
        value = value.split(' ')
        repos = []
        for repo in value:
            if repo in REPOS.keys():
                repos.append(repo)
            elif repo:
                self.fail("Invalid repo '{0}'.  Valid repos are: {1}".format(repo, ' '.join(REPOS)), param, ctx)
        return repos
