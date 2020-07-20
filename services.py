#!/usr/bin/env python

import json
import os
import shutil
import subprocess
import sys

from subprocess import CalledProcessError


DEV_DIR = 'dev'

TEST_DIR = 'test'

ADMIN_DIR = 'admin'


def between(parent, child):
    names = []

    for name in os.listdir(parent):
        path = os.path.join(parent, name)

        if os.access(path, os.R_OK) and os.path.isdir(path):
            if child in os.listdir(path):
                names.append(name)

    if len(names) < 1:
        raise FileNotFoundError('Folder with {} not found'.format(child))

    if len(names) > 1:
        raise FileNotFoundError('Multiple folders with {} found'.format(child))

    return names[0]


def compose(dir, args):
    path = os.path.join(dir, 'docker-compose.yml')

    return ['docker-compose', '-f', path, *args]


def compose_call(dir, args):
    subprocess.check_call(compose(dir, args))


def is_up(dir):
    output = subprocess.check_output(compose(dir, ['ps']))

    for line in output.decode('utf-8').strip().split('\n')[2:]:
        words = line.strip().split()

        if words:
            return True

    return False


def set_up(dir, args):
    compose_call(dir, ['up', *args])


def tear_set(dir, args):
    compose_call(dir, ['restart', *args])


def tear_down(dir, args):
    compose_call(dir, ['down', *args])


def build(args):
    compose_call(TEST_DIR, ['build', 'web', *args])


def mc(args):
    try:
        compose_call(ADMIN_DIR, ['run', 'filestore', *args])
    except CalledProcessError:
        pass


def rb(path):
    mc(['rb', path, '--force'])


def rm(path):
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass


def dev(args):
    if is_up(DEV_DIR):
        print('Development environment already running')
    elif is_up(TEST_DIR):
        print('Testing environment is running')
    else:
        set_up(DEV_DIR, args)


def test(args):
    if is_up(TEST_DIR):
        print('Testing environment already running')
    elif is_up(DEV_DIR):
        print('Development environment is running')
    else:
        build([])

        set_up(TEST_DIR, args)


def restart(args):
    if is_up(DEV_DIR):
        tear_set(DEV_DIR, args)
    elif is_up(TEST_DIR):
        tear_set(TEST_DIR, args)
    else:
        print('No environment is running')


def down(args):
    if is_up(DEV_DIR):
        tear_down(DEV_DIR, args)
    elif is_up(TEST_DIR):
        tear_down(TEST_DIR, args)
    else:
        print('No environment is running')


def remotemanage(args):
    if is_up(TEST_DIR):
        if 'test' in args:
            path = 'minio/media-test'
            rb(path)
            mc(['mb', path])
            mc(['policy', 'set', 'download', path + '/public'])
        else:
            path = None

        compose_call(TEST_DIR, ['exec', '-T', 'web', './manage.py', *args])

        if path is not None:
            rb(path)
    else:
        print('Testing environment not running')


def localmanage(args):
    if 'test' in args:
        path = os.path.join('dev', 'filestore', 'media-test')
        rm(path)
    else:
        path = None

    if 'collectstatic' in args:
        if is_up(TEST_DIR):
            mc(['mb', 'minio/static'])
            mc(['policy', 'set', 'download', 'minio/static'])
            mc(['mb', 'minio/media'])
            mc(['policy', 'set', 'download', 'minio/media/public'])
        else:
            print('Testing environment not running')

    prodmanage(args)

    if path is not None:
        rm(path)


def prodmanage(args):
    subprocess.check_call(['./manage.py', *args], cwd=os.environ['BASE_DIR'])


def main():
    subcommands = {f.__name__: f for f in [
        build,
        dev,
        test,
        restart,
        down,
        remotemanage,
        localmanage,
        prodmanage,
    ]}

    if len(sys.argv) < 2 or sys.argv[1] not in subcommands:
        print('Available subcommands: ' + ' '.join(subcommands))
    else:
        base_dir = between('.', 'manage.py')
        base_name = between(base_dir, 'asgi.py')

        with open('versions.json', encoding='utf-8') as file:
            data = json.load(file)

        for key, value in data.items():
            os.environ[key.upper() + '_VERSION'] = value

        os.environ['BASE_DIR'] = base_dir
        os.environ['BASE_NAME'] = base_name

        subcommands[sys.argv[1]](sys.argv[2:])


if __name__ == '__main__':
    main()
