import argparse


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