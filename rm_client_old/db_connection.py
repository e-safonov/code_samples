import psycopg2
from singleton import Singleton


class DBException(Exception):
    def __init__(self, pgcode, description = ''):
        super(DBException, self).__init__()
        self.pgcode, self.description = pgcode, description


class DBconnection(metaclass = Singleton):
    """Класс соединения с базой данных, локализует в себе методы работы с СУБД"""
    dsn = ""

    def __init__(self):
        self.State = 0  # Состояние соединения (1 - установленно; 0 - не установленно)
        self.__conn = None
        self.connect2DB(self.dsn)

    def connect2DB(self, aConn_str):
        if self.State == 1: return
        try:
            self.__conn = psycopg2.connect(aConn_str)
            self.State = 1
        except psycopg2.Error as e:
            self.__conn.rollback()
            print("Ошибка подключения к базе: ", str(e))
            self.State = 0
            raise DBException(e.pgcode, 'Ошибка подключения к базе данных {0}'.format(e))

    def DBGetData(self, aRequest, params = None):
        if self.State != 1: return None
        rows = None
        try:
            with self.__conn.cursor() as cur:
                cur.execute(aRequest, params)
                rows = cur.fetchall()
        except psycopg2.Error as e:
            self.__conn.rollback()
            print("Выполнение запроса: ", str(e))
            raise DBException(e.pgcode, 'Выполнение запроса {0}'.format(e))
        return rows  # Список кортежей с результатами запроса

    def DBUpdateData(self, aRequest, params):
        try:
            with self.__conn.cursor() as cur:
                cur.execute(aRequest, params)
                self.__conn.commit()
                try:
                    rid = cur.fetchone()[0]
                except:
                    rid = None
        except psycopg2.Error as e:
            self.__conn.rollback()
            print("Обновление данных: ", str(e))
            raise DBException(e.pgcode, 'Обновление данных {0}'.format(e))
        except Exception as ex:
            print('Req: {0}\nParams: {1}'.format(aRequest, params))
        return rid

    def DBGetHeader(self, aRequest, params = None, NumSeq = 0):
        """
        Функция получает заголовок запроса
        :param aRequest:
        :param NumSeq: 0<=NumSeq<=6  (0 - name, 1 - type _code , 2 - display_size ...)
        :return: список заголовков полей
        """
        header = []
        try:
            with self.__conn.cursor() as cur:
                cur.execute(aRequest, params)
                for v in cur.description:
                    header.append(str(v[NumSeq]))
        except psycopg2.Error as e:
            self.__conn.rollback()
            print("Ошибка выполнения запроса: ", str(e))
            raise DBException(e.pgcode, 'Обновление данных {0}'.format(e))
        return header

    def __del__(self):
        self.__conn.close()
        self.State = 0
