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
    subparsers = parser.add_subparsers(
        help="actions",
        title="actions",
        description="actions",
        dest="command",
    )
    ports = subparsers.add_parser(
        "ports",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Retrieve a list of ports in the range 30,000–32,767",
    )
    ports.add_argument(
        "-N",
        "--number",
        dest="number",
        type=int,
        help="Number of ports to get",
    )
    ports.add_argument(
        "--min",
        dest="minimum_range",
        type=int,
        default=30000,
        help="Minimum of range to use",
    )
    ports.add_argument(
        "--max",
        dest="maximum_range",
        type=int,
        default=32767,
        help="Maximum of range to use",
    )
    ports.add_argument(
        "--reset",
        default=False,
        action="store_true",
        help="Reset ports counter"
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


def next_port(options):
    for port in range(options):
        yield port


def derive_ports(handle, args):
    """
    Given a number, minimum range and max, derive a set of ports.

    We then set the last port used on the lead (top level) broker so we don't use them again.
    """
    # kvs key for the last used port
    port_key = "usernetes_last_used_port"    
    if args.reset:
        set_kvs(handle, port_key, None)
        return
    
    # We store metadata at the root
    handle = find_root(handle)
    minimum = args.minimum_range
    maximum = args.maximum_range
    last_used = get_kvs(handle, port_key)
    if last_used is not None:
        minimum = last_used
    if minimum >= maximum:
        raise ValueError(f"Minimum {minimum} cannot be >= maximum {maximum}")
    options = range(minimum, maximum)
    if len(options) < args.number:
        raise ValueError(
            f"Not enough ports left in instance to use. Need {args.number} and have {len(options)}"
        )

    # Custom function to get ports
    def get_ports(minimum, maximum, N):
        count = 0
        for i in range(minimum, maximum):
            yield i
            count += 1
            if count >= N:
                return

    for port in get_ports(minimum, maximum, args.number):
        print(port)

    # Set the kvs to be the next port that isn't used yet
    set_kvs(handle, port_key, port + 1)


def run_main():
    """
    this is the main entrypoint.
    """
    parser = get_parser()
    args, extra = parser.parse_known_args()
    handle = flux.Flux()

    if not args.command:
        parser.print_help()
        return

    # We want to get one or more ports
    if args.command == "ports":
        return derive_ports(handle, args)

    # Are we asking for a parent?
    if args.command == "top-level":
        handle = find_root(handle)

    # The user wants to get (and print) an attribute
    # This will also ENOENT if does not exist
    if args.get_attribute is not None:
        value = get_attribute(handle, args.get_attribute)
        if value is not None:
            print(value)

    # The user wants to get/set kvs
    if args.get_kvs:
        value = get_kvs(handle, args.get_kvs)
        if value is not None:
            print(value)

    if args.set_kvs:
        key, value = parse_pair(args.set_kvs)
        set_kvs(handle, key, value)


def get_attribute(handle, name):
    """
    Wrapper to get an attribute that allows failure
    """
    try:
        return handle.attr_get(args.get_attribute)
    except FileNotFoundError:
        pass


def get_kvs(handle, key):
    """
    Wrapper to get_kvs that allows for failure

    (when the key does not exist)
    """
    # ENOENT if does not exist
    try:
        return kvs.get(handle, key)
    except FileNotFoundError:
        pass


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
