# -*- coding: utf-8 -*-
"""
@author: Хохломин Роман, Сафонов Евгений
"""
import zlib
import zmq
from errno import EAGAIN

from zmq.utils import jsonapi

CONTEXT = zmq.Context()
error_cb = None


def connect_socket(socket_type, address):
    socket = CONTEXT.socket(socket_type)
    socket.connect(address)
    return socket


def bind_socket(socket_type, bind_address = "127.0.0.1", bind_port = None):
    socket = CONTEXT.socket(socket_type)
    address = "tcp://"+bind_address
    if bind_port:
        address = "{0}:{1}".format(address, bind_port)
        socket.bind(address)
    else:
        port = socket.bind_to_random_port(address)
        address = "{0}:{1}".format(address, port)
    return (socket, address)

def validIP(address):
    parts = address.split(".")
    if len(parts) != 4:
        return False
    try:
        for item in parts:
            if not 0 <= int(item) <= 255:
                return False
    except:
        return False
    return True


class Client:
    class ClientError(Exception):
        pass

    def client_initialize(self, address):
        self.address = address
        try:
            self.socket = connect_socket(zmq.REQ, address)
            self.socket.setsockopt(zmq.LINGER, 0)
            print("\x1b[1;32mClient connected..\x1b[0m "+self.address)
        except Exception as e:
            raise self.ClientError(str(e))

    def client_finalize(self):
        self.socket.close()

    def client_request(self, message):
        self.socket.send_json(message)
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)
        if poller.poll(5000):
            response = self.socket.recv_json()
            if response[0] == 'ok':
                return response[1:]
            else:
                raise self.ClientError(response[1])
        else:
            raise self.ClientError('Client connection timeout!')


class Subscriber:
    def __init__(self, callback):
        self.callback = callback

    def subscriber_initialize(self, key, address):
        self.socket = connect_socket(zmq.SUB, address)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, key)
        print("\x1b[1;32mSubscriber connected..\x1b[0m "+str(key)+" "+address)

    def subscriber_finalize(self):
        self.socket.close()

    def subscriber_routine(self):
        try:
            key = self.socket.recv(zmq.NOBLOCK)
            message = self.socket.recv_json()
            self.callback(key, message)
        except zmq.ZMQError as ez:
            if ez.errno != EAGAIN:
                msg = '\x1b[31mSubs ZMQ err#\x1b[0m'+str(ez.errno)+': '+str(ez)
                print(msg)
                if error_cb: error_cb(msg)
            pass
        except Exception as e:
            msg = '\x1b[31mSubs err:\x1b[0m'+str(e)
            print(msg)
            if error_cb: error_cb(msg)
            pass


class Puller:

    def __init__(self, callback, zcompressed = False):
        self.callback = callback if not zcompressed else lambda n, x: callback(n, zlib.decompress(x))
        self.socket = None

    def puller_initialize(self, address = "127.0.0.1", port = None):
        self.socket, self.address = bind_socket(zmq.PULL, address, port)
        self.socket.setsockopt(zmq.LINGER, 0)
        print("\x1b[1;32mPuller connected..\x1b[0m "+self.address)

    def puller_finalize(self):
        if self.socket is not None: self.socket.close()

    def puller_routine(self):
        try:
            message = self.socket.recv(zmq.NOBLOCK)
            self.callback(int(self.address[-1]), message)
        except zmq.ZMQError as ez:
            if ez.errno != EAGAIN:
                msg = '\x1b[31mPuller ZMQ err#\x1b[0m'+str(ez.errno)+': '+str(ez)
                print(msg)
                if error_cb:
                    error_cb(msg)
            pass
        except Exception as e:
            msg = "\x1b[31mError in Puller:\x1b[0m"+str(e)
            print(msg)
            import traceback
            traceback.print_exc()

class Pusher(object):
    class PusherError(Exception): pass

    def __init__(self):
        self.socket = None

    def pusher_initialize(self, address):
        self.socket = connect_socket(zmq.PUSH, address)
        self.socket.setsockopt(zmq.LINGER, 0)
        print("\x1b[1;32mPusher trying to connect..\x1b[0m "+address)

    def pusher_finalize(self):
        if self.socket is not None: self.socket.close()

    def send(self, message):
        self.socket.send(message)

    def send_multipart_string(self, msg1, msg2):
        self.socket.send_string(u = msg1, flags = zmq.SNDMORE)
        self.socket.send_string(u = msg2)

    def send_json(self, message):
        self.socket.send_json(message)

    def send_zcompressed(self, message):
        self.socket.send(zlib.compress(jsonapi.dumps(message)))
