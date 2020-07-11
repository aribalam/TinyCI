import argparse
from socketserver import ThreadingTCPServer
import socket
import threading
import time


def runner_checker(server):

    # function to remove the runner and its assigned commit from the server
    def manage_commit_lists(runner):
        for commit, assigned_runner in server.dispatched_commits.iteritems():
            if assigned_runner == runner:
                del server.dispatched_commits[commit]
                server.pending_commits.append(commit)
            server.runners.remove(runner)

    while not server.dead:
        time.sleep(1)
        # Ping each runners to see if its running
        for runner in server.runners:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                response = helpers.communicate(runner["host"], int(runner["port"]), "ping")
                # remove the runner and its commit if no response
                if response != "pong":
                    print("removing runner %s" % runner)
                    manage_commit_lists(runner)
            # remove the runner and its commit in case of any socket exceptions
            except socket.error as e:
                manage_commit_lists(runner)


def redistribute(server):
    while not server.dead:
        # dispatch all pending commits
        for commit in server.pending_commits:
            print("runnning redistribute")
            print(server.pending_commits)
            dispatch_tests(server, commit)
            time.sleep(5)

def serve():
    parser = argparse.ArgumentParser()
    # add arguments for dispacher's host and port
    parser.add_argument("--host",
                        help="dispatcher's host, by default it is localhost",
                        default="localhost",
                        action="store")
    parser.add_argument("--port",
                        help="dispatcher's port, by default it is 8888",
                        default=8888,
                        action="store")
    args = parser.parse_args()

    # start a new server
    server = ThreadingTCPServer((args.host, int(args.port)), DispatcherServer)
    print("Serving on %s:%s" % (args.host, int(args.port)))

    # spawn 2 threads for runner and redistributor
    runner_heartbeat = threading.Thread(target=runner_checker, args=(server,))
    redistributor = threading.Thread(target=redistribute, args=(server,))

    try:
        runner_heartbeat.start()
        redistributor.start()
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl+C or Cmd+C
        server.serve_forever()
    except (KeyboardInterrupt, Exception):
        # if any exception occurs, kill the thread
        server.dead = True
        runner_heartbeat.join()
        redistributor.join()