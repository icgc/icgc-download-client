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

import logging
import sys
import os
import yaml
import errno
import click

from clients.ega import ega_client
from clients.gdc import gdc_client
from clients.gnos import gt_client
from clients.icgc import icgc_client


def config_parse(filename):

    try:
        config_text = filename.read()
        filename.close()
    except IOError:
        print("Config file " + filename.name + " not found: Aborting")
        sys.exit(1)
    try:
        config_temp = yaml.load(config_text)
    except yaml.YAMLError:
        print("Could not read config file" + filename.name + ": Aborting")
        sys.exit(1)
    return config_temp


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

    make_directory(os.path.dirname(logfile))

    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    logger.addHandler(sh)
    return logger


def call_client(config, repo, fileid, manifest, output):
    config = config_parse(config)
    logger_setup(config['logfile'])
    make_directory(output)
    logger = logging.getLogger('__log__')
    code = 0

    if fileid is None and manifest is None:
        logger.error("Please provide either a file id value or a manifest file to download.")
        code = 1
        return code

    if repo == 'ega':
        if config['ega.username'] is None or config['ega.password'] is None:
            if config['ega.access'] is None:
                logger.error("No credentials provided for the ega repository.")
                code = 1
                return code
        if fileid is not None:
            if len(fileid) > 1:
                logger.error("The ega repository does not support input of multiple file id values.")
                code = 1
                return code
            else:
                if config['ega.transport.parallel'] != '1':
                    logger.warning("Parallel streams on the ega client may cause reliability issues and failed " +
                                   "downloads.  This option is not recommended.")
                code = ega_client.ega_call(fileid, config['ega.username'], config['ega.password'],config['ega.tool'],
                                           config['ega.transport.parallel'], config['udt'],
                                           output)
                if code != 0:
                    logger.error(repo + " exited with a nonzero error code.")

        if manifest is True:
            logger.warning("The ega repository doesn't support downloading from manifest files. Use the -f tag instead")
            code = 1
            return code

    elif repo == 'collab' or repo == 'aws':
        if config['icgc.access'] is None:
            logger.error("No credentials provided for the icgc repository")
            code = 1
            return code
        elif manifest is not True:
            code = icgc_client.icgc_manifest_call(fileid, config['icgc.access'], config['icgc.tool'],
                                                  config['icgc.transport.file.from'], config['icgc.transport.parallel'],
                                                  output, repo)
        elif fileid is not None:  # This code exists to let users use both file id's and manifests in one command
            if len(fileid) > 1:
                logger.error("The icgc repository does not support input of multiple file id values.")
                code = 1
                return code
            else:
                code = icgc_client.icgc_call(file, config['icgc.access'], config['icgc.tool'],
                                             config['icgc.transport.file.from'], config['icgc.transport.parallel'],
                                             output, repo)
        if code != 0:
            logger.error(repo + " exited with a nonzero error code.")

    elif repo == 'cghub':
        if config['cghub.access'] is None:
            logger.error("No credentials provided for the cghub repository.")
            code = 1
            return code
        if manifest is True:
            code = gt_client.genetorrent_manifest_call(fileid, config['cghub.access'], config['cghub.tool'],
                                                       config['cghub.transport.parallel'], output)
        elif fileid is not None:
            code = gt_client.genetorrent_call(file, config['cghub.access'], config['cghub.tool'],
                                              config['cghub.transport.parallel'], output)
        if code != 0:
            logger.error(repo + " exited with a nonzero error code.")

    elif repo == 'gdc':
        if manifest is True:
            code = gdc_client.gdc_manifest_call(fileid, config['gdc.access'], config['gdc.tool'], output,
                                                config['udt'], config['gdc.transport.parallel'])
        elif fileid is not None:
            code = gdc_client.gdc_call(fileid, config['gdc.access'], config['gdc.tool'], output, config['udt'],
                                       config['gdc.transport.parallel'])
        if code != 0:
            logger.error(repo + " exited with a nonzero error code.")

    return code


@click.command()
@click.option('--config', type=click.File(), default="/icgc/conf/config.yaml")
@click.argument('repo', type=click.Choice(['ega', 'collab', 'cghub', 'aws', 'gdc']))
@click.argument('fileid', nargs=-1)
@click.option('--manifest/--no-manifest', ' /-m', default="false")
@click.option('--output', default='/icgc/mnt/downloads', type=click.Path(exists=False))
def cli(config, repo, fileid, manifest, output):
    rc = call_client(config, repo, fileid, manifest, output)
    return rc


if __name__ == "__main__":
    cli()
