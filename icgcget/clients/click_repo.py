import click
REPOS = {
         'collaboratory': {'code': 'collaboratory', 'name': 'collab'},
         'aws': {'code': 'aws-virginia', 'name': 'aws'},
         'ega': {'code': 'ega', 'name': 'european genome association'},
         'gdc': {'code': 'gdc', 'name': 'genomic data commons'},
         'cghub': {'code': 'cghub', 'name': 'cancer genomic hub'},
         'pdc': {'code': 'pdc', 'name': 'bionimbus protected data commons'}
         }


class RepoParamType(click.ParamType):
    name = 'repo'

    def convert(self, value, param, ctx):
        try:
            if value in REPOS.keys():
                return REPOS[value]['code']
            elif len(value) == 1:
                  raise click.BadOptionUsage("Repos need to be entered in list format in config file.")
            elif repo:
                raise click.BadOptionUsage("Invalid repo {0}.  Valid repositories are: {1}".format(value,
                                                                                                   ' '.join(REPOS)))
        except ValueError:
            self.fail('%s is not a valid repository' % value, param, ctx)
