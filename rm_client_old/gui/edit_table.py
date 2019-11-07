# -*- coding: utf-8 -*-
import gui
from PyQt4 import QtCore, QtGui
from db_connection import DBconnection, DBException

db = DBconnection()
# максимальное значение индекса в таблице ref_accounts в БД(последовательность account_list_account_id_seq)
MAX = 9223372036854775807

# минимальное значение индекса в таблице ref_accounts в БД(последовательность account_list_account_id_seq)
MIN = 1


class EditTableValues(QtGui.QDialog):
    def __init__(self, parent, ac_name, is_edit, edited_table):
        super(EditTableValues, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.header = edited_table.table.header
        self.ac_name = ac_name
        self.edited_table_model = edited_table.table.model().sourceModel()
        self.adjustSize()
        title = gui.actions[ac_name]['title']
        if is_edit == 'empty':
            self.setWindowTitle('Добавление в справочник '+title)
            self.row = ['' for i in range(len(self.edited_table_model.tHeaderDB))]
            self.method = edited_table.insertTableRow
        else:
            self.setWindowTitle('Редактирование справочника '+title)
            index = edited_table.table.model().mapToSource(edited_table.table.currentIndex())
            self.row = list(self.edited_table_model.rows[index.row()])
            self.method = edited_table.changeTableRow
        self.edit_fields = []
        edit_lay = QtGui.QFormLayout()
        edit_lay.setHorizontalSpacing(20)
        self.d_combo = {'ac_counts': {'Клиент': 'clients', 'Стратегия': 'strategies', 'Инструмент': 'instruments'},
                        'ac_withdrawal': {'Счет': 'accounts', 'Клиент': 'clients'}}
        self.dependencies = [{'master': 'clients', 'slave': 'accounts'}, {'master': 'clients', 'slave': 'firms'}]
        if self.d_combo.get(self.ac_name) and self.row[-2] != '':
            values = (self.row[-2], 0)
        else:
            values = (MIN, MAX)
        for h in range(len(self.header)):
            edit_field = QtGui.QLineEdit()
            if self.header[h] == 'Мин. план.чист.' or self.header[h] == 'Сумма':
                edit_field.setValidator(QtGui.QDoubleValidator())
                edit_field.setPlaceholderText('0.00')
                edit_field.setToolTip('Пример: 546.89')
                edit_field.textEdited.connect(self.check_state)
            if self.header[h] == 'Дата/время':
                edit_field.setPlaceholderText('гггг-мм-дд чч:мм:сс')
                edit_field.setToolTip('Пример: 2016-01-31 18:34:05')
            if self.header[h] == 'Фирма' and self.d_combo.get(self.ac_name):
                edit_field.setDisabled(True)
                edit_field.setReadOnly(True)
                edit_field.setObjectName('firms')
            if self.d_combo.get(self.ac_name) and self.header[h] in self.d_combo[ac_name].keys():
                combo = QtGui.QComboBox()
                combo.setEditable(True)
                combo.setObjectName(self.d_combo[ac_name][self.header[h]])
                [combo.setDisabled(True) for d in self.dependencies if
                 d['slave'] == combo.objectName() and is_edit == 'empty']
                try:
                    combo_list = db.DBGetData(gui.filters[self.d_combo[ac_name][self.header[h]]]['tQuery_select'],
                                              values)
                    combo_list.insert(0, ('', ''))
                except DBException as e:
                    QtGui.QMessageBox.warning(self, "Ошибка базы данных", e.description+'\nКод ошибки:'+e.pgcode,
                                              QtGui.QMessageBox.Ok)
                [combo.addItem(cl[0], cl[1]) for cl in combo_list]
                [combo.setCurrentIndex(i) for i, t in enumerate(combo_list) if self.row[h] == t[0]]
                combo.currentIndexChanged.connect(self.select_item)
                edit_lay.addRow(self.header[h], combo)
                self.edit_fields.append(combo)
            else:
                if self.row[h] is not None:
                    edit_field.setText(str(self.row[h]))
                edit_lay.addRow(self.header[h], edit_field)
                self.edit_fields.append(edit_field)
        self.b_save = QtGui.QPushButton("Сохранить")
        QtCore.QObject.connect(self.b_save, QtCore.SIGNAL("clicked()"), self.save)
        self.b_cancel = QtGui.QPushButton("Отменить")
        self.b_cancel.setDefault(True)
        QtCore.QObject.connect(self.b_cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("close()"))
        button_lay = QtGui.QHBoxLayout()
        button_lay.setSpacing(20)
        button_lay.addWidget(self.b_save, 1, QtCore.Qt.AlignRight)
        button_lay.addWidget(self.b_cancel, 0, QtCore.Qt.AlignRight)
        edit_lay.addRow(button_lay)
        lay = QtGui.QFormLayout()
        lay.setSpacing(12)
        lay.addRow(edit_lay)
        self.setLayout(lay)
        self.layout().setSizeConstraint(QtGui.QLayout.SetFixedSize)

    def check_state(self):
        state = self.sender().validator().validate(self.sender().text(), 0)[0]
        if state == QtGui.QValidator.Acceptable:
            color = '#c4df9b'
        else:
            color = '#f6989d'
        self.sender().setStyleSheet('QLineEdit { background-color: %s }' % color)

    def reload_values(self, master_id, slave_obj):
        if master_id == '':
            slave_obj.setDisabled(True)
        else:
            try:
                values = (master_id, 0)
                slave_obj.setDisabled(False)
                result = db.DBGetData(gui.filters[slave_obj.objectName()]['tQuery_select'], values)
                if type(slave_obj) is QtGui.QLineEdit:
                    slave_obj.setText(result[0][0])
                if type(slave_obj) is QtGui.QComboBox:
                    result.insert(0, ('', ''))
                    slave_obj.clear()
                    [slave_obj.addItem(rs[0], rs[1]) for rs in result]
                    slave_obj.setCurrentIndex(0)
            except DBException as e:
                QtGui.QMessageBox.warning(self, "Ошибка базы данных", e.description+'\nКод ошибки:'+e.pgcode,
                                          QtGui.QMessageBox.Ok)

    def select_item(self, num):
        for el in range(len(self.edit_fields)):
            for d in self.dependencies:
                if d['master'] == self.sender().objectName() and self.edit_fields[el].objectName() == d['slave']:
                    self.reload_values(self.sender().itemData(num), self.edit_fields[el])
            if self.edit_fields[el] == self.sender():
                self.row[el] = self.sender().currentText()
                self.row[self.edited_table_model.tHeaderDB.index(
                    gui.filters[self.sender().objectName()]['id'])] = self.sender().itemData(num)

    def save(self):
        err = False
        for f in range(len(self.edit_fields)):
            if type(self.edit_fields[f]) is QtGui.QLineEdit:
                self.row[f] = (self.edit_fields[f].text() or None)
            if type(self.edit_fields[f]) is QtGui.QComboBox:
                self.row[f] = (self.edit_fields[f].currentText() or None)
            if (self.header[f] in ('Клиент', 'Название', 'Счет', 'Фирма', 'Сумма', 'Дата', 'Стратегия') and not
            self.row[f]):
                err = True
                QtGui.QMessageBox.warning(self, "Ошибка cохранения", "Не указано значение в поле "+self.header[f],
                                          QtGui.QMessageBox.NoButton)
        if not err:
            self.method(self.row)
            self.done(True)
