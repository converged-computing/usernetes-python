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
        dest="debug",
        help="use verbose logging to debug.",
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
    for start in [start_worker, start_control]:
        start.add_argument(
            "config",
            help="config file (defaults to usernetes release)",
            default=defaults.compose_file,
        )
        start.add_argument(
            "--workdir",
            help="working directory with docker-compose.yaml",
            default=defaults.usernetes_root,
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
    try:
        main(args, extra)
    except:
        help(1)


if __name__ == "__main__":
    run_usernetes()
