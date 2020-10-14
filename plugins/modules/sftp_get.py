#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Konstantinos Georgoudis <kgeor@blacklines.gr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: sftp_get

short_description: sftp client module

version_added: "1.0.0"

description: This module acts like an sftp client. It will connect on sftp servers and download files. You can deside whether you delete the files or not from the sftp server.

options:
    path:
        description: The path on the remote sftp server where the files are. It can be full path, relative path, or a . for current path.
        required: true
        type: path
    pattern:
        description: You can choose a filename, or wildcard ending with file extension. E.g. filaneme.txt or *.csv or ADD_????????_export.csv
        type: str
        default: "*"
    local_path:
        description: The local path where the files will be copied to. It can be full path, relative path, or a . for current path.
        required: true
        type: path
    server:
        description: The IP address or the FQDN of the remote sftp server.
        required: true
        type: str
    port:
        description: The TCP port of the remote sftp server. By default it's port 22.
        type: int
        default: 22
    delete:
        description: Deside if you want to delete files from the sftp server after they are successfully downloaded.
        type: bool
        default: no
    username:
        description: Username for the sftp connection.
        required: true
        type: str
    password:
        description: Password for the sftp connection.
        required: true
        type: str

requirements:
    pysftp>=0.2.9

author:
    - Konstantinos Georgoudis (@tsimouha)
'''

EXAMPLES = r'''

- name: Get all files from the remote sftp server and delete them from the source system
  sftp_client:
    path: /
    pattern: *.csv
    local_path: tmp
    server: test.example.com
    port: 22
    username: demo
    password: somepassword
    delete: true

'''

import os
import fnmatch
import json
import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import missing_required_lib

LIB_IMP_ERR = None
try:
    import pysftp
    PYSFTP_AVAILABLE = True
except ImportError:
    PYSFTP_AVAILABLE = False
    LIB_IMP_ERR = traceback.format_exc()

def check_local_path(module):

    local_path = module.params['local_path']
    if os.path.isfile(local_path):
        module.fail_json(msg="Local path %s is not a directory" % (local_path))
    if not os.path.exists(local_path):
        module.fail_json(msg="Local path %s does not exists" % (local_path))
    if not os.access(local_path, os.R_OK):
        module.fail_json(msg="Local path %s not readable. Make sure you have the right permissions" % (local_path))

def sftp_get_files(module, result):

    changed = False

    local_path = os.path.abspath(module.params['local_path'])
    local_path = os.path.join(local_path, '')
    files_proc = []
    files_skipped = []
    local_files = []

    with pysftp.Connection(module.params['server'], 
                        username=module.params['username'], 
                        password=module.params['password'], 
                        port=module.params['port']) as sftp:

        sftp.cwd(module.params['path'])
        directory_structure = sftp.listdir_attr()

        for file in directory_structure:
            if fnmatch.fnmatch(file.filename, module.params['pattern']):
                
                result['remote_files'].append(file.filename)
                local_file = local_path + file.filename
                
                if os.path.isfile(local_file) and sftp.stat(file.filename).st_mtime == os.stat(local_file).st_mtime:
                    files_skipped.append(file.filename)
                    continue
                else:
                    sftp.get(file.filename, local_file, preserve_mtime=True)
                    local_files.append(local_file)
                    files_proc.append(file.filename)
                    if module.params['delete']:
                        sftp.remove(file.filename)
                    changed = True

    result['changed'] = changed
    result['pattern'] = module.params['pattern']
    result['remote_path'] = module.params['path']
    result['local_path'] = local_path
    result['processed_count'] = len(files_proc)
    result['processed'] = files_proc
    result['skipped'] = files_skipped

    return result

def run_module():
    module_args = dict(
        path=dict(type='path', required=True),
        pattern=dict(type='str', required=True),
        local_path=dict(type='path', required=True),
        server=dict(type='str', required=True),
        port=dict(type='int', required=True),
        recurse=dict(type='bool', default=False),
        delete=dict(type='bool', default=False),
        username=dict(type='str',required=True),
        password=dict(type='str', no_log=True, required=True)
    )
 
    result = dict(
        changed = False,
        pattern = '',
        remote_files = list(),
        processed_count = '',
        skipped = '',
        remote_path='',
        local_path=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not PYSFTP_AVAILABLE:
        module.fail_json(msg=missing_required_lib("pysftp"), exception=LIB_IMP_ERR)

    if module.check_mode:
        module.exit_json(**result)

    check_local_path(module)
    sftp_get_files(module, result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

