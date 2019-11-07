from datetime import datetime, date, time
from decimal import Decimal

import gui
from PyQt4 import QtCore, QtGui
from db_connection import DBconnection, DBException

db = DBconnection()


class MonitorTableModel(QtCore.QAbstractTableModel):
    """ Модель для таблиц мониторинга """
    filter_varmargin = ("Вар.маржа", "Накопл.доход")
    filter_svod = ("Клиент", "Стратегия", "Лот", "Количество сделок", "Срок вложения")
    filter_instr = gui.tblHeaders['instruments']

    def __init__(self, parent, DBQuery, header = None, params = None):
        self.parent = parent
        super(MonitorTableModel, self).__init__(parent)
        self.rows = []
        self.filter_col = 0
        self.filter_regExp = ''
        self.header = header
        self._query = DBQuery
        try:
            self.tHeaderDB = db.DBGetHeader(self._query, params = params)
        except DBException as e:
            QtGui.QMessageBox.warning(self.parent, "Ошибка базы данных", e.description+'\nКод ошибки:'+e.pgcode,
                                      QtGui.QMessageBox.Ok)
        self.updateData(params = params)

    def rowCount(self, parent = None):
        return len(self.rows) if self.rows else 0

    def columnCount(self, parent = None):
        return len(self.header)

    def headerData(self, col, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return self.header[col] if orientation == QtCore.Qt.Horizontal else col+1
        return None

    def sort(self, col, order = QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self.rows = sorted(self.rows, key = lambda x: (x[col] is not None, x[col]),
                           reverse = order == QtCore.Qt.DescendingOrder)
        self.layoutChanged.emit()

    def setFilterKeyColumn(self, col):
        self.filter_col = col

    def setFilterRegExp(self, qregexp):
        self.filter_regExp = qregexp

    def data(self, index, role):
        if not index.isValid(): return None

        col = index.column()
        value = self.rows[index.row()][col]
        if value is None or value == '': return None

        if role == QtCore.Qt.DisplayRole:
            if type(value) is Decimal:
                value = '{0:,.2f}'.format(value).replace(',', ' ')
            elif type(value) is date:
                value = datetime.strftime(value, '%d.%m.%Y')
            elif type(value) is time:
                value = time.strftime(value, '%H:%M:%S')
            elif type(value) is datetime:
                value = datetime.strftime(value, '%d.%m.%Y %H:%M:%S')
            return value
        elif role == QtCore.Qt.TextAlignmentRole and col >= 4:
            return QtCore.Qt.AlignRight
        elif role == QtCore.Qt.BackgroundRole:
            if self.header[col] in self.filter_varmargin or (
                    self.objectName() == 'tableSvodModel' and
                    self.header[col] not in self.filter_svod
            ):
                return QtGui.QBrush(QtGui.QColor(QtCore.Qt.darkRed)) if int(value or 0) < 0 else \
                    QtGui.QBrush(QtGui.QColor(QtCore.Qt.darkGreen) if int(value or 0) > 0 else \
                                     QtGui.QBrush(QtGui.QColor(QtCore.Qt.gray)))
            elif self.objectName() == 'tvInstrModel':
                value_color = self.rows[index.row()][gui.tables['instruments']['header'].index('% ')] or .0
                return QtGui.QBrush(QtGui.QColor(QtCore.Qt.darkRed)) if float(value_color) < 0 else \
                    QtGui.QBrush(QtGui.QColor(QtCore.Qt.darkGreen) if float(value_color) > 0 else \
                                     QtGui.QBrush(QtGui.QColor(QtCore.Qt.gray)))

    def updateData(self, query = None, params = None):
        try:
            self.rows[:] = db.DBGetData(query or self._query, params = params)
        except DBException as e:
            QtGui.QMessageBox.warning(self.parent, "Ошибка базы данных", e.description+'\nКод ошибки:'+e.pgcode,
                                      QtGui.QMessageBox.Ok)

        if self.filter_regExp != '':
            self.rows[:] = [r for r in self.rows if self.filter_regExp.indexIn(r[self.filter_col], 0) != -1]

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
