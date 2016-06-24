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

import os
import re

from icgcget.clients.download_client import DownloadClient
from icgcget.clients.portal_client import call_api


class StorageClient(DownloadClient):

    def __init__(self, json_path=None, docker=False, verify=True):
        super(StorageClient, self).__init__(json_path, docker)
        self.verify = verify

    def download(self, uuids, access, tool_path, staging, processes, udt=None, file_from=None, repo=None,
                 password=None):
        call_args = []
        env_dict = dict(os.environ)
        env_dict['ACCESSTOKEN'] = access
        env_dict['TRANSPORT_PARALLEL'] = processes
        if file_from is not None:
            os.environ['TRANSPORT_FILEFROM'] = file_from
        if self.docker:
            call_args = ['docker', 'run', '-e', 'ACCESSTOKEN='+access, '-e', 'TRANSPORT_PARALLEL=' + processes, '-t',
                         '-v', staging + ':/icgc/mnt', 'icgc/icgc-get:test']
        call_args.extend([tool_path, '--profile', repo, 'download', '--object-id'])
        call_args.extend(uuids)
        if self.docker:
            call_args.extend(['--output-dir', '/icgc/mnt'])
        else:
            call_args.extend(['--output-dir', staging])
        if repo == 'collab':
            self.repo = 'collaboratory'
        elif repo == 'aws':
            self.repo = 'aws-virginia'
        code = self._run_command(call_args, parser=self.download_parser, env=env_dict)
        return code

    def access_check(self, access, uuids=None, path=None, repo=None, output=None, api_url=None, password=None):
        request = api_url + 'settings/tokens/' + access
        resp = call_api(request, verify=self.verify)
        match = repo + ".download"
        return match in resp["scope"]

    def print_version(self, path):
        call_args = []
        if self.docker:
            call_args = ['docker', 'run', '-t', 'icgc/icgc-get:test']
        call_args.extend([path, 'version'])
        self._run_command(call_args, self.version_parser)

    def version_parser(self, response):
        version = re.findall(r"Version: [0-9.]+", response)
        if version:
            self.logger.info(" ICGC Storage Client %s", version[0])

    def download_parser(self, response):
        filename = re.findall(r"\(\w{8}-\w{4}-\w{4}-\w{4}-\w{12}.+", response)
        if filename:
            filename = filename[0][1:-1]
            self.session_update(filename, self.repo)
        self.logger.info(response)
