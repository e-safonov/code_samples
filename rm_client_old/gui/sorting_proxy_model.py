from PyQt4 import QtGui


class SortingProxyModel(QtGui.QSortFilterProxyModel):
    def lessThan(self, left, right):
        """ left and right both have type of ModelIndex"""
        ld, rd = left.data(), right.data()
        if (ld is None) or (rd is None): return False
        if type(ld) is int and type(rd) is int: return ld < rd
        if type(ld) is float and type(rd) is float: return ld < rd
        try:
            lvalue = float(left.data().replace(' ', ''))
            rvalue = float((right.data()).replace(' ', ''))
        except ValueError:
            lvalue = str(left.data())
            rvalue = str(right.data())
        return lvalue < rvalue

    def filterCaseSensitivity(self):
        return False

    def dynamicSortFilter(self):
        return True
