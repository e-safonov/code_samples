tblHeaders = {
    'positions':  (
                    "Клиент",
                    "Стратегия",
                    "Фирма",
                    "Счёт",
                    "Инструмент",
                    "Акт. покупка",
                    "Акт. продажа",
                    "Куплено",
                    "Продано",
                    "Тек. чист.",
                    "Вар.маржа"
                    ),
    'restrictions': (
                     "Клиент",
                     "Фирма",
                     "Торговый счет",
                     "Тип лимита",
                     "Пред. лимит",
                     "Тек. лимит",
                     "Тек.чист.",
                     "План.чист.поз.",
                     "Вар.маржа",
                     "Накопл.доход",
                     "Комиссия"
                    ),
    'ref_clients': (
                    "Фирма",
                    "Клиент",
                    "Телефон"
                    ),
    'ref_accounts': (
                    "Счет",
                     "Мин. план.чист.",
                    "Клиент",
                    "Стратегия",
                    'Инструмент',
                    'Лист в отчёте',
                    'IP сервера РМ',
                    'IP:port робота'
                    ),
    'ref_strategies': ("Название"),
    'tableSvod': (
                    "Клиент",
                    "За месяц ",
                    "За послед. неделю",
                    "Доход", "Сумма",
                    "Срок вложения",
                    'Доходность',
                    'Стратегия',
                    'Лот',
                    'Количество сделок',
                    ''
                ),
    'orders': (
                'Дата',
                'Время',
                'Активация',
                'Снятие',
                'Номер',
                'Код бумаги',
                'Код класса',
                'Цена',
                'Кол-во',
                'Остаток',
                'Операция',
                'Статус',
                'Объем',
                'Валюта',
                'Счет',
                'Комментарий',
                'Связ. заявка',
                'ID транз.',
                'Доходность',
                'Купонный %',
                'Трейдер',
                'UID',
                'Цена выкупа',
                'Срок'
                ),
    'trades': (
                'Дата',
                'Время',
                'Номер',
                'Номер заявки',
                'Код бумаги',
                'Код класса',
                'Цена', 'Кол-во',
                'Операция',
                'Объем',
                'Валюта',
                'Счет',
                'Комментарий',
                'Доходность',
                'Купонный %',
                'Комиссия ТС',
                'Клиринговая комиссия',
                'ФБ комиссия',
                'ТЦ комиссия',
                'Трейдер',
                'Цена выкупа'
                ),
    'withdrawals': (
                    'Счет',
                    'Фирма',
                    'Клиент',
                    'Дата/время',
                    'Сумма'
                ),
    'robots': (
                '',
                'Клиент',
                'Стратегия',
                'Прибыль',
                'Позиция',
                'Состояние',
                'IP-адрес робота',
                'Версия ПО'
             ),
    'instruments': (
                    'Инструмент',
                    'Позиция',
                    'Тек.цена',
                    '% '
                )
}

tables = {
    'summary_table': {'header': tblHeaders['tableSvod'], 'tQuery_select': 'select * from get_summary_table(0);'},
    'positions'    : {'header': tblHeaders['positions'], 'tQuery_select': 'select * from vw_positions;'},
    'restrictions' : {
                      'header': tblHeaders['restrictions'],
                       'tQuery_select': 'select * from vw_restrictions;',
                      'tQuery_select_notnull': 'select * from vw_restrictions where varmargin <> 0;'
                     },
    'instruments'  : {'header': tblHeaders['instruments'],
                      'tQuery_select': 'select * from get_instruments_summary(0);'
                    }
}

actions = {
    'ac_clients': {
                   'title': 'Клиенты',
                   'header': tblHeaders['ref_clients'],
                   'tQuery_select': 'SELECT *  FROM vw_clients;',
                   'tQuery_update': 'UPDATE ref_clients SET firm_name=%s, client_name=%s, phone=%s \
                                     WHERE client_id=%s;',
                   'tQuery_insert': "INSERT INTO ref_clients (firm_name, client_name, phone) \
                                     VALUES (%s, %s, %s) RETURNING client_id;",
                   'tQuery_delete': "DELETE FROM ref_clients WHERE client_id=%s;"
                  },
    'ac_strategy': {
                    'title': 'Стратегии',
                    'header': tblHeaders['ref_strategies'],
                    'tQuery_select': "SELECT name, id  FROM ref_strategies;",
                    'tQuery_update': 'UPDATE ref_strategies SET name=%s WHERE id=%s;',
                    'tQuery_insert': "INSERT INTO ref_strategies (name) VALUES (%s) RETURNING id;",
                    'tQuery_delete': "DELETE FROM ref_strategies WHERE id=%s;"
                  },
    'ac_counts': {
                  'title': 'Счета',
                  'header': tblHeaders['ref_accounts'],
                  'tQuery_select': 'select * from vw_accounts;',
                  'tQuery_update': 'UPDATE ref_accounts SET account=%s, planned_min_limit=%s, client_id=%s,  '
                                    'strategy_id=%s, sec_id=%s, excel_name=%s, robot_srv_ip=%s, robot_ip_port=%s \
                                    WHERE account_id=%s;',
                  'tQuery_insert': 'INSERT INTO ref_accounts (account, planned_min_limit, client_id, \
                                    strategy_id, sec_id, excel_name, robot_srv_ip, robot_ip_port) '
                                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING account_id;',
                  'tQuery_delete': 'DELETE FROM ref_accounts WHERE account_id=%s;'
                 },
    'ac_withdrawal': {
                      'title': 'Операции ввода/вывода',
                      'header': tblHeaders['withdrawals'],
                      'tQuery_select': 'select * from vw_withdrawal;',
                      'tQuery_update': 'UPDATE account_withdrawal SET account_id=%s, with_datetime=%s, nsum=%s ,\
                                        firmid=%s, traccid=%s WHERE id=%s;',
                       'tQuery_insert': 'INSERT INTO account_withdrawal (account_id, with_datetime, nsum,\
                                        firmid, traccid) VALUES (%s, %s, %s, %s, %s) RETURNING id;',
                       'tQuery_delete': 'DELETE FROM account_withdrawal WHERE id=%s;'
                    },
    'act_orders': {
                  'title': 'Заявки ',
                   'header': tblHeaders['orders'],
                   'tQuery_select': "select * from orders_by_account(%s, %s, %s, %s);"
                  },
    'act_trades': {
                   'title': 'Сделки ',
                   'header': tblHeaders['trades'],
                    'tQuery_select': "select * from trades_by_account(%s, %s, %s, %s);"
                 }
}

filters = {
    'clients': {
                'tQuery_select': "select client_name, client_id from ref_clients ORDER BY client_name;",
                'id': 'client_id'
               },
    'strategies': {
                   'tQuery_select': "select name, id from ref_strategies ORDER BY name;",
                   'id': 'strategy_id'
                 },
    'firms': {
              'tQuery_select': "select firm_name, client_id from ref_clients WHERE client_id=%s or client_id<%s;",
               'id': 'client_id'
             },
    'accounts': {
                 'tQuery_select': "select account, account_id from ref_accounts \
                 WHERE client_id=%s or client_id<%s order by account;",
                 'id': 'account_id'
               },
    'instruments': {
                    'tQuery_select': "select sec_code, sec_id from ref_instruments ORDER BY sec_code;",
                    'id': 'sec_id'
                 }
}
