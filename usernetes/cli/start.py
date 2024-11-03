from usernetes.runner import UsernetesRunner


def main(args, _):
    runner = UsernetesRunner(args.config, workdir=args.workdir)
    if args.command == "start-worker":
        runner.start_worker(args)
    else:
        runner.start_control_plane(args)
