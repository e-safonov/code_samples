import os

from PyQt4 import QtGui
from export import OpenDialog

system_type = os.name
if system_type == 'nt':
    import win32com.client
    from pywintypes import com_error


class ExcelLoader(OpenDialog):
    def __init__(self):
        super().__init__()
        self.wbook = None
        self.last_rows = None
        self.line_list = None

    def _set_window_mode(self):
        """Задаём специальные параметры диалога открытия файла"""
        self.dialog.setFilter('Файлы Excel 2007 или более поздней верссии (*.xlsx)')
        self.dialog.setWindowTitle("Укажите файл отчёта для выгрузки данных")

    def _format_check(self, lst):
        """Проверка листа на соответствие формату"""
        try:
            k = self.wbook.Sheets(lst[2]).Index
            if self.wbook.Sheets(lst[2]).Range('E1').Value == 'Комиссия':
                self.last_rows[k] = 0
                return True
            else:
                return False
        except com_error:
            return False

    def _show_error(self, error):
        QtGui.QMessageBox.critical(self.dialog, "Ошибка!", error, QtGui.QMessageBox.Ok)
        return

    def _get_last_rows(self):
        """Получаем номера последних заполненных строк для нужных нам листов"""
        if len(self.last_rows) != 0:

            for l in sorted(self.last_rows):
                # Черная магия, не трогать!
                self.last_rows[l] = self.wbook.Sheets(l).Columns('A').SpecialCells(2).Count
            return True
        else:
            self._show_error('Ни один лист не задан для выгрузки.')
            self._close_file()
            return False

    def _past_formula(self, cur_sheet, row_num):
        cur_sheet.Columns('G').Rows(row_num).Value = ''.join(['=F', str(row_num), '+G', str(row_num-1)])
        cur_sheet.Columns('N').Rows(row_num).Value = ''.join(['=E', str(row_num), '/(0.93*R', str(row_num), ')'])
        cur_sheet.Columns('P').Rows(row_num).Value = ''.join(['=G', str(row_num), '/T', str(row_num)])
        cur_sheet.Columns('Q').Rows(row_num).Value = ''.join(['=(O', str(row_num), '-$O$2)/$O$2'])
        cur_sheet.Columns('R').Rows(row_num).Value = '=$R$2'
        cur_sheet.Columns('S').Rows(row_num).Value = ''.join(
            ['=СУММ($I$2:I', str(row_num-1), ')*(A', str(row_num), '-A', str(row_num-1), ')'])
        cur_sheet.Columns('T').Rows(row_num).Value = ''.join(
            ['=СУММ($S$2:S', str(row_num), ')/(A', str(row_num), '-$A$2)'])
        cur_sheet.Columns('U').Rows(row_num).Value = ''.join(['=Q', str(row_num)])
        cur_sheet.Columns('V').Rows(row_num).Value = ''.join(['=S', str(row_num)])
        cur_sheet.Columns('W').Rows(row_num).Value = ''.join(
            ['=СУММ($V$2:V', str(row_num), ')/(A', str(row_num), '-$A$2)'])
        cur_sheet.Columns('X').Rows(row_num).Value = ''.join(['=G', str(row_num), '/W', str(row_num)])
        return

    def _open_file(self):
        xlapp = win32com.client.Dispatch("Excel.Application")
        xlapp.DisplayAlerts = 0
        file_path = self.get_path()
        self.wbook = xlapp.Workbooks.Open(file_path[0])
        return

    def _close_file(self):
        if self.wbook:
            self.wbook.Save()
            self.wbook.Application.Quit()
        return

    def write(self, line_list):
        """Здесь перехватываем все ошибки грёбанного Excel-я"""
        self.line_list = line_list
        try:
            self._write_main()
        except (com_error, TypeError, NameError) as e:
            self._show_error(str(e))

        self._close_file()
        return

    def _write_main(self):
        """Здесь выполняем основную работу по выгрузке"""
        self._open_file()
        self.last_rows = dict()
        self.line_list = list(filter(self._format_check, self.line_list))
        if not self._get_last_rows():
            return

        for i in range(len(self.line_list)):
            line = self.line_list[i]
            sheet_num = self.wbook.Sheets(line[2]).Index
            cur_sheet = self.wbook.Sheets(sheet_num)
            # Вставляем новые строки, начиная с последней (не затераем ни низ, ни верх)
            self.last_rows[sheet_num] += 1
            cur_sheet.Rows(self.last_rows[sheet_num]).Insert()
            row_num = self.last_rows[sheet_num]
            # print("row="+str(row_num)+" sheet="+cur_sheet.Name)

            cur_sheet.Columns('A').Rows(row_num).Value = line[0] if line[0] != 'None' else ''  # Дата
            cur_sheet.Columns('B').Rows(row_num).Value = line[4] if line[4] != 'None' else ''  # Остаток на начало дня
            cur_sheet.Columns('C').Rows(row_num).Value = line[11]  # Вар.маржа фьючерсы
            cur_sheet.Columns('D').Rows(row_num).Value = line[12]  # Вар.маржа опционы
            cur_sheet.Columns('E').Rows(row_num).Value = line[10] if line[10] != 'None' else ''  # Комиссия
            cur_sheet.Columns('F').Rows(row_num).Value = line[9] if line[9] != 'None' else ''  # Результат - сборы
            cur_sheet.Columns('H').Rows(row_num).Value = line[6] if line[6] != 'None' else ''  # Остаток на конец дня
            cur_sheet.Columns('I').Rows(row_num).Value = line[7] if line[7] != 'None' else ''  # Вводы/выводы
            cur_sheet.Columns('J').Rows(row_num).Value = line[5] if line[5] != 'None' else ''  # Фьючерс
            cur_sheet.Columns('O').Rows(row_num).Value = line[8] if line[8] != 'None' else ''  # Значение индекса

            past_border = len(line[13])
            merge_border = past_border-1

            if past_border >= 2:

                # добавляем строчки ниже, текущую не трогаем
                for k in range(0, merge_border):
                    ins_num = row_num+k
                    cur_sheet.Rows(ins_num).Insert()

                for k in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'N', 'O', 'P', 'Q']:
                    parts = [k, str(row_num), ':', k, str(row_num+merge_border)]
                    cur_sheet.Range(''.join(parts)).Merge()

                for k in range(past_border):
                    cur_sheet.Columns('L').Rows(row_num+k).Value = str(line[13][k])
                    cur_sheet.Columns('M').Rows(row_num+k).Value = str(line[14][k])
                    cur_sheet.Columns('K').Rows(row_num+k).Value = str(line[15][k])

                self.last_rows[sheet_num] = row_num+merge_border

            elif past_border == 1:
                cur_sheet.Columns('L').Rows(row_num).Value = str(line[13][0])
                cur_sheet.Columns('M').Rows(row_num).Value = str(line[14][0])
                cur_sheet.Columns('K').Rows(row_num).Value = str(line[15][0])
            else:
                cur_sheet.Columns('L').Rows(row_num).Value = ''
                cur_sheet.Columns('M').Rows(row_num).Value = '0.0'
                cur_sheet.Columns('K').Rows(row_num).Value = '0'

            section = ''.join(['B', str(row_num), ':I', str(row_num)])
            cur_sheet.Range(section).NumberFormat = '# ##0,00'

            self._past_formula(cur_sheet, row_num)

        return
