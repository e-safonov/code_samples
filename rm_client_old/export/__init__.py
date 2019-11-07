from PyQt4 import QtGui


class OpenDialog:
    def __init__(self):
        self.dialog = None

    def _set_window_mode(self):
        """Задаёт специальные параметры диалога открытия файла"""
        raise Exception("NotImplementedException")

    def get_path(self):
        self.dialog = QtGui.QFileDialog()
        self.dialog.setModal(True)
        self.dialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
        self._set_window_mode()
        self.dialog.open()

        choice = self.dialog.exec_()
        if choice == QtGui.QDialog.Accepted:
            print(self.dialog.selectedFiles())
            return self.dialog.selectedFiles()
        else:
            QtGui.QMessageBox.warning(self.dialog, "Ошибка!", 'Не выбрано ни одного объекта!', QtGui.QMessageBox.Ok)
            return None
