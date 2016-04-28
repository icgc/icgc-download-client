#
# Copyright (c) 2016 The Ontario Institute for Cancer Research. All rights reserved.
#
# This program and the accompanying materials are made available under the terms of the GNU Public License v3.0.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import errno
import logging
import os
import sys

import click
import yaml
import collections

from clients.ega import ega_client
from clients.gdc import gdc_client
from clients.gnos import gt_client
from clients.icgc import icgc_client


def config_parse(filename):
    try:
        config_text = open(filename, 'r')
    except IOError:
        print("Config file {} not found: Aborting".format(filename.name))
        sys.exit(1)
    try:
        config_temp = yaml.safe_load(config_text)
        config_download = flatten_dict(normalize_keys(config_temp))
        config = {'download': config_download, 'logfile': config_temp['logfile']}
    except yaml.YAMLError:
        print("Could not read config file {}: Aborting".format(filename.name))
        sys.exit(1)
    return config


def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def normalize_keys(obj):
    if type(obj) != dict:
        return obj
    else:
        return {k.replace('.', '_'): normalize_keys(v) for k, v in obj.items()}


def make_directory(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def logger_setup(logfile):
    if logfile is None:
        print("Logging file not specified: Aborting")
        sys.exit(1)
    logger = logging.getLogger('__log__')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # make_directory(os.path.dirname(logfile))
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    logger.addHandler(sh)
    return logger


@click.group()
@click.option('--config', default=os.path.join(click.get_app_dir('icgc-get'), 'config.yaml'), envvar="ICGCGET.CONFIG",
              type=click.Path(exists=True))
@click.option('--logfile', default=None, envvar="ICGCGET.LOGFILE", type=click.Path(exists=True))
@click.pass_context
def cli(cli_context, config, logfile):
    config_file = config_parse(config)
    if logfile is not None:
        logger_setup(logfile)
    else:
        logger_setup(config_file['logfile'])
    cli_context.default_map = config_file
    return config_file


@click.command()
@click.argument('repo', type=click.Choice(['collab', 'aws', 'ega', 'gdc', 'cghub']))
@click.argument('fileid', nargs=-1)
@click.option('--manifest', '-m', default="false")
@click.option('--output', type=click.Path(exists=False), envvar="ICGCGET.OUTPUT")
@click.option('--udt', envvar="ICGCGET.UDT")
@click.option('--transport-memory', envvar="ICGCGET.TRANSPORT.MEMORY")
@click.option('--ega-transport-parallel', envvar="ICGCGET.EGA.TRANSPORT.PARALLEL")
@click.option('--ega-username', envvar="ICGCGET.EGA.USERNAME")
@click.option('--ega-password', envvar="ICGCGET.EGA.PASSWORD")
@click.option('--ega-access', envvar="ICGCGET.EGA.ACCESS")
@click.option('--ega-path', envvar="ICGCGET.EGA.PATH")
@click.option('--gdc-transport-parallel', envvar="ICGCGET.GDC.TRANSPORT.PARALLEL")
@click.option('--gdc-access', envvar="ICGCGET.GDC.ACCESS")
@click.option('--gdc-path', envvar="ICGCGET.GDC.PATH")
@click.option('--cghub-transport-parallel', envvar="ICGCGET.CGHUB.TRANSPORT.PARALLEL")
@click.option('--cghub-access', envvar="ICGCGET.CGHUB.ACCESS")
@click.option('--cghub-path', envvar="ICGCGET.CGHUB.PATH")
@click.option('--icgc-transport-parallel', envvar="ICGCGET.ICGC.TRANSPORT.PARALLEL")
@click.option('--icgc-access', envvar="ICGCGET.ACCESS")
@click.option('--icgc-path', envvar="ICGCGET.ICGC.PATH")
@click.option('--icgc-transport-file-from', envvar="ICGCGET.ICGC.FILE.FROM")
@click.pass_context
def download(ctex, repo, fileid, manifest, output, udt, transport_memory, ega_transport_parallel, ega_access,
             ega_username, ega_password, ega_path, gdc_transport_parallel, gdc_access, gdc_path,
             cghub_transport_parallel, cghub_access, cghub_path, icgc_transport_parallel, icgc_access, icgc_path,
             icgc_transport_file_from):

        logger = logging.getLogger('__log__')
        code = 0

        if fileid is None and manifest is None:
            logger.error("Please provide either a file id value or a manifest file to download.")
            code = 1
            return code

        if repo == 'ega':
            if ega_username is None or ega_password is None:
                if ega_access is None:
                    logger.error("No credentials provided for the ega repository.")
                    code = 1
                    return code
            if fileid is not None:
                if len(fileid) > 1:
                    logger.error("The ega repository does not support input of multiple file id values.")
                    code = 1
                    return code
                else:
                    if ega_transport_parallel != '1':
                        logger.warning("Parallel streams on the ega client may cause reliability issues and failed " +
                                       "downloads.  This option is not recommended.")
                    code = ega_client.ega_call(fileid, ega_username, ega_password, ega_path, ega_transport_parallel,
                                               udt, output)
                    if code != 0:
                        logger.error("{} exited with a nonzero error code.".format(repo))

            if manifest is True:
                logger.warning(
                    "The ega repository doesn't support downloading from manifest files. Use the -f tag instead")
                code = 1
                return code

        elif repo == 'collab' or repo == 'aws':
            if icgc_access is None:
                logger.error("No credentials provided for the icgc repository")
                code = 1
                return code
            elif manifest is not True:
                code = icgc_client.icgc_manifest_call(fileid, icgc_access, icgc_path, icgc_transport_file_from,
                                                      icgc_transport_parallel, output, repo)
            elif fileid is not None:  # This code exists to let users use both file id's and manifests in one command
                if len(fileid) > 1:
                    logger.error("The icgc repository does not support input of multiple file id values.")
                    code = 1
                    return code
                else:
                    code = icgc_client.icgc_call(fileid, icgc_access, icgc_path, icgc_transport_file_from,
                                                 icgc_transport_parallel, output, repo)
            if code != 0:
                logger.error(repo + " exited with a nonzero error code.")

        elif repo == 'cghub':
            if cghub_access is None:
                logger.error("No credentials provided for the cghub repository.")
                code = 1
                return code
            if manifest is True:
                code = gt_client.genetorrent_manifest_call(fileid, cghub_access, cghub_path, cghub_transport_parallel,
                                                           output)
            elif fileid is not None:
                code = gt_client.genetorrent_call(fileid, cghub_access, cghub_path,
                                                  cghub_transport_parallel, output)
            if code != 0:
                logger.error(repo + " exited with a nonzero error code.")

        elif repo == 'gdc':
            if manifest is True:
                code = gdc_client.gdc_manifest_call(fileid, gdc_access, gdc_path, output, udt, gdc_transport_parallel)
            elif fileid is not None:
                code = gdc_client.gdc_call(fileid, gdc_access, gdc_path, output, udt, gdc_transport_parallel)
            if code != 0:
                logger.error(repo + " exited with a nonzero error code.")

        return code



if __name__ == "__main__":
    cli.add_command(download)
    sys.exit(cli())
