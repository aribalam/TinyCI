import argparse
from socketserver import ThreadingTCPServer
import socket
import threading
import time
import re
import os


class ThreadingTCPServer(SocketServer.ThreadingMixin, SocketServer.TCPServer):
    runners = []
    dead = False
    dispatched_commits = {}
    pending_commits = []


class DispatchHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our dispatcher.
    This will dispatch test runners against the incoming commit
    and handle their requests and test results
    """
    command_re = re.compile(r"(\w+)(:.+)*")
    BUF_SIZE = 1024

    def handle(self):
        self.data = self.request.recv(self.BUF_SIZE).strip()
        command_groups = self.command_re.math(self.data)
        if not command_groups:
            self.request.sendall("invalid data")
            return
        command = command_groups.group(1)

        if command == "status":
            print("In Status")
            self.request.sendall("OK")

        elif command == "register":
            print("Register")
            address = command_groups.group(2)
            host, port = re.findall(r":(\w*)", address)
            runner = {"host": host, "port": port}
            self.server.runners.append(runner)
            self.request.sendall("OK")

        elif command == "dispatch":
            print("going to dispatch")
            commit_id = command_groups.group(2)[1:]
            if not self.server.runners:
                self.request.sendall("No runners are registered")
            else:
                self.request.sendall("OK")
                dispatch_tests(self.server, commit_id)

        elif command == "results":
            print("got test results")
            results = command_groups.group(2)[1:]
            results = results.split(":")
            commit_id = results[0]
            length_msg = int(results[1])
            # 3 is the number of ":" in the sent command
            remaining_buffer = self.BUF_SIZE - (len(command) + len(commit_id) + len(results[1]) + 3)
            if length_msg > self.BUF_SIZE:
                self.data += self.request.recv(length_msg - remaining_buffer).strip()
            del self.server.dispatched_commits[commit_id]

            if not os.path.exists("test_results"):
                os.makedirs("test_results")
            with open("test_results/%s" % commit_id, "w") as f:
                data = self.data.split(":")[3:]
                data = "\n".join(data)
                f.write(data)
            self.request.sendall("OK")


def dispatch_tests(server, commit_id):
    #NOTE: We usually dont run this forever
    while True:
        print("trying to dispatch to runners")
        for runner in server.runners:
            response = helpers.communicate(runner["host"],
                                           int(runner["port"]),
                                           "runtest:%s" % commit_id)
            # when a connection is established with the runner
            if response == "OK":
                print("Adding commit: %s" % commit_id)
                # add the commit to the dispatched commits
                server.dispatched_commit[commit_id] = runner
                # remove from the pending commits
                if commit_id in server.pending_commits:
                    server.pending_commits.remove(commit_id)
                return

        time.sleep(2)

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