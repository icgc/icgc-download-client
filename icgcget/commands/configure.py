import os
import yaml
import click
from icgcget.commands.utils import config_parse, validate_repos


class ConfigureDispatcher(object):

    def __init__(self, config_destination, default):
        self.old_config = {}
        if os.path.isfile(config_destination):
            old_config = config_parse(config_destination, default, empty_ok=True)
            if old_config:
                self.old_config = old_config['report']

    def configure(self, config_destination, repo_list):
        config_directory = os.path.split(config_destination)
        if not os.path.isdir(config_directory[0]):
            raise click.BadOptionUsage("Unable to write to directory {}".format(config_directory[0]))
        print "You will receive a series of prompts for all relevant configuration values and access parameters "
        print "Existing configuration values are listed in square brackets.  To keep these values, press Enter."
        print "To input multiple values for a prompt, separate each value with a space."
        output = self.prompt('output', input_type=click.Path(exists=True, writable=True, file_okay=False,
                                                             resolve_path=True))
        logfile = self.prompt('logfile')
        repos = self.prompt('repos')
        repos = repos.split(' ')
        validate_repos(repos, repo_list)
        conf_yaml = {'output': output, 'logfile': logfile, 'repos': repos}
        if "aws-virginia" in repos or "collaboratory" in repos:
            icgc_path = self.prompt('ICGC path', input_type=click.Path(exists=True, dir_okay=False, resolve_path=True))
            icgc_access = self.prompt('ICGC token', hide=True)
            conf_yaml["icgc"] = {'path': icgc_path, 'token': icgc_access}
        if "cghub" in repos:
            cghub_path = self.prompt('CGHub path', input_type=click.Path(exists=True, dir_okay=False,
                                                                         resolve_path=True))
            cghub_access = self.prompt('CGHub key', hide=True)
            conf_yaml["cghub"] = {'path': cghub_path, 'key': cghub_access}
        if "ega" in repos:
            ega_path = self.prompt('EGA path', input_type=click.Path(exists=True, dir_okay=False, resolve_path=True))
            ega_username = self.prompt('EGA username')
            ega_password = self.prompt('EGA password', hide=True)
            conf_yaml["ega"] = {'path': ega_path, 'username': ega_username, 'password': ega_password}
        if "gdc" in repos:
            gdc_path = self.prompt('GDC path', input_type=click.Path(exists=True, dir_okay=False, resolve_path=True))
            gdc_access = self.prompt('GDC token', hide=True)
            conf_yaml["gdc"] = {'path': gdc_path, 'token': gdc_access}
        if "pdc" in repos:
            pdc_path = self.prompt('PDC path', input_type=click.Path(exists=True, dir_okay=False, resolve_path=True))
            pdc_key = self.prompt('PDC key')
            pdc_secret_key = self.prompt('PDC secret key', hide=True)
            conf_yaml['pdc'] = {'path': pdc_path, 'key': pdc_key, 'secret': pdc_secret_key}

        config_file = open(config_destination, 'w')
        yaml.safe_dump(conf_yaml, config_file, encoding=None, default_flow_style=False)
        os.environ['ICGCGET_CONFIG'] = config_destination
        print "Configuration file saved to {}".format(config_file.name)

    def prompt(self, value_name, input_type=click.STRING, hide=False):
        default = None
        if value_name in self.old_config:
            if value_name == 'repos':
                default = ' '.join(self.old_config[value_name])
            else:
                default = self.old_config[value_name]
        if not default:
            default = ''
        value = click.prompt(value_name, default=default, hide_input=hide, type=input_type, show_default=not hide)
#        if value == '':
#            value = None
        return value
