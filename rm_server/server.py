import json
import network
from threads import PyTPThread, run_threads


class RiskManagerServer:
    def __init__(self):
        self.robo_commands = (
            'quik_connect',
            'quik_disconnect',
            'start_trading',
            'stop_trading',
            'close_position'
        )
        self.is_connected = False
        self.pushers = dict()
        self.units = dict()
        self.puller  = None
        self.th_pull = None

    def connect(self):

        self.puller = network.Puller(self.pull_cb)

        try:
            self.puller.puller_initialize('0.0.0.0', 9900)
        except Exception as e:
            self.is_connected = False
            print("Can't initialize PULL, exiting...")
            return
        self.th_pull = PyTPThread(rest_interval = 0.01)
        self.th_pull.finalizers.append(self.puller.puller_finalize)
        self.th_pull.routines.append(self.puller.puller_routine)
        run_threads((self.th_pull,))
        self.is_connected = True

    def register(self, message):
        pusher = network.Pusher()
        address = message['source_addr']
        pusher.pusher_initialize(address)
        self.pushers[address] = pusher
        message['state_count'] = 0
        self.units[address] = message
        pusher.send_json(('ok_register', message['source_addr'],))

    def print_units(self, unit_type):
        """Вывод списка клиентов и/или роботов на локальную консоль"""
        if unit_type == 'all':
            print('robots: \n')
            for address in self.units:
                print(address+' '+self.units[address]['state'])

    def pull_cb(self, message):
        message = json.loads(message.decode('cp1252'))

        source_addr = message['source_addr']
        if source_addr not in self.pushers:
            self.register(message)
            print('regitster unit '+source_addr)

        self.units[source_addr]['state_count'] = 0

        if message['unit_type'] == 'client':
            if message['command'] in self.robo_commands:
                self.pushers[message['target_addr']].send_json((message['command'], message['source_addr'],))
                print(message['command'], message['target_addr'])
            elif message['command'] == 'show_units':
                self.pushers[message['source_addr']].send_json(self.units)

        elif message['unit_type'] == 'robot':
            self.units[source_addr]['state'] = message['state']
            if 'pos' in message.keys():
                self.units[source_addr]['pos'] = message['pos']

    def unit_check(self, unit):
        unit['state_count'] += 1
        # print("state_count=" + str(unit['state_count']))

        if unit['state_count'] == 10:
            unit['state'] = 'dead'

            if unit['source_addr'] in self.pushers.keys():
                pshr = self.pushers.pop(unit['source_addr'])
                pshr.pusher_finalize()

        elif unit['state_count'] >= 15:
            self.units.pop(unit['source_addr'])

    def check_units(self):
        for address in list(self.units):
            self.unit_check(self.units[address])
