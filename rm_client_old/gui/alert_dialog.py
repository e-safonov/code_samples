from PyQt4 import QtGui, QtCore


class AlertDialog(QtGui.QDialog):
    """
    Диалог для отображения сообщений об ошибках

    status = 0 - стандартное сообщение
    status = 1 - ошибка, подсвечивается красным
    """

    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle("Сообщения об ошибках")
        self.resize(700, 300)
        self.mlist = QtGui.QListWidget()
        self.mbox = QtGui.QVBoxLayout()
        self.mbox.addWidget(self.mlist)
        self.setLayout(self.mbox)

        self.cmenu = QtGui.QMenu()
        aclear = self.cmenu.addAction("Очистить сообщения")
        aclear.triggered.connect(self.clear_messages)

    def show_message(self, message, status = 0):
        item = QtGui.QListWidgetItem(message)
        if status == 1:
            item.setBackgroundColor(QtCore.Qt.darkRed)
        self.mlist.addItem(item)

    def contextMenuEvent(self, QContextMenuEvent):
        self.cmenu.exec(self.mlist.mapToGlobal(QContextMenuEvent.pos()))

    def clear_messages(self):
        self.cmenu.clear()
