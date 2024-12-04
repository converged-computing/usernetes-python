from usernetes.runner import UsernetesRunner


def main(args, _):
    runner = UsernetesRunner(workdir=args.workdir)
    runner.clean(cache_only=not args.clean_all, keep_nodes=args.keep_node)
