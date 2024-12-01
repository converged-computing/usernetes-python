from usernetes.runner import UsernetesRunner


def main(args, _):
    runner = UsernetesRunner(workdir=args.workdir)
    runner.down()
