from threading import Thread, Event
from time import sleep
import logging

logger = logging.getLogger(__name__)

class PyTPThread(Thread):

    def __init__(self, daemon = True, rest_interval = None):
        self.REST_INTERVAL = rest_interval or 4e-2
        Thread.__init__(self)
        self.daemon = daemon
        self.interrupted = True
        self.__initialize_done = Event()
        self.__finalize_result = None
        self.initializers = []
        self.finalizers   = []
        self.routines     = []

    def start(self):
        self.interrupted = False
        Thread.start(self)
        self.__initialize_done.wait()
        result = self.__initialize_result
        if isinstance(result, Exception):
            raise result
        return result

    def stop(self, join = True):
        self.interrupted = True
        if join:
            self.join()
            return self.__finalize_result

    def thread_initialize(self):
        """Метод, который вызывается новым потоком, перед основным циклом."""
        return [i() for i in self.initializers]

    def thread_finalize(self):
        """Метод, который вызывается новым потоком, после прерывания."""
        return [f() for f in self.finalizers]

    def thread_routine(self):
        """Метод, который вызывается новым потоком, после прерывания."""
        return [r() for r in self.routines]

    def run(self):
        try:
            self.__initialize_result = self.thread_initialize()
            self.__initialize_done.set()
            while not self.interrupted:
                try:
                    self.thread_routine()
                except Exception as e:
                    logger.error("Thread error: ", str(e))
                finally:
                    sleep(self.REST_INTERVAL)
        except Exception as e:
            self.__initialize_result = e
            self.__initialize_done.set()
        finally:
            self.__finalize_result = self.thread_finalize()

def run_threads(threads = (), routines = ()):
    for t in threads:
        t.start()
