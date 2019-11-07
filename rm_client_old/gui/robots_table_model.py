# -*- coding: utf-8 -*-
from operator import itemgetter

from PyQt4 import QtCore, QtGui
from gui import tblHeaders


class RobotsTableModel(QtCore.QAbstractTableModel):
    """ Модель для таблицы с роботами """
    greenColour = QtGui.QBrush(QtGui.QColor(230, 255, 235))
    yellowColour = QtGui.QBrush(QtGui.QColor(255, 255, 192))

    def __init__(self, parent):
        self.parent = parent
        super(RobotsTableModel, self).__init__(parent)
        self.rows = list()
        self.header = tblHeaders['robots']
        self.filters = {'clt': '', 'strategy': '', 'state': ''}

    def rowCount(self, parent = None):
        return len(self.rows) if self.rows else 0

    def columnCount(self, parent = None):
        return len(self.header)

    def headerData(self, col, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return self.header[col] if orientation == QtCore.Qt.Horizontal else col+1
        return None

    def data(self, index, role):
        if not index.isValid(): return None

        col = index.column()
        row = index.row()
        value = self.rows[row][col]
        if value is None or value == '': return None

        if role == QtCore.Qt.DisplayRole:
            return value
        elif role == QtCore.Qt.BackgroundColorRole:
            return self.greenColour if 'торговля запущена' == self.rows[row][5] else self.yellowColour if \
            self.rows[row][5] in ('подключен к QUIK', 'торговля остановлена') else None
        elif role == QtCore.Qt.CheckStateRole and col == 0:
            return QtCore.Qt.Checked if self.rows[row][0] else QtCore.Qt.Unchecked

    def sort(self, col, order = QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self.rows = sorted(self.rows, key = itemgetter(col), reverse = order == QtCore.Qt.DescendingOrder)
        self.layoutChanged.emit()

    def setData(self, index, p_object, role = None):
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            self.rows[index.row()][0] = not self.rows[index.row()][0]
        return True

    def updateData(self, srv_ip, message):
        for addr in message:
            row = next((r for r in self.rows if r[6] == addr and r[8] == srv_ip), None)
            unit = message[addr]
            if row is not None:
                if unit['state'] == 'dead':
                    self.rows.remove(row)
                else:
                    titles = unit['title'].split(' ', 1)
                    if len(titles) == 1: titles += ['', ]
                    lclt, lstr, lst = len(self.filters['clt']) >= 3, len(self.filters['strategy']) >= 3, len(
                        self.filters['state']) >= 3
                    inclt = self.filters['clt'].lower() in titles[0].lower()
                    instr = self.filters['strategy'].lower() in titles[1].lower()
                    inst = self.filters['state'].lower() in unit['state'].lower()
                    if self.filter_row(lclt, lstr, lst, inclt, instr, inst):
                        row[1:6] = titles+[unit['inc'] if 'inc' in unit.keys() else 0,
                                           unit['pos'] if 'pos' in unit.keys() else 0, unit['state']]
                    else:
                        self.rows.remove(row)
            elif unit['unit_type'] == 'robot' and unit['state'] != 'dead':
                titles = unit['title'].split(' ', 1)
                if len(titles) == 1: titles += ['', ]
                lclt, lstr, lst = len(self.filters['clt']) >= 3, len(self.filters['strategy']) >= 3, len(
                    self.filters['state']) >= 3
                inclt = self.filters['clt'].lower() in titles[0].lower()
                instr = self.filters['strategy'].lower() in titles[1].lower()
                inst = self.filters['state'].lower() in unit['state'].lower()
                if self.filter_row(lclt, lstr, lst, inclt, instr, inst):
                    self.rows.append([False]+titles+[unit['inc'] if 'inc' in unit.keys() else 0,
                                                     unit['pos'] if 'pos' in unit.keys() else 0, unit['state'], addr,
                                                     unit['version'], srv_ip])

    def setFilter(self, flt_cat = None, flt_text = None):
        if flt_cat not in self.filters or len(flt_text) < 3:
            self.filters[flt_cat] = ''
        else:
            self.filters[flt_cat] = flt_text

    def filter_row(self, lclt, lstr, lst, inclt, instr, inst):
        return not (lclt or lstr or lst) or lclt and not (lstr or lst) and inclt or lstr and not (
        lclt or lst) and instr or lst and not (
        lclt or lstr) and inst or lclt and lstr and not lst and inclt and instr or lclt and lst and not lstr and inclt and inst or lstr and lst and not lclt and instr and inst or lclt and lstr and lst and inclt and instr and inst

    def check_all(self, check):
        for r in self.rows: r[0] = check

    def is_any_checked(self):
        return any([r for r in self.rows if r[0]])

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable
