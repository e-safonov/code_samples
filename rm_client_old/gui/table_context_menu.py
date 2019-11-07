from datetime import datetime

import gui
from PyQt4 import QtGui, QtCore
from gui.sorting_proxy_model import SortingProxyModel
from gui.table_model import MonitorTableModel

MAX = 10


class TableInfo(QtGui.QDialog):
    def __init__(self, parent, acc, firm, ac_name):
        super(TableInfo, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.acc = acc
        self.firm = firm
        self.ac_name = ac_name
        self.setWindowTitle(gui.actions[self.ac_name]['title']+' '+self.firm+' | '+self.acc)
        self.resize(1500, 700)
        self.date_from = QtGui.QDateEdit()
        cur_date = datetime.now().date()
        self.date_from.setDate(cur_date)
        self.date_from.setCalendarPopup(True)
        self.date_to = QtGui.QDateEdit()
        self.date_to = QtGui.QDateEdit(cur_date)
        self.date_to.setCalendarPopup(True)
        self.bt_choose = QtGui.QPushButton("Выбрать")
        QtCore.QObject.connect(self.bt_choose, QtCore.SIGNAL("clicked()"), self.choose_data)
        self.progressBar = QtGui.QProgressBar(self)
        self.progressBar.setRange(0, MAX)
        self.progressBar.setValue(MAX)
        self.progressBar.setFormat('Загрузка завершена')
        self.progressBar.setTextVisible(True)
        self.progressBar.setAlignment(QtCore.Qt.AlignCenter)
        self.table_info = QtGui.QTableView()
        self.table_info.setUpdatesEnabled(False)
        self.table_info.setSortingEnabled(True)
        self.table_info.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.table_info.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.table_info.setUpdatesEnabled(True)
        self.table_info.verticalHeader().hide()
        self.table_info.setAlternatingRowColors(True)
        self.table_info.horizontalHeader().setMinimumSectionSize(-1)
        self.table_info.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.table_info.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.table_info.resizeColumnsToContents()
        self.table_info.resizeRowsToContents()
        self.table_info.horizontalHeader().setSortIndicator(0, QtCore.Qt.DescendingOrder)
        self.table_info.sortByColumn(0)
        self.progressBar.show()
        self.layout = QtGui.QGridLayout(self)
        self.layout.addWidget(QtGui.QLabel('с '), 0, 0, QtCore.Qt.AlignLeft)
        self.layout.addWidget(self.date_from, 0, 1, QtCore.Qt.AlignLeft)
        self.layout.addWidget(QtGui.QLabel('по '), 0, 2, QtCore.Qt.AlignLeft)
        self.layout.addWidget(self.date_to, 0, 3, QtCore.Qt.AlignLeft)
        self.layout.addWidget(self.bt_choose, 0, 4, QtCore.Qt.AlignLeft)
        if self.ac_name == 'act_orders':
            self.active_status = QtGui.QRadioButton('Активные')
            QtCore.QObject.connect(self.active_status, QtCore.SIGNAL("clicked()"), self.set_filter)
            self.done_status = QtGui.QRadioButton('Исполненные')
            QtCore.QObject.connect(self.done_status, QtCore.SIGNAL("clicked()"), self.set_filter)
            self.takeoff_status = QtGui.QRadioButton('Снятые')
            QtCore.QObject.connect(self.takeoff_status, QtCore.SIGNAL("clicked()"), self.set_filter)
            self.all_status = QtGui.QRadioButton('Все')
            self.all_status.setChecked(True)
            QtCore.QObject.connect(self.all_status, QtCore.SIGNAL("clicked()"), self.set_filter)
            self.layout.addWidget(self.active_status, 0, 8, QtCore.Qt.AlignLeft)
            self.layout.addWidget(self.done_status, 0, 9, QtCore.Qt.AlignLeft)
            self.layout.addWidget(self.takeoff_status, 0, 10, QtCore.Qt.AlignLeft)
            self.layout.addWidget(self.all_status, 0, 11, QtCore.Qt.AlignLeft)
        self.layout.addWidget(self.table_info, 1, 0, 1, 60)
        self.label_empty = QtGui.QLabel('Нет данных для отображения')
        self.label_empty.setVisible(False)
        self.layout.addWidget(self.label_empty, 1, 0, 1, 60, QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.progressBar, 2, 0, 1, 60)
        basemodelInfo = MonitorTableModel(self, gui.actions[self.ac_name]['tQuery_select'],
                                          gui.actions[self.ac_name]['header'],
                                          params = (self.firm, self.acc, cur_date, cur_date))
        self.modelTableInfo = SortingProxyModel(self)
        self.modelTableInfo.setSourceModel(basemodelInfo)
        self.table_info.setModel(self.modelTableInfo)
        if self.table_info.model().sourceModel().rowCount() == 0:
            self.table_info.setDisabled(True)
            self.label_empty.setVisible(True)
        self.timer = QtCore.QBasicTimer()

    def timerEvent(self, e):
        if self.step >= MAX:
            self.progressBar.setFormat('Загрузка завершена')
            self.timer.stop()
            return
        self.step = self.step+1
        self.progressBar.setValue(self.step)

    def set_filter(self):
        status = {'Снятые': 'Снята', 'Исполненные': 'Исполнена', 'Активные': 'Активна', 'Все': ''}
        self.table_info.model().setFilterKeyColumn(gui.actions[self.ac_name]['header'].index('Статус'))
        self.table_info.model().setFilterRegExp(QtCore.QRegExp(status[self.sender().text()]))

    def choose_data(self):
        self.table_info.setDisabled(False)
        self.label_empty.setVisible(False)
        self.progressBar.setFormat('Загрузка данных...')
        self.progressBar.reset()
        self.progressBar.setValue(1)
        if self.timer.isActive():
            self.timer.stop()
        self.timer.start(1, self)
        self.step = 0
        self.table_info.setUpdatesEnabled(False)
        date_to = self.date_to.date().toPyDate()
        date_from = self.date_from.date().toPyDate()
        time_delta = (date_to-date_from).days
        if time_delta > 5:
            QtGui.QMessageBox.warning(self, "Ошибка выбора данных", "За указанный период слишком много данных. "
                                                                    "Формирование выборки займет много времени.",
                                      QtGui.QMessageBox.NoButton)
        elif time_delta < 0:
            QtGui.QMessageBox.warning(self, "Неверный диапазон дат", "Конечная дата не может быть раньше начальной",
                                      QtGui.QMessageBox.NoButton)
        else:
            self.table_info.model().sourceModel().updateData(gui.actions[self.ac_name]['tQuery_select'],
                                                             params = (self.firm, self.acc, date_from, date_to))
            self.table_info.model().sourceModel().endResetModel()
            if self.table_info.model().sourceModel().rowCount() == 0:
                self.table_info.setDisabled(True)
                self.label_empty.setVisible(True)
        self.table_info.setUpdatesEnabled(True)
