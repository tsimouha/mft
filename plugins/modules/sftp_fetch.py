#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Konstantinos Georgoudis <kgeor@blacklines.gr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

import os
import pysftp
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r'''
---
module: sftp_fetch

short_description: sftp fetch module

version_added: "1.0.1"

description: This module acts like an sftp fetch client. It will connect on sftp servers and download the requested file(s). You can decide whether you want to archive files on the sftp server or not.

options:
    src:
        description: The path on the remote sftp server where the files are. It can be full path, relative path, or a . for current path.
        required: true
        type: path
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
    archive:
        description: Decide if you want to archive files on the sftp server after they have successfully been downloaded.
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

- name: Fetches all files from a remote sftp server and moves them in the Archive directory
  sftp_fetch:
    src: '/filaneme.txt'
    local_path: 'tmp'
    server: 'test.example.com'
    port: 22
    username: 'demo'
    password: 'somepassword'
    archive: true
'''


def check_local_path(module, local_path):
    local_path = local_path
    if os.path.isfile(local_path):
        module.fail_json(msg="Local path %s is not a directory" % local_path)
    if not os.path.exists(local_path):
        module.fail_json(msg="Local path %s does not exists" % local_path)
    if not os.access(local_path, os.R_OK):
        module.fail_json(msg="Local path %s not readable. Make sure you have the right permissions" % local_path)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type='path', required=True),
            local_path=dict(type='path', required=True),
            server=dict(type='str', required=True),
            port=dict(type='int', required=True),
            recurse=dict(type='bool', default=False),
            archive=dict(type='bool', default=False),
            username=dict(type='str', required=True),
            password=dict(type='str', no_log=True, required=True)
        ),
        supports_check_mode=True
    )

    src = module.params['src']
    local_path = module.params['local_path']
    server = module.params['server']
    username = module.params['username']
    password = module.params['password']
    port = module.params['port']
    archive = module.params['archive']

    changed = False

    check_local_path(module, local_path)

    local_path = os.path.abspath(local_path)
    local_path = os.path.join(local_path, '')
    local_file = local_path + os.path.basename(src)

    skipped = []

    with pysftp.Connection(server,
                           username=username,
                           password=password,
                           port=port) as sftp:

        if os.path.isfile(local_file) and sftp.stat(src).st_mtime == os.stat(local_file).st_mtime:
            skipped.append(src)
        else:
            changed = True

    if changed and not module.check_mode:
        sftp.get(src, local_file, preserve_mtime=True)
        if archive:
            a_path, a_filename = os.path.split(src)
            archive_file = str(a_path + "/Archive/" + a_filename)
            try:
                sftp.rename(src, archive_file)
            except IOError:
                pass

    module.exit_json(src=src, local_file=local_file, skipped=skipped, changed=changed)


if __name__ == '__main__':
    main()
