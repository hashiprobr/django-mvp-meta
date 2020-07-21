#!/usr/bin/env python

import os
import subprocess
import sys

from getpass import getpass


def main():
    ran = False

    if sys.argv.count('%') == 1:
        index = sys.argv.index('%')

        vars = sys.argv[1:index]
        args = sys.argv[(index + 1):]

        if vars and args:
            ran = True

            for var in vars:
                os.environ[var] = getpass(var + '=')

            subprocess.check_call(args)

    if not ran:
        print('Usage: vars % args')


if __name__ == '__main__':
    main()
