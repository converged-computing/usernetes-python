from usernetes.runner import UsernetesRunner


def main(args, _):
    runner = UsernetesRunner(workdir=args.workdir)
    runner.wait_for_workers(args.worker_count)
    # We assume that new workers need a sync
    runner.sync_external_ip()
