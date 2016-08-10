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

import os
import tempfile
import click

REPOS = {'collaboratory': {'code': 'collaboratory', 'name': 'collab'},
         'aws-virginia': {'code': 'aws-virginia', 'name': 'aws'},
         'ega': {'code': 'ega', 'name': 'european genome association'},
         'gdc': {'code': 'gdc', 'name': 'genomic data commons'},
         'gnos': {'code': 'gnos', 'name': 'gnos'},
         'pdc': {'code': 'pdc', 'name': 'bionimbus protected data commons'}}

GNOS = {'pcawg-chicago-icgc': {'code': 'pcawg-chicago-icgc', 'name': 'pcawg-chicago-icgc',
                               'path': "https://gtrepo-osdc-icgc.annailabs.com/"},
        'pcawg-heidelberg': {'code': 'pcawg-heidelberg', 'name': 'pcawg-heidelberg',
                             'path': "https://gtrepo-dkfz.annailabs.com/"},
        'pcawg-london': {'code': 'pcawg-london', 'name': 'pcawg-london', 'path': "https://gtrepo-ebi.annailabs.com/"},
        'pcawg-tokyo': {'code': 'pcawg-tokyo', 'name': 'pcawg-tokyo', 'path': "https://gtrepo-riken.annailabs.com/"},
        'pcawg-seoul': {'code': 'pcawg-seoul', 'name': 'pcawg-seoul', 'path': "https://gtrepo-etri.annailabs.com/"},
        'pcawg-barcelona': {'code': 'pcawg-barcelona', 'name': 'pcawg-barcelona',
                            'path': "https://gtrepo-bsc.annailabs.com/"},
        'pcawg-cghub': {'code': 'pcawg-cghub', 'name': 'pcawg-cghub', 'path': "https://cghub.ucsc.edu/"},
        'pcawg-chicago-tcga': {'code': 'pcawg-chicago-tcga', 'name': 'pcawg-chicago-tcga',
                               'path': "https://gtrepo-osdc-tcga.annailabs.com/"}}


class LogfileParam(click.ParamType):
    """
    Custom click parameter to verify valid inputs for logfiles.
    """
    name = 'logfile'

    def convert(self, value, param, ctx):
        """
        Method to check if logfile is an accessible file if it exists or in an accessible directory if it doesn't exist
        :param value:
        :param param:
        :param ctx:
        :return:
        """
        if os.path.isdir(value):
            self.fail("Logfile destination '%s' is a directory" % value, param, ctx)
        elif os.path.isfile(value):
            try:
                logfile = open(value, 'a')
                logfile.close()
                return value
            except IOError as ex:
                if ex.errno != 2:
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


class RepoParam(click.ParamType):
    """
    Custom click parameter for a single repository.  Used for command line inputs, typically provided in a list
    """
    name = 'repo'

    def convert(self, value, param, ctx):
        """
        Function that verifies that repository name is valid repository name
        :param value:
        :param param:
        :param ctx:
        :return:
        """
        try:
            if value in REPOS.keys() or value in GNOS.keys():
                return value
            else:
                self.fail("Invalid repo '{0}'.  Valid repos are: {1}".format(value, ' '.join(REPOS)), param, ctx)
        except ValueError:
            self.fail('%s is not a valid repository' % value, param, ctx)


class ReposParam(click.ParamType):
    """
    Custom click parameter for a list of repositories: used in the configure function exclusively due to limitations of
    prompts.
    """
    name = 'repos'

    def convert(self, value, param, ctx):
        """
        Function that ensures every non null value must be a valid repository name.  Null values are stripped later
        :param value:
        :param param:
        :param ctx:
        :return:
        """
        value = value.split(' ')
        repos = []
        for repo in value:
            if repo in REPOS.keys() or GNOS.keys():
                repos.append(repo)
            elif repo:
                self.fail("Invalid repo '{0}'.  Valid repos are: {1}".format(repo, ' '.join(REPOS)), param, ctx)
        return repos
