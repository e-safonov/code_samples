from PyQt4 import QtGui, QtCore
from db_connection import DBconnection
from export.to_excel import ExcelLoader


class DailyReport(QtGui.QDialog):
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.setModal(True)
        self.setWindowTitle("Введите период")
        self.resize(250, 100)
        self.box = QtGui.QVBoxLayout()
        self.ed_begin = QtGui.QDateEdit()
        self.ed_end = QtGui.QDateEdit()
        self.ed_begin.setDate(QtCore.QDate.currentDate())
        self.ed_end.setDate(QtCore.QDate.currentDate())
        self.ed_begin.setDisplayFormat('yyyy-MM-dd')
        self.ed_end.setDisplayFormat('yyyy-MM-dd')
        self.bt_load = QtGui.QPushButton("Сформировать")
        self.box.addWidget(self.ed_begin)
        self.box.addWidget(self.ed_end)
        self.box.addWidget(self.bt_load)
        self.setLayout(self.box)
        self.dbcon = DBconnection()
        self.connect(self.bt_load, QtCore.SIGNAL("clicked()"), self.load_slot)
        self.loader = ExcelLoader()

    def res_processing(self, main_result, ins_result):
        main_result = list(map(list, main_result))
        ins_result = list(map(list, ins_result))
        for i in range(len(main_result)):
            main_result[i].append(0.0)  # ячейка 11 для вариационки фьючерсов
            main_result[i].append(0.0)  # ячейка 12 для вариационки опционов
            main_result[i].append(list())  # служебная ячейка 13
            main_result[i].append(list())  # служебная ячейка 14
            main_result[i].append(list())  # служебная ячейка 15
            for n in range(len(ins_result)):
                if main_result[i][0] == ins_result[n][0] and main_result[i][1] == ins_result[n][1]:
                    if ins_result[n][4] == 'SPBFUT':
                        main_result[i][11] += float(ins_result[n][5])
                    elif ins_result[n][4] == 'SPBOPT':
                        main_result[i][12] += float(ins_result[n][5])
                        main_result[i][13].append(ins_result[n][3])
                        main_result[i][14].append(ins_result[n][5])
                        main_result[i][15].append(ins_result[n][6])
        return main_result

    def load_slot(self):
        self.bt_load.setText("Данные выгружаются..")
        self.bt_load.setEnabled(False)

        main_query = "SELECT * FROM daily_report("
        main_query += "'"+self.ed_begin.text()+"'"
        main_query += ", '"+self.ed_end.text()+"'"
        main_query += ");"
        main_result = self.dbcon.DBGetData(main_query)

        ins_query = "SELECT * FROM daily_report_instruments("
        ins_query += "'"+self.ed_begin.text()+"'"
        ins_query += ", '"+self.ed_end.text()+"'"
        ins_query += ");"
        ins_result = self.dbcon.DBGetData(ins_query)

        result = self.res_processing(main_result, ins_result)
        for i in range(len(result)):
            result[i] = list(map(str, result[i][:13]))+result[i][13:]
        self.loader.write(line_list = result)
        self.bt_load.setText("Сформировать")
        self.bt_load.setEnabled(True)
