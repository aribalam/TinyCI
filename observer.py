import argparse
import subprocess
import os
import time


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

        # check if file exists (a new commit has been made)
        if os.path.isfile(".commit_id"):
            try:
                # try to setup a connection with the dispatcher
                response = helpers.communicate(dispatcher_host, int(dispatcher_port), "status")
            except socket.error as e:
                raise Exception("Could not communicate with dispatcher server: %s" % e)

            # send the commit id to the dispatcher server
            if response == "OK":
                commit = ""
                with open(".commit_id", "r") as f:
                    commit = f.readline()
                response = helpers.communicate(dispatcher_host, int(dispatcher_port), "dispatch:%s" % commit)

                # raise error if failed to send commit id
                if response != "OK":
                    raise Exception("Could not dispatch commit: %s" % response)

                print("Dispatched!")

            else:
                raise Exception("Could not dispatch: %s" % response)

        time.sleep(5)