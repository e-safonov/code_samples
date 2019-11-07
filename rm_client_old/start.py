import os
import sys

from PyQt4 import QtCore, QtGui
from gui.main_window import MyWindow

# from gui.alert_dialog import AlertDialog


if __name__ == "__main__":
    # import cProfile
    # import pstats
    app = QtGui.QApplication(sys.argv)
    ic = QtGui.QIcon()
    ic.addFile(os.path.join(os.getcwd(), 'Icons', 'rm24.png'), QtCore.QSize(24, 24))
    ic.addFile(os.path.join(os.getcwd(), 'Icons', 'rm32.png'), QtCore.QSize(32, 32))
    ic.addFile(os.path.join(os.getcwd(), 'Icons', 'rm48.png'), QtCore.QSize(48, 48))
    ic.addFile(os.path.join(os.getcwd(), 'Icons', 'rm64.png'), QtCore.QSize(64, 64))
    app.setWindowIcon(ic)
    window = MyWindow()
    window.show()

    # alert
    # alert = AlertDialog()
    # alert.show()
    # alert.show_message("Пипец какая ошибка!", 1)
    # alert.show_message("Просто ошибка.")

    sys.exit(app.exec_())
    # cProfile.run('app.exec_()','main.prof')
    # pst=pstats.Stats('main.prof')
    # pst.strip_dirs().sort_stats('cumulative').print_stats(30)
    # pst.print_callers(20)
    # sys.exit()
