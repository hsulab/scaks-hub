#!/usr/bin/env python
# -*- coding: utf-8 -*-

# View functions for microkinetics model building.

import os
from collections import namedtuple
from datetime import datetime

from flask import request
from flask import render_template, url_for
from flask import make_response, send_file, redirect, abort

from . import main
from .errors import PathError
from .utils import file_mtime, file_ctime, file_size

# Global variables.
CODE_SUFFIXES = dict(py='python',
                     c='c',
                     cpp='c',
                     html='html',
                     css='css',
                     js='javascript',
                     h='c',
                     conf='text',
                     txt='text',
                     json='javascript')

TEXT_SUFFIXES = dict(conf='text',
                     txt='text',
                     md='text',
                     log='text')

ZIP_SUFFIXES = ['zip', 'rar', 'tar', 'tgz', '7z', 'gz']

FILE_SUFFIXES = {**CODE_SUFFIXES, **TEXT_SUFFIXES}


# --------------------------------------------------------
# Utility functions.
# --------------------------------------------------------

def get_links_paths(full_path, path):
    ''' Get all accumulate links and subdirs for a given path.
    '''
    if path:
        if not os.path.exists(full_path):
            raise PathError('No such file or directory: {}'.format(full_path))
        path = [subdir for subdir in path.split('/') if subdir]

        # Links for each subdir in path information.
        path_links = []
        base_link = url_for('main.filetree')[:-1]
        accumulate_link = base_link
        for subdir in path:
            accumulate_link += ('/' + subdir)
            path_links.append(accumulate_link)
        links_paths = zip(path_links, path)
    else:
        links_paths = []

    return links_paths


# --------------------------------------------------------
# Flask view functions.
# --------------------------------------------------------

@main.route('/')
def index():
    return redirect(url_for('main.filetree'))

@main.route('/files/', defaults={'path': ''})
@main.route('/files/<path:path>')
def filetree(path):
    # Parameters passed to template.
    locs = {}

    # Activate navigation tab.
    locs['files'] = 'active'

    # Current path information.
    base_path = os.getcwd()
    full_path = '{}/{}'.format(base_path, path)

    # Path information.
    locs['links_paths'] = get_links_paths(full_path, path)
    locs['path'] = path

    # Show file tree.
    if os.path.isdir(full_path):
        # File list.
        dirs_files  = os.listdir(full_path)
        dirs = [i for i in dirs_files if os.path.isdir('{}/{}'.format(full_path, i))]
        files = [i for i in dirs_files if os.path.isfile('{}/{}'.format(full_path, i))]

        url = request.url.strip('/')

        # Store information for each item in file table.
        FileItem = namedtuple('FileItem', ['name', 'link', 'mtime'])

        dir_items = []
        for dir in sorted(dirs):
            link = '{}/{}'.format(url, dir)
            mtime = file_mtime('{}/{}'.format(full_path, dir))
            dir_item = FileItem._make([dir, link, mtime])
            dir_items.append(dir_item)

        file_items = []
        for file in sorted(files):
            link = '{}/{}'.format(url, file)
            mtime = file_mtime('{}/{}'.format(full_path, file))
            file_item = FileItem._make([file, link, mtime])
            file_items.append(file_item)

        locs['file_items'], locs['dir_items'] = file_items, dir_items

        # File types.
        locs['code_suffixes'] = CODE_SUFFIXES
        locs['text_suffixes'] = TEXT_SUFFIXES
        locs['zip_suffixes'] = ZIP_SUFFIXES

        # Previous link.
        if path:
            locs['prev_link'] = '/'.join(url.split('/')[: -1])
        else:
            locs['prev_link'] = None

        return render_template('files/file_tree.html', **locs)
    else:
        file_suffix = full_path.split('.')[-1]

        # Show text file content.
        if file_suffix in FILE_SUFFIXES:
            with open(full_path, 'r') as f:
                file_content = f.read()
            locs['file_content'] = file_content
            locs['file_type'] = FILE_SUFFIXES[file_suffix]
            locs['mtime'] = file_mtime(full_path)
            locs['filesize'] = file_size(full_path)
            locs['filename'] = full_path.split('/')[-1]
            return render_template('files/file_content.html', **locs)
        # Download the file.
        else:
            response = make_response(send_file(full_path))
            filename = full_path.split('/')[-1]
            response.headers["Content-Disposition"] = "attachment; filename={};".format(filename)
            return response

