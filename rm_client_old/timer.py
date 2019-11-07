from PyQt4 import QtCore


class MyTimer(QtCore.QThread):
    def __init__(self, parent = None):
        QtCore.QThread.__init__(self, parent)

    def run(self):
        while True:
            self.sleep(1)
            self.emit(QtCore.SIGNAL("MyTimer()"))
