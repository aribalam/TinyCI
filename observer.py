import argparse
import subprocess


def poll():
    parser = argparse.ArgumentParser()
    # Add argument to retrieve the dispatcher host and port
    parser.add_argument("--dispatcher-parser",
                        help="specify the dispatcher server host:port, "\
                        "by default it uses localhost:8888",
                        default="localhost:8888",
                        action="store")

    # add argument to get the target repo name
    parser.add_argument("repo", metavar="repo", type=str, help="specify the target repository")

    args = parser.parse_args()
    dispatcher_host, dispatcher_port = args.dispatcher_parser.split(":")

    while True:
        try:
            # try calling a bash script to detect any changes in the repo
            # Any new commit made will be added to a .commit_id file in the current working directory
            subprocess.check_output(["./update_repo.sh", args.repo])
        except subprocess.CalledProcessError as e:
            raise Exception("Could not update and check repository: " + "Reason: %s" % e.output)
