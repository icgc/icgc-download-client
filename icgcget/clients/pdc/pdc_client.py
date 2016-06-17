#!/usr/bin/python
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
from icgcget.clients.errors import SubprocessError
from icgcget.clients.download_client import DownloadClient


class PdcDownloadClient(DownloadClient):

    def __init__(self, pickle_path=None):
        super(PdcDownloadClient, self).__init__(pickle_path)
        self.repo = 'pdc'

    def download(self, data_paths, key, tool_path, output, processes, udt=None, file_from=None, repo=None,
                 secret_key=None):
        code = 0
        os.environ['AWS_ACCESS_KEY_ID'] = key
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
        for data_path in data_paths:
            call_args = [tool_path, 's3', '--endpoint-url=https://bionimbus-objstore.opensciencedatacloud.org/', 'cp',
                         data_path, output + '/']
            code = self._run_command(call_args, self.download_parser)
            if code != 0:
                return code
            self.session_update(data_path, 'pdc')
        return code

    def access_check(self, key, data_paths=None, path=None, repo=None, output=None, api_url=None, secret_key=None):
        os.environ['AWS_ACCESS_KEY_ID'] = key
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
        for data_path in data_paths:
            call_args = [path, 's3', '--endpoint-url=https://bionimbus-objstore.opensciencedatacloud.org/', 'cp',
                         data_path, output + '/', '--dryrun']
            result = self._run_test_command(call_args, "(403)", "(404)")
            if result == 3:
                return False
            elif result == 0:
                return True
            elif result == 2:
                raise SubprocessError(result, "Path to AWS client did not lead to expected application")
            else:
                raise SubprocessError(result, "AWS failed with code {}".format(result))

    def print_version(self, path):
        call_args = [path, '--version']
        self._run_command(call_args, self.version_parser)

    def download_parser(self, output):
        self.logger.info(output)

    def version_parser(self, output):
        version = re.findall(r"aws-cli/[0-9.]+", output)
        if version:
            self.logger.info(" AWS CLI Version:             %s", version[0][8:])
