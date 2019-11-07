import csv
import os

from export import OpenDialog


class CSVLoader(OpenDialog):
    def _set_window_mode(self):
        """Задаёт специальные параметры диалога открытия файла"""
        self.dialog.setFileMode(self.dialog.Directory)
        self.dialog.setOption(self.dialog.ShowDirsOnly)
        self.dialog.setWindowTitle("Откройте папку, где будет создан файл CSV")

    def write(self, line_list):
        file_path = self.get_path()

        if file_path is None:
            return

        file_path = os.path.join(os.path.abspath(file_path[0]), 'data.csv')
        with open(file_path, "w") as csv_fh:
            writer = csv.writer(csv_fh, delimiter = ';', quoting = csv.QUOTE_MINIMAL, quotechar = '`',
                                lineterminator = '\n')
            writer.writerows(line_list)
        return
