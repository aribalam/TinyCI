import argparse
from socketserver import ThreadingTCPServer
import threading


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