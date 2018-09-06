#!/usr/bin/env python3
import os
import sys


def main():
    path_to_binary = sys.argv[1]
    path_to_firmware_root = sys.argv[2]
    rel_path = os.path.relpath(path_to_binary, path_to_firmware_root)
    print('/{}'.format(rel_path))


if __name__ == '__main__':
    sys.exit(main())
