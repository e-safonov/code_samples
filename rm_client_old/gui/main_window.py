"""
Хохломин Роман, Сафонов Евгений, Мишина Любовь
"""
import json
import network
import os
import socket
from datetime import datetime

import gui
from PyQt4 import QtCore, QtGui, uic
from db_connection import DBconnection
from export.to_csv import CSVLoader
from gui.daily_report import DailyReport
from gui.list_model import MyListModel
from gui.robots_table_model import RobotsTableModel
from gui.sorting_proxy_model import SortingProxyModel
from gui.tableCL import RefTable
from gui.table_context_menu import TableInfo
from gui.table_model import MonitorTableModel

db = DBconnection()


class MyWindow(QtGui.QMainWindow):
    """Класс основного окна программы """
    version = '0.2'

    def __init__(self, parent = None):
        super(MyWindow, self).__init__(parent)
        if not os.path.exists(os.path.join(os.getcwd(), "RiskManagerForm.ui")):
            uic.loadUi(os.path.join(os.getcwd(), "gui", "RiskManagerForm.ui"), self)
        else:
            uic.loadUi(os.path.join(os.getcwd(), "RiskManagerForm.ui"), self)

        self.setWindowTitle(self.windowTitle()+' v'+self.version)
        self.my_ip = None
        self.gzip = False

        # region ### Добавляем метки в статусбар ###
        self.lbst_clients, self.lbst_robots = QtGui.QLabel(self), QtGui.QLabel(self)
        [self.statusBar().addWidget(w) for w in (self.lbst_clients, self.lbst_robots)]
        # endregion

        # region ### Заполняем фильтры ###
        self.lv_Clients.setSelectionMode(3)
        self.lv_Clients.uniformItemSizes = True
        self.lv_Clients.setModel(MyListModel(self, gui.filters["clients"]['tQuery_select'], 'clients'))
        self.connect(self.lv_Clients, QtCore.SIGNAL("clicked(QModelIndex)"), lambda x: self.setFilter(0))
        self.lv_Strategies.setSelectionMode(3)
        self.lv_Strategies.setModel(MyListModel(self, gui.filters['strategies']['tQuery_select'], 'strategies'))
        self.connect(self.lv_Strategies, QtCore.SIGNAL("clicked(QModelIndex)"), lambda x: self.setFilter(1))
        self.connect(self.clearFilter, QtCore.SIGNAL("clicked()"), self.unsetFilterAll)
        # endregion

        # region ### Инициализируем сводную таблицу ###
        basemodelSvod = MonitorTableModel(self, gui.tables['summary_table']['tQuery_select'],
                                          list(gui.tables['summary_table']['header']))
        results, month = [' Итого'], ''
        for column in range(gui.tables['summary_table']['header'].index('За месяц '),
                            len(gui.tables['summary_table']['header'])):
            if column in range(gui.tables['summary_table']['header'].index('За месяц '),
                               gui.tables['summary_table']['header'].index('Срок вложения')) or column == (
            gui.tables['summary_table']['header'].index('')):
                sum = 0
                for row in range(len(basemodelSvod.rows)):
                    if basemodelSvod.rows[row][column] is not None:
                        try:
                            sum += basemodelSvod.rows[row][column]
                        except:
                            month = datetime.strftime(basemodelSvod.rows[row][column], '%m.%Y')
            else:
                sum = ''
            results.append(sum)
        basemodelSvod.header[1] = (basemodelSvod.header[1]+month) if month else 'За послед. месяц'
        basemodelSvod.rows.append(results)
        basemodelSvod.setObjectName('tableSvodModel')
        self.tableSvodModel = SortingProxyModel(self)
        self.tableSvodModel.setSourceModel(basemodelSvod)
        self.tableSvod.setModel(self.tableSvodModel)
        self.tableSvod.setColumnHidden(len(self.tableSvod.model().sourceModel().header)-1, True)
        self.tableSvod.verticalHeader().hide()
        self.tableSvod.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableSvod.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tableSvod.horizontalHeader().setMinimumSectionSize(-1)
        self.tableSvod.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.tableSvod.horizontalHeader().setResizeMode(4, QtGui.QHeaderView.Interactive)
        self.tableSvod.resizeColumnsToContents()
        self.tableSvod.horizontalHeader().setSortIndicator(gui.tables['summary_table']['header'].index('Клиент'),
                                                           QtCore.Qt.DescendingOrder)
        self.tableSvod.sortByColumn(gui.tables['summary_table']['header'].index('Клиент'))
        # endregion

        # region ### Инициализируем таблицу позиций по инструментам ###
        self.modelPos = MonitorTableModel(self, gui.tables['positions']['tQuery_select'],
                                          list(gui.tables['positions']['header']))
        self.tvPos.setUpdatesEnabled(False)
        self.tvPos.setModel(self.modelPos)
        self.tvPos.setAutoScroll(False)
        self.tvPos.verticalHeader().hide()
        self.tvPos.setAlternatingRowColors(True)
        self.tvPos.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tvPos.horizontalHeader().setMinimumSectionSize(-1)
        self.tvPos.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.tvPos.horizontalHeader().setResizeMode(3, QtGui.QHeaderView.Interactive)
        self.tvPos.resizeColumnsToContents()
        self.tvPos.horizontalHeader().setSortIndicator(10, QtCore.Qt.DescendingOrder)
        self.tvPos.sortByColumn(10)
        self.tvPos.customContextMenuRequested.connect(lambda pos: self.create_popup(pos, self.tvPos))
        self.tvPos.setUpdatesEnabled(True)
        # endregion

        # region ### Инициализируем таблицу инструментов ###
        self.modelInstr = MonitorTableModel(self, gui.tables['instruments']['tQuery_select'],
                                            list(gui.tables['instruments']['header']))
        self.modelInstr.setObjectName('tvInstrModel')
        self.tvInstr.setUpdatesEnabled(False)
        self.tvInstr.setModel(self.modelInstr)
        self.tvInstr.verticalHeader().hide()
        self.tvInstr.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tvInstr.horizontalHeader().setMinimumSectionSize(-1)
        self.tvInstr.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.tvInstr.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Interactive)
        self.tvInstr.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Interactive)
        self.tvInstr.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Interactive)
        self.tvInstr.resizeRowsToContents()
        self.tvInstr.resizeColumnsToContents()
        self.tvInstr.horizontalHeader().setSortIndicator(0, QtCore.Qt.AscendingOrder)
        self.tvInstr.setSortingEnabled(True)
        self.tvInstr.setUpdatesEnabled(True)
        # endregion

        # region ### Инициализируем справочники###
        menu_actions = [self.ac_clients, self.ac_strategy, self.ac_counts, self.ac_withdrawal]
        [self.connect(action, QtCore.SIGNAL("triggered()"), self.init_ref) for action in menu_actions]
        # endregion

        # region ### Заполняем меню Help###
        self.connect(self.ac_about, QtCore.SIGNAL("triggered()"), self.about_program)
        # endregion

        # region ### Инициализируем таблицу остатков по деньгам ###
        self.modelMoney = MonitorTableModel(self, gui.tables['restrictions']['tQuery_select'],
                                            list(gui.tables['restrictions']['header']))
        self.tvMoney.setUpdatesEnabled(False)
        self.tvMoney.setModel(self.modelMoney)
        self.tvMoney.setAutoScroll(False)
        self.tvMoney.verticalHeader().hide()
        self.tvMoney.setAlternatingRowColors(True)
        self.tvMoney.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tvMoney.horizontalHeader().setSortIndicator(8, QtCore.Qt.DescendingOrder)
        self.tvMoney.horizontalHeader().setMinimumSectionSize(-1)
        self.tvMoney.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.tvMoney.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Interactive)
        self.tvMoney.sortByColumn(8)
        self.tvMoney.customContextMenuRequested.connect(lambda pos: self.create_popup(pos, self.tvMoney))
        self.connect(self.check_null_acc, QtCore.SIGNAL("stateChanged(int)"), lambda x: self.rest_select_change(x))
        self.check_null_acc.setCheckState(2)
        self.tvMoney.setUpdatesEnabled(True)
        # endregion

        # region ### Управление роботами ###
        self.robotimer = None
        self.srv_ips = list()
        self.bt_close_position.setIcon(self.style().standardIcon(QtGui.QStyle.SP_BrowserStop))
        self.bt_start.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPlay))
        self.bt_stop.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaStop))
        self.rm_connected = False
        self.modelRobo = RobotsTableModel(self)
        self.tvRobots.setUpdatesEnabled(False)
        self.tvRobots.setAutoScroll(False)
        self.tvRobots.setModel(self.modelRobo)
        self.tvRobots.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tvRobots.verticalHeader().hide()
        self.tvRobots.horizontalHeader().setMinimumSectionSize(-1)
        self.tvRobots.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        [self.tvRobots.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Interactive) for i in (0, 4)]
        self.tvRobots.resizeColumnsToContents()
        self.tvRobots.horizontalHeader().setSortIndicator(1, QtCore.Qt.AscendingOrder)
        self.tvRobots.setColumnWidth(0, 30)
        self.tvRobots.setUpdatesEnabled(True)

        self.connect(self.bt_connect, QtCore.SIGNAL("clicked()"), self.connect_slot)
        self.connect(self.bt_robot_connect, QtCore.SIGNAL("clicked()"), self.robot_connect_slot)
        self.connect(self.bt_robot_disconnect, QtCore.SIGNAL("clicked()"), self.robot_disconnect_slot)
        self.connect(self.bt_start, QtCore.SIGNAL("clicked()"), self.start_slot)
        self.connect(self.bt_stop, QtCore.SIGNAL("clicked()"), self.stop_slot)
        self.connect(self.bt_close_position, QtCore.SIGNAL("clicked()"), self.close_position_slot)
        self.connect(self.ch_select_all, QtCore.SIGNAL("stateChanged(int)"), self.check_all)
        self.pushers = dict()
        self.pullers = dict()
        self.checkbox = None
        self.layout_checkbox = None
        self.checkbox_widget = None
        # endregion

        # region ### Фильтры роботов ###
        self.leFltClient.focusInEvent = lambda evt: self.leFltClient.clear()
        self.leFltStrategy.focusInEvent = lambda evt: self.leFltStrategy.clear()
        self.leFltState.focusInEvent = lambda evt: self.leFltState.clear()
        self.leFltClient.textChanged.connect(lambda txt: self.modelRobo.setFilter('clt', txt))
        self.leFltStrategy.textChanged.connect(lambda txt: self.modelRobo.setFilter('strategy', txt))
        self.leFltState.textChanged.connect(lambda txt: self.modelRobo.setFilter('state', txt))
        # endregion

        # region ### Ежедневный отчёт ###
        self.dreport = None
        self.connect(self.ac_daily, QtCore.SIGNAL("triggered()"), self.daily_report)
        # endregion

        # region ### Запускаем таймеры ###
        tmrPos, tmrMoney, tmrInstr = QtCore.QTimer(self), QtCore.QTimer(self), QtCore.QTimer(self)
        tmrPos.timeout.connect(lambda: self.__update_data(self.tvPos))
        tmrMoney.timeout.connect(lambda: self.__update_data(self.tvMoney))
        tmrInstr.timeout.connect(lambda: self.__update_data(self.tvInstr))
        tmrPos.start(2000)
        tmrMoney.start(2000)
        tmrInstr.start(1000)
        # endregion

    def daily_report(self):
        self.report = DailyReport()
        self.report.show()

    def rest_select_change(self, check_state):
        if check_state == 0:
            self.modelMoney._query = gui.tables['restrictions']['tQuery_select_notnull']
        else:
            self.tvMoney.model()._query = gui.tables['restrictions']['tQuery_select']

    def create_popup(self, position, tv):
        index = tv.currentIndex()
        firm = tv.model().rows[index.row()][1 if tv.objectName() == 'tvMoney' else 2]
        acc = tv.model().rows[index.row()][2 if tv.objectName() == 'tvMoney' else 3]
        self.act_orders = QtGui.QAction('Заявки', self)
        self.act_orders.setObjectName('act_orders')
        self.act_trades = QtGui.QAction('Сделки', self)
        self.act_trades.setObjectName('act_trades')
        self.act_csv_export = QtGui.QAction('Выгрузка в csv', self)
        self.act_csv_export.setObjectName('act_csv_export')
        self.act_trades.triggered.connect(lambda: self.choose_data(firm, acc))
        self.act_orders.triggered.connect(lambda: self.choose_data(firm, acc))
        self.act_csv_export.triggered.connect(lambda: self.load_data(tv.model().sourceModel().rows))
        menu = QtGui.QMenu(self)
        menu.addAction(self.act_orders)
        menu.addAction(self.act_trades)
        menu.addAction(self.act_csv_export)
        menu.popup(tv.viewport().mapToGlobal(position))

    def closeEvent(self, QCloseEvent):
        if self.robotimer is not None: self.robotimer.stop()
        [p.pusher_finalize() for p in self.pushers.values()]
        [p.puller_finalize() for p in self.pullers.values()]
        db.__del__()
        QCloseEvent.accept()

    def about_program(self):
        QtGui.QMessageBox.about(self, "О программе",
                                "<div style='margin:10px;'><b>ООО ИК МультиБотСистемс<br><br>Система риск-менеджмента</b></div>"
                                "<div style='margin:20px;'> (с) 2016 Версия "+self.version+"</div>")

    def init_ref(self):
        self.tableCl = RefTable(self, ac_name = self.sender().objectName())
        self.tableCl.exec_()

    def __update_data(self, tableview):
        if self.tabWidget.currentIndex() > 0: return

        tableview.setUpdatesEnabled(False)
        tableview.setSortingEnabled(False)
        sel = tableview.selectionModel().selectedRows()
        sortCol = tableview.horizontalHeader().sortIndicatorSection()
        tableview.model().layoutAboutToBeChanged.emit()
        tableview.model().updateData()
        tableview.model().layoutChanged.emit()
        if len(sel) > 0: tableview.setCurrentIndex(sel[0])
        tableview.setSortingEnabled(True)
        tableview.sortByColumn(sortCol)
        tableview.setUpdatesEnabled(True)
        if self.lv_Clients.model() is not None: self.lbst_clients.setText(
            'Клиентов: '+str(len(self.lv_Clients.model().rows)))

    def load_data(self, rows):
        loader = CSVLoader()
        loader.write(rows)

    def choose_data(self, firm, account):
        self.tableDataInfo = TableInfo(self, acc = account, firm = firm, ac_name = self.sender().objectName())
        self.tableDataInfo.exec_()

    def unsetFilterAll(self):
        [flt.clearSelection() for flt in (self.lv_Clients, self.lv_Strategies)]
        for mdl in (self.tvPos.model(), self.tvMoney.model()):
            mdl.setFilterRegExp('')

    def setFilter(self, flt_column = 0):
        flt_keys = []
        [flt_keys.append(self.sender().model().data(fl, QtCore.Qt.DisplayRole)) for fl in
         self.sender().selectedIndexes()]
        for mdl in (self.tvPos.model(), self.tvMoney.model()):
            mdl.setFilterKeyColumn(flt_column)
            mdl.setFilterRegExp(QtCore.QRegExp('|'.join(flt_keys)))

    # region ### Управление роботами
    def check_all(self, all_checked):
        """checkbox ch_select_all slot"""
        self.modelRobo.check_all(all_checked)

    def send_command(self, srv_ip, self_addr, command, target_addr = None):
        if srv_ip in self.pushers.keys() and (self.my_ip is not None):
            command_message = dict()
            command_message['unit_type'] = 'client'
            command_message['state'] = 'программа запущена'
            command_message['command'] = command
            command_message['source_addr'] = self_addr
            if target_addr:
                command_message['target_addr'] = target_addr

            if self.pushers[srv_ip] is not None:
                if self.gzip:
                    self.pushers[srv_ip].send_zcompressed(command_message)
                else:
                    self.pushers[srv_ip].send_json(command_message)

    def is_selected(self):
        if not self.modelRobo.is_any_checked():
            QtGui.QMessageBox.warning(self, "Выберите робота", 'Ни один робот не выбран для данного действия.',
                                      QtGui.QMessageBox.NoButton)
            return True
        return False

    def mass_send(self, command):
        for robot in [r for r in self.modelRobo.rows if r[0]]:
            print(command, robot)
            self.send_command(robot[8], self.pullers[robot[8]].address, command, robot[6])

    def pull_cb(self, srv_ip, message):
        if 'ok_register' in message:
            print(srv_ip, message)
            return
        if self.tabWidget.currentIndex() != 1: return

        self.tvRobots.setUpdatesEnabled(False)
        self.tvRobots.setSortingEnabled(False)
        sel = self.tvRobots.selectionModel().selectedRows()
        sortCol = self.tvRobots.horizontalHeader().sortIndicatorSection()
        self.modelRobo.beginResetModel()
        self.modelRobo.updateData(srv_ip, message)
        self.modelRobo.endResetModel()
        self.lbst_robots.setText('Роботов: '+str(len(self.modelRobo.rows)))
        if len(sel) > 0: self.tvRobots.setCurrentIndex(sel[0])
        self.tvRobots.setSortingEnabled(True)
        self.tvRobots.sortByColumn(sortCol)
        self.tvRobots.setUpdatesEnabled(True)

    def robotimerEvent(self):
        for ip in self.pullers:
            self.send_command(ip, self.pullers[ip].address, 'show_units')
            self.pullers[ip].puller_routine()

    def connect_slot(self):
        if self.rm_connected: return
        self.my_ip = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]
        if len(self.my_ip) == 0:
            self.my_ip = None
            QtGui.QMessageBox.warning(self, "Ошибка определения ip-адреса",
                                      "Не найден ip-адрес, отличный от localhost\n"+str(self.my_ip),
                                      QtGui.QMessageBox.NoButton)
        else:
            self.my_ip = self.my_ip[0]

        cfg = QtCore.QSettings('settings', QtCore.QSettings.IniFormat)
        self.srv_ips = cfg.value('network/srv_ip') or ['192.168.9.3']
        self.gzip = cfg.value('network/gzip') == 'true'
        srv_port = cfg.value('network/srv_port') or 6512

        i = 0
        for ip in self.srv_ips:
            if not network.validIP(ip): continue
            pull = network.Puller(lambda idx, msg: self.pull_cb(self.srv_ips[idx], json.loads(msg.decode('utf-8'))),
                                  zcompressed = self.gzip)
            pull.puller_initialize(self.my_ip, 9070+i)
            self.pullers[ip] = pull
            push = network.Pusher()
            push.pusher_initialize('tcp://'+ip+':'+str(srv_port))
            self.pushers[ip] = push
            i += 1

        self.robotimer = QtCore.QTimer(self)
        self.robotimer.timeout.connect(self.robotimerEvent)
        self.robotimer.start(1000)  # интервал 1 секунда

        self.bt_connect.setStyleSheet('background-color:rgba(50,200,20,100);')
        self.lb_last_command.setText('Подключиться')
        self.rm_connected = True

    def robot_connect_slot(self):
        if self.is_selected():
            reply = QtGui.QMessageBox.No
        else:
            reply = QtGui.QMessageBox.question(self, 'Подключение роботов',
                                               "Вы уверены, что хотите подключить выбранных роботов?",
                                               buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                               defaultButton = QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.mass_send('quik_connect')
            self.lb_last_command.setText('Подключить робота')

    def robot_disconnect_slot(self):
        if self.is_selected():
            reply = QtGui.QMessageBox.No
        else:
            reply = QtGui.QMessageBox.question(self, 'Отключение роботов',
                                               "Вы уверены, что хотите отключить выбранных роботов?",
                                               buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                               defaultButton = QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.mass_send('quik_disconnect')
            self.lb_last_command.setText('Отключить робота')

    def start_slot(self):
        if self.is_selected():
            reply = QtGui.QMessageBox.No
        else:
            reply = QtGui.QMessageBox.question(self, 'Запуск роботов',
                                               "Вы уверены, что хотите запустить выбранных роботов?",
                                               buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                               defaultButton = QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.mass_send('start_trading')
            self.lb_last_command.setText('Старт')

    def stop_slot(self):
        if self.is_selected():
            reply = QtGui.QMessageBox.No
        else:
            reply = QtGui.QMessageBox.question(self, 'Остановка роботов',
                                               "Вы уверены, что хотите остановить выбранных роботов?",
                                               buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                               defaultButton = QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.mass_send('stop_trading')
            self.lb_last_command.setText('Стоп')

    def close_position_slot(self):
        if self.is_selected():
            reply = QtGui.QMessageBox.No
        else:
            reply = QtGui.QMessageBox.question(self, 'Закрытие позиций',
                                               "Вы уверены, что хотите закрыть позиции по выбранным роботам?",
                                               buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                               defaultButton = QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.mass_send('close_position')
            self.lb_last_command.setText('Закрыть всё')

            # endregion
