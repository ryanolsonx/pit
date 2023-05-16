import argparse
import hashlib
import os
import sys


GIT_DIR = ".pit"
HEAD_PATH = f"{GIT_DIR}/HEAD"


def set_head(oid):
    with open(HEAD_PATH, "w") as f:
        f.write(oid)


def get_head():
    if not os.path.isfile(HEAD_PATH):
        return None

    with open(HEAD_PATH) as f:
        return f.read().strip()


def commit(msg):
    commit = f"tree {write_tree()}\n"
    HEAD = get_head()
    if HEAD:
        commit += f"parent {HEAD}\n"
    commit += f"\n{msg}\n"
    
    oid = hash_object(commit.encode(), "commit")

    set_head(oid)
    
    return oid


def commit_cli(args):
    print(commit(args.message))


def is_ignored(path):
    return ".pit" in path.split("/")


def get_object(oid, expected_type = "blob"):
    object_path = os.path.join(GIT_DIR, "objects", oid)
    with open(object_path, "rb") as f:
        obj = f.read()

    type_, _, data = obj.partition(b"\x00")
    type_ = type_.decode()

    if expected_type is not None:
        assert type_ == expected_type, f"Expected {expected_type}, got {type_}"

    return data


def get_tree_entries(oid):
    if not oid:
        return
    tree = get_object(oid, "tree")
    entries = tree.decode().splitlines()
    for entry in entries:
        type_, oid, name = entry.split(" ", 2)
        yield type_, oid, name


def get_tree(oid, base_path=""):
    result = {}
    for type_, oid, name in get_tree_entries(oid):
        assert "/" not in name
        assert name not in ("..", ".")
        path = base_path + name
        if type_ == "blob":
            result[path] = oid
        elif type_ == "tree":
            result.update(get_tree(oid, f"{path}/"))
        else:
            assert False, f"Unknown tree entry {type_}"
    return result;


def empty_current_dir():
    for root, dirnames, filenames in os.walk(".", topdown=False):
        for name in filenames:
            path = os.path.relpath(f"{root}/{name}")
            if is_ignored(path) or not os.path.isfile(path):
                continue
            os.remove(path)
        for name in dirnames:
            path = os.path.relpath(f"{root}/{name}")
            if is_ignored(path):
                continue
            try:
                os.rmdir(path)
            except (FileNotFoundError, OSError):
                pass


def read_tree(tree_oid):
    empty_current_dir()
    tree = get_tree(tree_oid, base_path="./").items()
    for path, oid in tree:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(get_object(oid))


def read_tree_cli(args):
    read_tree(args.tree)


def write_tree(current_dir = "."):
    entries = []
    with os.scandir(current_dir) as dir:
        for entry in dir:
            path = os.path.join(current_dir, entry.name)
            if is_ignored(path):
                continue

            if entry.is_file(follow_symlinks=False):
                type_ = "blob"
                oid = hash_object_from_path(path)
            elif entry.is_dir(follow_symlinks=False):
                type_ = "tree"
                oid = write_tree(path)
            entries.append((entry.name, oid, type_))

    items = [
        f"{type_} {oid} {name}\n"
        for name, oid, type_
        in sorted(entries)
    ]
    tree = "".join(items)

    return hash_object(tree.encode(), "tree")


def write_tree_cli(args):
    print(write_tree())


def cat_file_cli(args):
    sys.stdout.flush()
    oid = args.object
    data = get_object(oid)
    sys.stdout.buffer.write(data)


def hash_object(data, type_ = "blob"):
    obj = type_.encode() + b"\x00" + data
    oid = hashlib.sha1(data).hexdigest()
    obj_path = os.path.join(GIT_DIR, "objects", oid)

    with open(obj_path, "wb") as out:
        out.write(obj)

    return oid


def hash_object_from_path(file_path, type_ = "blob"):
    with open(file_path, "rb") as f:
        data = f.read()

    return hash_object(data, type_)


def hash_object_cli(args):
    file = args.file
    oid = hash_object_from_path(file)
    print(oid)


def init():
    os.makedirs(GIT_DIR)
    object_dir = os.path.join(GIT_DIR, "objects")
    os.makedirs(object_dir)
    cwd = os.getcwd()

    return f"{cwd}/{GIT_DIR}"


def init_cli(args):
    dot_path = init()
    print(f"Initialized empty pit repository in {dot_path}")


def parse_args():
    parser = argparse.ArgumentParser()

    cmds = parser.add_subparsers(dest="command")
    cmds.required = True

    init_parser = cmds.add_parser("init")
    init_parser.set_defaults(func=init_cli)

    hash_object_parser = cmds.add_parser("hash-object")
    hash_object_parser.set_defaults(func=hash_object_cli)
    hash_object_parser.add_argument("file")

    cat_file_parser = cmds.add_parser("cat-file")
    cat_file_parser.set_defaults(func=cat_file_cli)
    cat_file_parser.add_argument("object")

    write_tree_parser = cmds.add_parser("write-tree")
    write_tree_parser.set_defaults(func=write_tree_cli)

    read_tree_parser = cmds.add_parser("read-tree")
    read_tree_parser.set_defaults(func=read_tree_cli)
    read_tree_parser.add_argument("tree")

    commit_parser = cmds.add_parser("commit")
    commit_parser.set_defaults(func=commit_cli)
    commit_parser.add_argument("-m", "--message", required=True)

    return parser.parse_args()


def main():
    args = parse_args()
    args.func(args)
