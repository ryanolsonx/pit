import argparse
import hashlib
import os
import sys


GIT_DIR = ".pit"


def cat_file(args):
    sys.stdout.flush()
    with open(os.path.join(GIT_DIR, "objects", args.object), "rb") as f:
        data = f.read()
    sys.stdout.buffer.write(data)


def hash_object(args):
    with open(args.file, "rb") as f:
        data = f.read()
        oid = hashlib.sha1(data).hexdigest()
    path = os.path.join(GIT_DIR, "objects", oid)
    with open(path, "wb") as out:
        out.write(data)
    print(oid)


def init(args):
    cwd = os.getcwd()
    os.makedirs(GIT_DIR)
    os.makedirs(os.path.join(GIT_DIR, "objects"))
    print(f"Initialized empty pit repository in {cwd}/{GIT_DIR}")


def parse_args():
    parser = argparse.ArgumentParser()

    cmds = parser.add_subparsers(dest="command")
    cmds.required = True

    init_parser = cmds.add_parser("init")
    init_parser.set_defaults(func=init)

    hash_object_parser = cmds.add_parser("hash-object")
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument("file")

    cat_file_parser = cmds.add_parser("cat-file")
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument("object")

    return parser.parse_args()


def main():
    args = parse_args()
    args.func(args)
    
