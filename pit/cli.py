import argparse


def init(args):
    print("Hello world")


def parse_args():
    parser = argparse.ArgumentParser()

    cmds = parser.add_subparsers(dest='command')
    cmds.required = True

    init_parser = cmds.add_parser('init')
    init_parser.set_defaults(func=init)

    return parser.parse_args()


def main():
    args = parse_args()
    args.func(args)
    
