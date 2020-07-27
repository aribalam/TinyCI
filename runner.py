import time
import socket
import socketserver as SocketServer


def dispatcher_server(server):
    while not server.added:
        time.sleep(5)
    if (time.time() - server.last_communication) > 10:
        try:
            response = helpers.communicate(
                server.dispatcher_server["host"],
                int(server.dispatcher_server["port"]),
                "status"
            )
            if response != "OK":
                print("Dispatcher is no longer functional")
                server.shutdown()
                return
        except socket.error as e:
            print("Cant communicate with dispatcher %s" % e)
            server.shutdown()
            return


class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    dispatcher_server = None
    last_communication = None
    busy = False
    dead = False
