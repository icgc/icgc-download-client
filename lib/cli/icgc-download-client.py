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

import argparse
import logging
import yaml
import sys

from clients.ega import ega_client
from clients.gdc import gdc_client
from clients.gnos import gt_client
from clients.icgc import icgc_client


def config_parse(filename):

    try:
        config_text = open(filename, 'r')
    except IOError:
        print "Config file " + filename + " not found: Aborting"
        sys.exit(1)
    try:
        config_temp = yaml.load(config_text)
    except yaml.YAMLError:
        print "Could not read config file" + filename + ": Aborting"
        sys.exit(1)
    return config_temp


def logger_setup(logfile):

    if logfile is None:
        print "Logging file not specified: Aborting"
        sys.exit(1)
    logger = logging.getLogger('__log__')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    logger.addHandler(sh)
    return logger


repos = ['ega', 'collab', 'cghub', 'aws', 'gdc']

parser = argparse.ArgumentParser()
parser.add_argument("--config", nargs='?', default="/icgc/mnt/conf/config.yaml",
                    help="File used to set download preferences and authentication criteria")
parser.add_argument('repo', choices=repos, help='Specify which repository to download from, all lowercase letters')
parser.add_argument('-f', '--file', nargs='*', help='Lowercase identifier of file or path to manifest file')
parser.add_argument('-m', '--manifest', help='Flag used when the downloading from a manifest file')
parser.add_argument('--output', nargs='?', default='/icgc/mnt/downloads', help='Directory to save downloaded files')
args = parser.parse_args()

config = config_parse(args.config)
logger_setup(config['logfile'])
logger = logging.getLogger('__log__')
code = None

if args.file is None and args.manifest is None:
    logger.error("Please provide either a file id value or a manifest file to download.")
    sys.exit(1)

if args.repo == 'ega':
    if config['username.ega'] is None or config['password.ega'] is None:
        if config['access.ega'] is None:
            logger.error("No credentials provided for the ega repository.")
            sys.exit(1)
    if args.file is not None:
            if len(args.file) > 1:
                logger.error("The ega repository does not support input of multiple file id values.")
                sys.exit(1)
            else:
                if config['transport.parallel.ega'] is not '1':
                    logger.warning("Parallel streams on the ega client may cause reliability issues and failed " +
                                   "downloads.  This option is not recommended.")
                code = ega_client.ega_call(args.file, config['username.ega'], config['password.ega'],
                                           config['tool.ega'], config['transport.parallel.ega'], config['udt'],
                                           args.output)
                if code != 0:
                    logger.error(args.repo + " exited with a nonzero error code.")
                    sys.exit(2)
                sys.exit(1)
    if args.manifest is not None:
        logger.warning("The ega repository does not support downloading from manifest files.  Use the -f tag instead")
        sys.exit(1)
elif args.repo == 'collab' or args.repo == 'aws':
    if config['access.icgc'] is None:
        logger.error("No credentials provided for the icgc repository")
        sys.exit(1)
    if args.manifest is not None:
        code = icgc_client.icgc_manifest_call(args.manifest, config['access.icgc'], config['tool.icgc'],
                                              config['transport.file.from.icgc'], config['transport.parallel.icgc'],
                                              args.output, args.repo)
    if args.file is not None:  # This code exists to let users use both file id's and manifests in one command
        if len(args.file) > 1:
            logger.error("The icgc repository does not support input of multiple file id values.")
            sys.exit(1)
        else:
            code = icgc_client.icgc_call(args.file, config['access.icgc'], config['tool.icgc'],
                                         config['transport.file.from.icgc'], config['transport.parallel.icgc'],
                                         args.output, args.repo)

    if code != 0:
        logger.error(args.repo + " exited with a nonzero error code.")
        sys.exit(2)

elif args.repo == 'cghub':
    if config['access.cghub'] is None:
        logger.error("No credentials provided for the cghub repository.")
        sys.exit(1)
    if args.manifest is not None:
        code = gt_client.genetorrent_manifest_call(args.manifest, config['access.cghub'], config['tool.cghub'],
                                                   config['transport.parallel.cghub'], args.output)
    if args.file is not None:
        code = gt_client.genetorrent_call(args.file, config['access.cghub'], config['tool.cghub'],
                                          config['transport.parallel.cghub'], args.output)
    if code != 0:
        logger.error(args.repo + " exited with a nonzero error code.")
        sys.exit(2)

elif args.repo == 'gdc':
    if args.manifest is not None:
        code = gdc_client.gdc_manifest_call(args.manifest, config['access.gdc'], config['tool.gdc'], args.output,
                                            config['udt'], config['transport.parallel.gdc'])
    if args.file is not None:
        code = gdc_client.gdc_call(args.file, config['access.gdc'], config['tool.gdc'], args.output, config['udt'],
                                   config['transport.parallel.gdc'])
    if code != 0:
        logger.error(args.repo + " exited with a nonzero error code.")
        sys.exit(2)
