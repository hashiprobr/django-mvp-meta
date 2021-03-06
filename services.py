#!/usr/bin/env python

import json
import os
import shutil
import subprocess
import sys

from subprocess import PIPE, CalledProcessError


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


def run_compose(dir, args):
    subprocess.run(compose(dir, args), check=True)


def is_up(dir):
    process = subprocess.run(compose(dir, ['ps']), check=True, stdout=PIPE)

    for line in process.stdout.decode().strip().split('\n')[2:]:
        words = line.strip().split()

        if words:
            return True

    return False


def set_up(dir, args):
    run_compose(dir, ['up', *args])


def tear_set(dir, args):
    run_compose(dir, ['restart', *args])


def tear_down(dir, args):
    run_compose(dir, ['down', *args])


def build(args):
    run_compose(TEST_DIR, ['build', 'web', *args])


def mc(args):
    try:
        run_compose(ADMIN_DIR, ['run', 'filestore', *args])
    except CalledProcessError:
        pass


def dev(args):
    if os.path.exists(DEV_DIR):
        if is_up(DEV_DIR):
            print('Development environment already running')
        elif is_up(TEST_DIR):
            print('Testing environment is running')
        else:
            set_up(DEV_DIR, args)
    else:
        print('Development environment not available')


def test(args):
    if is_up(TEST_DIR):
        print('Testing environment already running')
    elif os.path.exists(DEV_DIR) and is_up(DEV_DIR):
        print('Development environment is running')
    else:
        build([])

        set_up(TEST_DIR, args)


def restart(args):
    if os.path.exists(DEV_DIR) and is_up(DEV_DIR):
        tear_set(DEV_DIR, args)
    elif is_up(TEST_DIR):
        tear_set(TEST_DIR, args)
    else:
        print('No environment is running')


def down(args):
    if os.path.exists(DEV_DIR) and is_up(DEV_DIR):
        tear_down(DEV_DIR, args)
    elif is_up(TEST_DIR):
        tear_down(TEST_DIR, args)
    else:
        print('No environment is running')


def remotemanage(args):
    if is_up(TEST_DIR):
        if 'test' in args:
            path = 'minio/media-test'
            mc(['mb', path])
            mc(['policy', 'set', 'download', path + '/public'])
        else:
            path = None

        command = ['exec']

        if 'createsuperuser' not in args:
            command.append('-T')

        try:
            run_compose(TEST_DIR, [*command, 'web', './manage.py', *args])
        finally:
            if path is not None:
                mc(['rb', path, '--force'])
    else:
        print('Testing environment not running')


def localmanage(args):
    if 'collectstatic' in args:
        if is_up(TEST_DIR):
            mc(['mb', 'minio/static'])
            mc(['policy', 'set', 'download', 'minio/static'])
            mc(['mb', 'minio/media'])
            mc(['policy', 'set', 'download', 'minio/media/public'])
        else:
            print('Testing environment not running')

    try:
        prodmanage(args)
    finally:
        if 'test' in args:
            path = os.path.join('dev', 'filestore', 'media-test')
            try:
                shutil.rmtree(path)
            except FileNotFoundError:
                pass


def prodmanage(args):
    subprocess.run(['./manage.py', *args], check=True, cwd=os.environ['BASE_DIR'])


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

        with open('versions.json') as file:
            data = json.load(file)

        for key, value in data.items():
            os.environ[key.upper() + '_VERSION'] = value

        os.environ['BASE_DIR'] = base_dir
        os.environ['BASE_NAME'] = base_name

        try:
            subcommands[sys.argv[1]](sys.argv[2:])
        except CalledProcessError as error:
            sys.exit(error.returncode)


if __name__ == '__main__':
    main()
