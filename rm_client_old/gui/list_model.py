from PyQt4 import QtCore, QtGui
from db_connection import DBconnection, DBException

db = DBconnection()


class MyListModel(QtCore.QAbstractListModel):
    def __init__(self, parent, aSQLquery, aModelName):
        self.parent = parent
        super(MyListModel, self).__init__(parent)
        self.ModelName = aModelName
        self.rows = []
        self.getSQLdata(aSQLquery)

    def getSQLdata(self, aSQLquery):
        # Обновляем модель путем выполнения запроса к СУБД
        self.tQuery = aSQLquery
        try:
            self.rows = db.DBGetData(self.tQuery)
        except DBException as e:
            QtGui.QMessageBox.warning(self.parent, "Ошибка базы данных", e.description+'\nКод ошибки:'+e.pgcode,
                                      QtGui.QMessageBox.Ok)

    def rowCount(self, index = None):
        return len(self.rows)

    def data(self, index, role):
        if not index.isValid() or role != QtCore.Qt.DisplayRole:
            return None
        return str(self.rows[index.row()][index.column()])
