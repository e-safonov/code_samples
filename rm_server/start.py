import sys
import time
import tempfile
import daemon
import server
import signal


class ServerDaemon(daemon.Daemon):
    def __init__(self, pidfile):
        self.pidfile = pidfile
        daemon.Daemon.__init__(
            self,
            self.pidfile,
            stderr = '/dev/null',
            stdout = '/dev/null',
            stdin = '/dev/null'
        )
        self.working = False
        self.srv = None

    def run(self):
        self.working = True
        self.srv = server.RiskManagerServer()
        while self.working:
            self.srv.check_units()  # Checking units
            time.sleep(0.5)

    def finalize(self, signo, arg):
        print("Stopping run() and close sockets..")
        self.working = False
        if self.srv:
            self.srv.th_pull.stop()
            for address in self.srv.pushers:
                self.srv.pushers[address].pusher_finalize()
            self.srv.pushers.clear()
        exit()


if __name__ == "__main__":
    pidfile = tempfile.gettempdir() + '/MRM_daemon.pid'
    srv_daemon = ServerDaemon(pidfile)
    signal.signal(signal.SIGTERM, srv_daemon.finalize)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            print('Daemon starting..')
            srv_daemon.start()
            print('Daemon started!')
        elif 'stop' == sys.argv[1]:
            print('Daemon stopping..')
            srv_daemon.stop()
            print('Daemon stopped!')
        elif 'restart' == sys.argv[1]:
            print('Daemon restarting..')
            srv_daemon.restart()
            print('Daemon restarted!')
        else:
            print('Unknown command')
            sys.exit(2)
        sys.exit(0)
    else:
        print('usage: %s start|stop|restart' % sys.argv[0])
        sys.exit(2)
