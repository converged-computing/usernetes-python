# These functions for environment and attributes assume
# being in a flux instance, and also assume it is created
# in the user temporary directory.
import os

import usernetes.instance as iutils


def attributes(contenders):
    """
    Return unique (or default) attributes.
    """
    contenders = list(set(contenders))
    if not contenders:
        contenders = ["kubeconfig", "workdir"]
    return contenders


def attr_main(args, _):
    """
    Get (and print) one or more attributes
    """
    instance = iutils.InstanceAttributes()
    for name in attributes(args.attributes):
        attribute = getattr(instance, name, None)
        if not attribute:
            continue
        print(attribute)


def env_main(args, _):
    """
    Get (and print) one or more envars
    """
    instance = iutils.InstanceAttributes()
    attribute_set = attributes(args.attributes)
    if "kubeconfig" in attribute_set:
        print(f"export KUBECONFIG={instance.kubeconfig}")
    if "workdir" in args.attributes:
        print(f"export USERNETES_WORKDIR={instance.workdir}")
