#!/usr/bin/env python

# These are functions specific to flux instances.

import argparse

import flux
from flux import kvs


def get_parser():
    parser = argparse.ArgumentParser(
        description="Usernetes-Flux Python",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--develop",
        help="Don't wrap main in a try except (allow error to come through)",
        default=False,
        action="store_true",
    )
    subparsers = parser.add_subparsers(
        help="actions",
        title="actions",
        description="actions",
        dest="command",
    )
    broker = subparsers.add_parser(
        "broker",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Interact with the broker of the current instance",
    )
    top_level = subparsers.add_parser(
        "top-level",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Interact with the top level instance",
    )
    for command in [top_level, broker]:
        command.add_argument(
            "--getattr",
            dest="get_attribute",
            help="Get a broker attribute",
        )
        command.add_argument(
            "--setkvs",
            dest="set_kvs",
            help="Set an key value store attribute",
        )
        command.add_argument(
            "--getkvs",
            dest="get_kvs",
            help="Get n key value store attribute",
        )
    return parser


def find_root(handle):
    """
    Given a handle, recurse up to root handle (and return it)
    """
    while True:
        try:
            parent_uri = handle.attr_get("parent-uri")
            handle = flux.Flux(parent_uri)
        # We will get an ENOENT exception when we reach the top level
        except:
            break
    return flux.Flux(handle.attr_get("local-uri"))


def run_main():
    """
    this is the main entrypoint.
    """
    parser = get_parser()
    args, extra = parser.parse_known_args()
    handle = flux.Flux()

    # Are we asking for a parent?
    if args.command == "top-level":
        handle = find_root(handle)

    # The user wants to get (and print) an attribute
    # This will also ENOENT if does not exist
    if args.get_attribute is not None:
        try:
            print(handle.attr_get(args.get_attribute))
        except FileNotFoundError:
            pass

    # The user wants to get/set kvs
    if args.get_kvs:
        # ENOENT if does not exist
        try:
            print(kvs.get(handle, args.get_kvs))
        except FileNotFoundError:
            pass

    if args.set_kvs:
        key, value = parse_pair(args.set_kvs)
        set_kvs(handle, key, value)


def parse_pair(pair):
    """
    Split based on =, required.
    """
    if "=" not in pair:
        raise ValueError("Please provide --setkvs value as <key>=<value>")
    return pair.split("=", 1)


def set_kvs(handle, key, value):
    """
    Set a kvs value for a handle
    """
    kvs.put(handle, key, value)
    return kvs.commit(handle)


if __name__ == "__main__":
    run_main()
