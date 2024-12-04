#!/usr/bin/env python

import argparse
import os
import sys

import usernetes
import usernetes.defaults as defaults
from usernetes.logger import setup_logger


def get_parser():
    parser = argparse.ArgumentParser(
        description="Usernetes Python",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Global Variables
    parser.add_argument(
        "--debug",
        help="use verbose logging to debug.",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--develop",
        help="Don't wrap main in a try except (allow error to come through)",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--quiet",
        dest="quiet",
        help="suppress additional output.",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--version",
        dest="version",
        help="show software version.",
        default=False,
        action="store_true",
    )

    subparsers = parser.add_subparsers(
        help="actions",
        title="actions",
        description="actions",
        dest="command",
    )
    subparsers.add_parser("version", description="show software version")
    start_worker = subparsers.add_parser(
        "start-worker",
        formatter_class=argparse.RawTextHelpFormatter,
        description="start user-space Kubernetes worker (akin to 'up')",
    )
    start_control = subparsers.add_parser(
        "start-control-plane",
        formatter_class=argparse.RawTextHelpFormatter,
        description="start user-space Kubernetes control plane (akin to 'up')",
    )
    start_control.add_argument(
        "--serial",
        help="Serial execution mode (do not wait for workers to come up)",
        action="store_true",
        default=False,
    )
    down = subparsers.add_parser(
        "down",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Bring down a node",
    )
    wait = subparsers.add_parser(
        "wait-workers",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Wait for workers and sync ip address when ready.",
    )
    # Env and attributes are obtainable from the instance.
    # E.g., we assume we can run flux getattr and similar.
    attribute = subparsers.add_parser(
        "attr",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Derive attributes",
    )
    envars = subparsers.add_parser(
        "env",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Derive environment variables",
    )
    for command in [attribute, envars]:
        command.add_argument(
            "attributes",
            action="append",
            default=[],
            help="Return (by default) kubeconfig and workdir",
        )
    clean = subparsers.add_parser(
        "clean",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Clean the worker cache (to prepare for another job)",
    )
    clean.add_argument(
        "--keep-node",
        dest="keep_node",
        help="Do not remove the node (requires keeping the workdir)",
    )
    for command in [start_control, clean]:
        command.add_argument(
            "--all",
            dest="clean_all",
            help="Also remove the entire usernetes root (not just worker cache)",
            action="store_true",
            default=False,
        )
    for command in [start_worker, start_control, wait, down, clean]:
        command.add_argument(
            "--workdir",
            help="working directory with docker-compose.yaml",
        )
    for command in [start_control, wait]:
        command.add_argument(
            "--worker-count",
            help="worker count (not including control plane)",
        )
    return parser


def run_usernetes():
    """
    this is the main entrypoint.
    """
    parser = get_parser()

    def help(return_code=0):
        """print help, including the software version and active client
        and exit with return code.
        """
        version = usernetes.__version__

        print("\nUsernetes Python v%s" % version)
        parser.print_help()
        sys.exit(return_code)

    # If the user didn't provide any arguments, show the full help
    if len(sys.argv) == 1:
        help()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    if args.debug is True:
        os.environ["MESSAGELEVEL"] = "DEBUG"

    # Show the version and exit
    if args.command == "version" or args.version:
        print(usernetes.__version__)
        sys.exit(0)

    setup_logger(
        quiet=args.quiet,
        debug=args.debug,
    )

    # Here we can assume instantiated to get args
    if args.command in ["start-worker", "start-control-plane"]:
        from .start import main
    elif args.command == "down":
        from .down import main
    elif args.command == "wait-workers":
        from .wait import main
    elif args.command == "clean":
        from .clean import main
    elif args.command == "attr":
        from .environment import attr_main as main
    elif args.command == "env":
        from .environment import env_main as main

    # Develop mode, akin to commenting out the try/except below
    if args.develop:
        return main(args, extra)
    try:
        main(args, extra)
    except:
        help(1)


if __name__ == "__main__":
    run_usernetes()
