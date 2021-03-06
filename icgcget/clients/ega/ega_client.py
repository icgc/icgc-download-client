#!/usr/bin/python
# -*- coding: utf-8 -*-
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

import fnmatch
import os
import re
from copy import copy
from random import SystemRandom
from string import ascii_uppercase, digits
from urllib import quote
from requests import HTTPError

from icgcget.clients.utils  import client_style
from icgcget.clients.download_client import DownloadClient
from icgcget.clients.portal_client import call_api


class EgaDownloadClient(DownloadClient):
    """
    Download client subclass responsible for communicating with the EGA download client
    """
    def __init__(self, json_path=None, docker=False, verify=True, log_dir=None, container_version=''):
        super(EgaDownloadClient, self) .__init__(json_path, log_dir, docker=docker, container_version=container_version)
        self.repo = 'ega'
        self.verify = verify
        self.label = ''
        self.skip = False

    def download(self, object_ids, access, tool_path, staging, parallel, udt=None, file_from=None, repo=None,
                 secret_key=None, password=None):
        """
        Inherited method.  Makes four subprocess calls to request, download and decrypt data from the EGA repository
        :param object_ids:
        :param access:
        :param tool_path:
        :param staging:
        :param parallel:
        :param udt:
        :param file_from:
        :param repo:
        :param password:
        :param secret_key:
        :return:
        """
        key = ''.join(SystemRandom().choice(ascii_uppercase + digits) for _ in range(4))
        self.label = object_ids[0] + '_download_request'
        args = ['java', '-jar', tool_path, '-p', access, password, '-nt', parallel]
        if self.docker:
            args = self.prepend_docker_args(args, staging)
            file_dir = self.docker_mnt
        else:
            file_dir = staging
        # Get a list of outstanding requests, to see if the current request has already been made
        request_list_args = copy(args)
        request_list_args.append('-lr')
        code = self._run_command(request_list_args, self.requests_parser)
        if code != 0:
            return code
        # If the request hasn't already been made, make a download request
        if not self.skip:
            for object_id in object_ids:
                request_call_args = copy(args)
                if object_id[3] == 'D':
                    request_call_args.append('-rfd')
                else:
                    request_call_args.append('-rf')
                request_call_args.extend([object_id, '-re', key, '-label', self.label])
                rc_request = self._run_command(request_call_args, self.download_parser)
                if rc_request != 0:
                    return rc_request
        # Now that request exists in some form, download the files
        download_call_args = copy(args)
        download_call_args.extend(['-dr', self.label, '-path', file_dir])
        if udt:
            download_call_args.append('-udt')
        rc_download = self._run_command(download_call_args, self.download_parser)
        if rc_download != 0:
            return rc_download
        # Decrypt downloaded files
        decrypt_call_args = copy(args)
        decrypt_call_args.append('-dc')
        for cip_file in os.listdir(file_dir):  # File names cannot be dynamically predicted from dataset names
            if fnmatch.fnmatch(cip_file, '*.cip'):  # Tool attempts to decrypt all encrypted files in download directory
                decrypt_call_args.append(file_dir + '/' + cip_file)
        decrypt_call_args.extend(['-dck', key])
        rc_decrypt = self._run_command(decrypt_call_args, self.download_parser)
        if rc_decrypt != 0:
            return rc_decrypt
        return 0

    def access_check(self, access, uuids=None, path=None, repo=None, output=None, api_url=None, password=None,
                     secret_key=None):
        """
        Calls ega api once to log in and a second time to verify access
        :param access:
        :param uuids:
        :param path:
        :param repo:
        :param output:
        :param api_url:
        :param password:
        :param secret_key:
        :return:
        """
        base_url = 'https://ega.ebi.ac.uk/ega/rest/access/v2/'

        login_request = base_url + 'users/' + quote(access) + '?pass=' + quote(password)
        try:
            resp = call_api(login_request, verify=self.verify)
        except HTTPError:  # invalid return code
            return False
        if resp['header']['userMessage'] == 'OK':
            session_id = resp['response']['result'][1]
            dataset_request = base_url + 'datasets?session=' + session_id
            try:
                dataset_response = call_api(dataset_request, verify=self.verify)
                data_sets = dataset_response['response']['result']
            except HTTPError:
                return False
            if 'EGAD00001000023' in data_sets and 'EGAD00010000562' in data_sets:
                return True
        return False

    def print_version(self, path):
        """
        Makes subprocess call to show EGA version
        """
        call_args = ['java', '-jar', path, '-p', 'demo@test.org', '123pass']
        if self.docker:
            call_args = self.prepend_docker_args(call_args)
        self._run_command(call_args, self.version_parser)

    def version_parser(self, response):
        """
        Method to parse version number from client version output
        :param response:
        :return:
        """
        version = re.findall(r"Version: [0-9.]+", response)
        if version:
            version = version[0][9:]
            self.logger.info(' EGA Client Version:          %s', version)

    def download_parser(self, response):
        """
        Parser to keep track of which files are being downloaded in session info and output client response to user
        :param response:
        :return:
        """
        filename = re.findall(r'/[^/]+.cip  \(', response)
        if filename:
            filename = filename[0][1:-7]
            self.session_update(filename, 'ega')
        self.logger.info(client_style(response.strip()))

    def requests_parser(self, response):
        """
        Parser that attempts to identify if a request for a given file has already been made based on request command
        output
        :param response:
        :return:
        """
        request = re.findall(r'EGA[A-Z][0-9]+_download_request', response)
        if request and request[0] == self.label:
            self.skip = True
