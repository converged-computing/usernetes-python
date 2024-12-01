from usernetes.runner import UsernetesRunner


def main(args, _):
    runner = UsernetesRunner(workdir=args.workdir)
    if args.command == "start-worker":
        runner.start_worker()
    else:
        if not args.worker_count:
            raise ValueError("A --worker-count is required.")
        runner.start_control_plane(args.worker_count, serial=args.serial)
