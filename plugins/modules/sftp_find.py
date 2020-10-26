#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Konstantinos Georgoudis <kgeor@blacklines.gr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: sftp_find

short_description: sftp find module

version_added: "1.0.0"

description:
    - Return a list of files based on specific criteria on an sftp server.
    - Multiple criteria are AND'd together.

options:
    path:
        description:
            - The path on the remote sftp server where the files are.
            - It can be full path, relative path, or a . for current path.
        required: true
        type: path
    pattern:
        description:
            - You can choose a filename, or wildcard ending with file extension.
            - E.g. filename.txt or *.csv or ADD_????????_export.csv
        type: str
        default: "*"
    server:
        description:
            - The IP address or the FQDN of the remote sftp server.
        required: true
        type: str
    port:
        description:
            - The TCP port of the remote sftp server. The default port is 22.
        type: int
        default: 22
    username:
        description:
            - Username for the sftp server.
        required: true
        type: str
    password:
        description:
            - Password for the sftp server.
        required: true
        type: str

requirements:
    pysftp>=0.2.9

author:
    - Konstantinos Georgoudis (@tsimouha)
'''

EXAMPLES = r'''

- name: Find all csv files on the remote sftp server
  sftp_find:
    path: /some_path
    pattern: *.csv
    server: test.example.com
    port: 22
    username: demo
    password: somepassword

'''

import fnmatch
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


def sftp_check_sftp_path(path, sftp, module):
    if not sftp.exists(path):
        module.fail_json(msg="The path %s does not exists" % path)

    if sftp.isfile(path):
        module.fail_json(msg="The path %s is not a directory" % path)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True),
            pattern=dict(type='str', required=True),
            server=dict(type='str', required=True),
            port=dict(type='int', required=True),
            username=dict(type='str', required=True),
            password=dict(type='str', no_log=True, required=True)
        ),
        supports_check_mode=True
    )

    path = module.params['path']
    pattern = module.params['pattern']
    server = module.params['server']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']

    files_found = []
    file_names = []

    if not PYSFTP_AVAILABLE:
        module.fail_json(msg=missing_required_lib("pysftp"), exception=LIB_IMP_ERR)

    with pysftp.Connection(server,
                           username=username,
                           password=password,
                           port=port) as sftp:

        sftp_check_sftp_path(path, sftp, module)

        sftp.cwd(path)
        directory_structure = sftp.listdir_attr()

        for file in directory_structure:
            if fnmatch.fnmatch(file.filename, pattern):
                changed = True

            if changed and not module.check_mode:
                files_found.append(sftp.normalize(file.filename))
                file_names.append(file.filename)

    module.exit_json(files_found=files_found, file_names=file_names, changed=changed)


if __name__ == '__main__':
    main()
