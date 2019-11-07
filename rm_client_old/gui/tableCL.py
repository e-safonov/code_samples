import gui
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
from db_connection import DBconnection, DBException
from gui.edit_table import EditTableValues
from gui.list_model import MyListModel
from gui.sorting_proxy_model import SortingProxyModel
from gui.table_model import MonitorTableModel

db = DBconnection()


class RefTable(QtGui.QDialog):
    def __init__(self, parent, ac_name):
        super(RefTable, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.ac_name = ac_name
        self.setWindowTitle(gui.actions[self.ac_name]['title'])
        self.table = QTableView()
        self.table.setUpdatesEnabled(False)
        self.table.header = list(gui.actions[self.ac_name]['header'])
        baseModelRef = MonitorTableModel(self, gui.actions[self.ac_name]['tQuery_select'], self.table.header)
        self.modelRef = SortingProxyModel(self)
        self.modelRef.setSourceModel(baseModelRef)
        self.table.setModel(self.modelRef)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        width = self.table.model().sourceModel().columnCount() * self.table.columnWidth(0)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.resizeRowsToContents()
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        sort_column = gui.actions[self.ac_name]['header'].index('Клиент') if 'Клиент' in gui.actions[self.ac_name][
            'header'] else 0
        self.table.sortByColumn(sort_column)
        self.table.horizontalHeader().setSortIndicator(sort_column, QtCore.Qt.AscendingOrder)
        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self.edit_row)
        self.table.setUpdatesEnabled(True)
        add_button = QtGui.QPushButton("Добавить")
        QtCore.QObject.connect(add_button, QtCore.SIGNAL("clicked()"), self.insert_row)
        del_button = QtGui.QPushButton("Удалить")
        QtCore.QObject.connect(del_button, QtCore.SIGNAL("clicked()"), self.delete_row)
        gbox = QtGui.QGridLayout()
        column = 0
        add = 200
        if ac_name == 'ac_withdrawal':
            self.flt_Clients = QListView()
            self.flt_Clients.setSelectionMode(3)
            self.flt_Clients.setModel(MyListModel(self, gui.filters["clients"]['tQuery_select'], 'clients'))
            self.connect(self.flt_Clients, QtCore.SIGNAL("clicked(QModelIndex)"), self.setFilter)
            self.btn_clearFilter = QtGui.QPushButton("Очистить фильтр")
            self.connect(self.btn_clearFilter, QtCore.SIGNAL("clicked()"), self.unsetFilterAll)
            gbox.addWidget(self.flt_Clients, 0, 0)
            gbox.addWidget(self.btn_clearFilter, 1, 0, QtCore.Qt.AlignLeft)
            column = 4
            add += 300
        gbox.addWidget(self.table, 0, column, 1, column)
        gbox.setColumnMinimumWidth(column, 100)
        gbox.setColumnStretch(column, 1)
        gbox.addWidget(add_button, 1, column+1, 1, 1, QtCore.Qt.AlignRight)
        gbox.addWidget(del_button, 1, column+2, 1, 1, QtCore.Qt.AlignRight)
        self.resize(width+add, 500)
        self.table.adjustSize()
        self.setLayout(gbox)

    def unsetFilterAll(self):
        self.flt_Clients.clearSelection()
        self.table.model().setFilterRegExp('')

    def setFilter(self):
        flt_keys = []
        [flt_keys.append(self.sender().model().data(fl, QtCore.Qt.DisplayRole)) for fl in
         self.sender().selectedIndexes()]
        self.table.model().setFilterKeyColumn(gui.actions[self.ac_name]['header'].index('Клиент'))
        self.table.model().setFilterRegExp(QtCore.QRegExp('|'.join(flt_keys)))

    def edit_row(self):
        self.edit = EditTableValues(self, edited_table = self, ac_name = self.ac_name, is_edit = 'not empty')
        self.edit.exec_()

    def insert_row(self):
        self.edit = EditTableValues(self, edited_table = self, ac_name = self.ac_name, is_edit = 'empty')
        self.edit.exec_()

    def delete_row(self):
        reply = QtGui.QMessageBox.question(self, 'Удаление записи', "Вы уверены, что хотите удалить запись?",
                                           buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                           defaultButton = QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            index = self.table.model().mapToSource(self.table.currentIndex())
            self.deleteTableRow(index.row())

    def insertTableRow(self, tlist):
        self.table.setSortingEnabled(False)
        if self.ac_name == 'ac_counts':
            values = list(tlist)
            values[self.table.model().sourceModel().tHeaderDB.index('client_name')] = tlist[
                self.table.model().sourceModel().tHeaderDB.index('client_id')]
            values[self.table.model().sourceModel().tHeaderDB.index('str_name')] = tlist[
                self.table.model().sourceModel().tHeaderDB.index('strategy_id')]
            values[self.table.model().sourceModel().tHeaderDB.index('sec_code')] = tlist[
                self.table.model().sourceModel().tHeaderDB.index('sec_id')]
            values = values[0:self.table.model().sourceModel().tHeaderDB.index('client_id')]
        elif self.ac_name == 'ac_withdrawal':
            values = [tlist[self.table.model().sourceModel().tHeaderDB.index('account_id')],
                      tlist[self.table.model().sourceModel().tHeaderDB.index('with_datetime')],
                      tlist[self.table.model().sourceModel().tHeaderDB.index('nsum')]]
        else:
            values = tlist[:-1]
        returned_id = None
        try:
            returned_id = db.DBUpdateData(gui.actions[self.ac_name]['tQuery_insert'], tuple(values))
            if returned_id is not None:
                tlist[-1] = returned_id
                self.table.model().sourceModel().rows.append(tlist)
                self.table.model().sourceModel().endResetModel()
        except DBException as e:
            if e.pgcode == '23505':
                QtGui.QMessageBox.warning(self, "Ошибка добавления записи", "Такое значение уже существует.",
                                          QtGui.QMessageBox.NoButton)
            else:
                QtGui.QMessageBox.warning(self, "Ошибка базы данных", e.description+'\nКод ошибки:'+e.pgcode,
                                          QtGui.QMessageBox.Ok)
        self.table.setSortingEnabled(True)

    def deleteTableRow(self, num_row):
        self.table.setSortingEnabled(False)
        try:
            db.DBUpdateData(gui.actions[self.ac_name]['tQuery_delete'],
                            (self.table.model().sourceModel().rows[num_row][-1],))
            self.table.model().sourceModel().rows.pop(num_row)
            self.table.model().sourceModel().endResetModel()
        except DBException as e:
            if (self.ac_name == 'ac_clients' or self.ac_name == 'ac_strategy') and e.pgcode == '23503':
                QtGui.QMessageBox.warning(self, "Ошибка удаления", "Невозможно удалить запись:"
                                                                   " в справочнике счетов есть ссылки на данную запись",
                                          QtGui.QMessageBox.NoButton)
            else:
                QtGui.QMessageBox.warning(self.parent, "Ошибка базы данных", e.description+'\nКод ошибки:'+e.pgcode,
                                          QtGui.QMessageBox.Ok)
        self.table.setSortingEnabled(True)

    def changeTableRow(self, tlist):
        self.table.setSortingEnabled(False)
        if self.ac_name == 'ac_counts':
            values = list(tlist[:-1])
            values[self.table.model().sourceModel().tHeaderDB.index('client_name')] = tlist[
                self.table.model().sourceModel().tHeaderDB.index('client_id')]
            values[self.table.model().sourceModel().tHeaderDB.index('str_name')] = tlist[
                self.table.model().sourceModel().tHeaderDB.index('strategy_id')]
            values[self.table.model().sourceModel().tHeaderDB.index('sec_code')] = tlist[
                self.table.model().sourceModel().tHeaderDB.index('sec_id')]
            values[self.table.model().sourceModel().tHeaderDB.index('client_id')] = tlist[
                self.table.model().sourceModel().tHeaderDB.index('account_id')]
            # values[self.table.model().sourceModel().tHeaderDB.index('excel_name')]  = tlist[self.table.model().sourceModel().tHeaderDB.index('excel_name')]
            values = tuple(values[0:self.table.model().sourceModel().tHeaderDB.index('client_id')+1])
        elif self.ac_name == 'ac_withdrawal':
            values = (tlist[self.table.model().sourceModel().tHeaderDB.index('account_id')],
                      tlist[self.table.model().sourceModel().tHeaderDB.index('with_datetime')],
                      tlist[self.table.model().sourceModel().tHeaderDB.index('nsum')],
                      tlist[self.table.model().sourceModel().tHeaderDB.index('id')])
        else:
            values = tlist
        res = None
        try:
            res = db.DBUpdateData(gui.actions[self.ac_name]['tQuery_update'], values)
            if res is None:
                index = self.table.model().mapToSource(self.table.currentIndex())
                self.table.model().sourceModel().rows[index.row()] = tlist
                self.table.model().sourceModel().endResetModel()
        except DBException as e:
            if e.pgcode == '23505':
                QtGui.QMessageBox.warning(self, "Ошибка обновления данных", "Такое значение уже существует.",
                                          QtGui.QMessageBox.NoButton)
            else:
                QtGui.QMessageBox.warning(self, "Ошибка базы данных", e.description+'\nКод ошибки:'+e.pgcode,
                                          QtGui.QMessageBox.Ok)
        self.table.setSortingEnabled(True)
