# -*- coding: utf-8 -*-
'''
python -m pip install pyserial
python -m pip install paho-mqtt
'''
import os
import os.path
import serial
import socket
import time
import platform
import threading
import json
import logging
import logging.config
import logging.handlers
import configparser
import paho.mqtt.client as mqtt
from collections import OrderedDict

# Version
SW_VERSION = 'RS485 Compilation 1.0.3b'
# Log Level
CONF_LOGLEVEL = 'info' # debug, info, warn

###############################################################################################################
################################################## K O C O M ##################################################
# 본인에 맞게 수정하세요

# 보일러 초기값
INIT_TEMP = 22
# 환풍기 초기속도 ['low', 'medium', 'high']
DEFAULT_SPEED = 'medium'
# 조명 / 플러그 갯수
KOCOM_LIGHT_SIZE            = {'livingroom': 3, 'bedroom': 2, 'room1': 2, 'room2': 2, 'kitchen': 3}
KOCOM_PLUG_SIZE             = {'livingroom': 2, 'bedroom': 2, 'room1': 2, 'room2': 2, 'kitchen': 2}

# 방 패킷에 따른 방이름 (패킷1: 방이름1, 패킷2: 방이름2 . . .)
# 월패드에서 장치를 작동하며 방이름(livingroom, bedroom, room1, room2, kitchen 등)을 확인하여 본인의 상황에 맞게 바꾸세요
# 조명/콘센트와 난방의 방패킷이 달라서 두개로 나뉘어있습니다.
KOCOM_ROOM                  = {'00': 'livingroom', '01': 'bedroom', '02': 'room2', '03': 'room1', '04': 'kitchen'}
KOCOM_ROOM_THERMOSTAT       = {'00': 'livingroom', '01': 'bedroom', '02': 'room1', '03': 'room2'}

# TIME 변수(초)
SCAN_INTERVAL = 300         # 월패드의 상태값 조회 간격
SCANNING_INTERVAL = 0.8     # 상태값 조회 시 패킷전송 간격
####################### Start Here by Zooil ###########################
option_file = '/data/options.json'                                                                                             
if os.path.isfile(option_file):                                                                                                
    with open(option_file) as json_file:                                                                                   
        json_data = json.load(json_file)                                                                               
        INIT_TEMP = json_data['Advanced']['INIT_TEMP']                                                                 
        SCAN_INTERVAL = json_data['Advanced']['SCAN_INTERVAL']                                                         
        SCANNING_INTERVAL = json_data['Advanced']['SCANNING_INTERVAL'] 
        DEFAULT_SPEED = json_data['Advanced']['DEFAULT_SPEED'] 
        CONF_LOGLEVEL = json_data['Advanced']['LOGLEVEL']
        KOCOM_LIGHT_SIZE = {} 
        dict_data = json_data['KOCOM_LIGHT_SIZE']                                                               
        for i in dict_data:
            KOCOM_LIGHT_SIZE[i['name']] = i['number'] 
        KOCOM_PLUG_SIZE = {} 
        dict_data = json_data['KOCOM_PLUG_SIZE']                                                               
        for i in dict_data:
            KOCOM_PLUG_SIZE[i['name']] = i['number'] 
        num = 0
        KOCOM_ROOM = {}
        list_data = json_data['KOCOM_ROOM']                                                                           
        for i in list_data:
            if num < 10:
                num_key = "0%d" % (num)
            else:           
                num_key = "%d" % (num)
            KOCOM_ROOM[num_key] = i
            num += 1
        num = 0
        KOCOM_ROOM_THERMOSTAT = {}
        list_data = json_data['KOCOM_ROOM_THERMOSTAT']                                                                           
        for i in list_data:
            if num < 10:
                num_key = "0%d" % (num)
            else:
                num_key = "%d" % (num)
            KOCOM_ROOM_THERMOSTAT[num_key] = i
            num += 1         
####################### End Here by Zooil ########################### 
###############################################################################################################

###############################################################################################################
################################################# 수 정 금 지 ##################################################
################################################# 수 정 금 지 ##################################################
################################################# 수 정 금 지 ##################################################
###############################################################################################################

# HA MQTT Discovery
HA_PREFIX = 'homeassistant'
HA_SWITCH = 'switch'
HA_LIGHT = 'light'
HA_CLIMATE = 'climate'
HA_SENSOR = 'sensor'
HA_FAN = 'fan'

# DEVICE 명명
DEVICE_WALLPAD = 'wallpad'
DEVICE_LIGHT = 'light'
DEVICE_THERMOSTAT = 'thermostat'
DEVICE_PLUG = 'plug'
DEVICE_GAS = 'gas'
DEVICE_ELEVATOR = 'elevator'
DEVICE_FAN = 'fan'

# KOCOM 코콤 패킷 기본정보
KOCOM_DEVICE                = {'01': DEVICE_WALLPAD, '0e': DEVICE_LIGHT, '36': DEVICE_THERMOSTAT, '3b': DEVICE_PLUG, '44': DEVICE_ELEVATOR, '2c': DEVICE_GAS, '48': DEVICE_FAN}
KOCOM_COMMAND               = {'3a': '조회', '00': '상태', '01': 'on', '02': 'off'}
KOCOM_TYPE                  = {'30b': 'send', '30d': 'ack'}
KOCOM_FAN_SPEED             = {'4': 'low', '8': 'medium', 'c': 'high', '0': 'off'}
KOCOM_DEVICE_REV            = {v: k for k, v in KOCOM_DEVICE.items()}
KOCOM_ROOM_REV              = {v: k for k, v in KOCOM_ROOM.items()}
KOCOM_ROOM_THERMOSTAT_REV   = {v: k for k, v in KOCOM_ROOM_THERMOSTAT.items()}
KOCOM_COMMAND_REV           = {v: k for k, v in KOCOM_COMMAND.items()}
KOCOM_TYPE_REV              = {v: k for k, v in KOCOM_TYPE.items()}
KOCOM_FAN_SPEED_REV         = {v: k for k, v in KOCOM_FAN_SPEED.items()}
KOCOM_ROOM_REV[DEVICE_WALLPAD] = '00'

# KOCOM TIME 변수
KOCOM_INTERVAL = 100
VENTILATOR_INTERVAL = 150

# GREX 그렉스 전열교환기 패킷 기본정보
GREX_MODE                   = {'0100': 'auto', '0200': 'manual', '0300': 'sleep', '0000': 'off'}
GREX_SPEED                  = {'0101': 'low', '0202': 'medium', '0303': 'high', '0000': 'off'}

# CONFIG 파일 변수값
CONF_FILE = 'rs485.conf'
CONF_LOGFILE = 'rs485.log'
CONF_LOGNAME = 'RS485'
CONF_WALLPAD = 'Wallpad'
CONF_MQTT = 'MQTT'
CONF_DEVICE = 'RS485'
CONF_SERIAL = 'Serial'
CONF_SERIAL_DEVICE = 'SerialDevice'
CONF_SOCKET = 'Socket'
CONF_SOCKET_DEVICE = 'SocketDevice'

# Log 폴더 생성 (도커 실행 시 로그폴더 매핑)
def make_folder(folder_name):
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
root_dir = str(os.path.dirname(os.path.realpath(__file__)))
log_dir = root_dir + '/log/'
make_folder(log_dir)
conf_path = str(root_dir + '/'+ CONF_FILE)
log_path = str(log_dir + '/' + CONF_LOGFILE)

class rs485:
    def __init__(self):
        self._mqtt_config = {}
        self._port_url = {}
        self._device_list = {}
        self._wp_list = {}
        self.type = None

        config = configparser.ConfigParser()
        config.read(conf_path)

        get_conf_wallpad = config.items(CONF_WALLPAD)
        for item in get_conf_wallpad:
            self._wp_list.setdefault(item[0], item[1])
            logger.info('[CONFIG] {} {} : {}'.format(CONF_WALLPAD, item[0], item[1]))

        get_conf_mqtt = config.items(CONF_MQTT)
        for item in get_conf_mqtt:
            self._mqtt_config.setdefault(item[0], item[1])
            logger.info('[CONFIG] {} {} : {}'.format(CONF_MQTT, item[0], item[1]))

        d_type = config.get(CONF_LOGNAME, 'type').lower()
        if d_type == 'serial':
            self.type = d_type
            get_conf_serial = config.items(CONF_SERIAL)
            port_i = 1
            for item in get_conf_serial:
                if item[1] != '':
                    self._port_url.setdefault(port_i, item[1])
                    logger.info('[CONFIG] {} {} : {}'.format(CONF_SERIAL, item[0], item[1]))
                port_i += 1

            get_conf_serial_device = config.items(CONF_SERIAL_DEVICE)
            port_i = 1
            for item in get_conf_serial_device:
                if item[1] != '':
                    self._device_list.setdefault(port_i, item[1])
                    logger.info('[CONFIG] {} {} : {}'.format(CONF_SERIAL_DEVICE, item[0], item[1]))
                port_i += 1
            self._con = self.connect_serial(self._port_url)
        elif d_type == 'socket':
            self.type = d_type
            server = config.get(CONF_SOCKET, 'server')
            port = config.get(CONF_SOCKET, 'port')
            self._socket_device = config.get(CONF_SOCKET_DEVICE, 'device')
            self._con = self.connect_socket(server, port)
        else:
            logger.info('[CONFIG] SERIAL / SOCKET IS NOT VALID')
            logger.info('[CONFIG] EXIT RS485')
            exit(1)

    @property
    def _wp_light(self):
        return True if self._wp_list['light'] == 'True' else False

    @property
    def _wp_fan(self):
        return True if self._wp_list['fan'] == 'True' else False

    @property
    def _wp_thermostat(self):
        return True if self._wp_list['thermostat'] == 'True' else False

    @property
    def _wp_plug(self):
        return True if self._wp_list['plug'] == 'True' else False

    @property
    def _wp_gas(self):
        return True if self._wp_list['gas'] == 'True' else False

    @property
    def _wp_elevator(self):
        return True if self._wp_list['elevator'] == 'True' else False

    @property
    def _device(self):
        if self.type == 'serial':
            return self._device_list
        elif self.type == 'socket':
            return self._socket_device

    @property
    def _type(self):
        return self.type

    @property
    def _connect(self):
        return self._con

    @property
    def _mqtt(self):
        return self._mqtt_config

    def connect_serial(self, port):
        ser = {}
        opened = 0
        for p in port:
            try:
                ser[p] = serial.Serial(port[p], 9600, timeout=None)
                if ser[p].isOpen():
                    ser[p].bytesize = 8
                    ser[p].stopbits = 1
                    ser[p].autoOpen = False
                    logger.info('Port {} : {}'.format(p, port[p]))
                    opened += 1
                else:
                    logger.info('시리얼포트가 열려있지 않습니다.[{}]'.format(port[p]))
            except serial.serialutil.SerialException:
                logger.info('시리얼포트에 연결할 수 없습니다.[{}]'.format(port[p]))
        if opened == 0: return False
        return ser

    def connect_socket(self, server, port):
        soc = socket.socket()
        soc.settimeout(10)
        try:
            soc.connect((server, int(port)))
        except Exception as e:
            logger.info('소켓에 연결할 수 없습니다.[{}][{}:{}]'.format(e, server, port))
            return False
        soc.settimeout(None)
        return soc

class Kocom(rs485):
    def __init__(self, client, name, device, packet_len):
        self.client = client
        self._name = name
        self.connected = True

        self.ha_registry = False
        self.kocom_scan = True
        self.scan_packet_buf = []

        self.tick = time.time()
        self.wp_list = {}
        self.wp_light = self.client._wp_light
        self.wp_fan = self.client._wp_fan
        self.wp_plug = self.client._wp_plug
        self.wp_gas = self.client._wp_gas
        self.wp_elevator = self.client._wp_elevator
        self.wp_thermostat = self.client._wp_thermostat
        for d_name in KOCOM_DEVICE.values():
            if d_name == DEVICE_ELEVATOR or d_name == DEVICE_GAS:
                self.wp_list[d_name] = {}
                self.wp_list[d_name][DEVICE_WALLPAD] = {'scan': {'tick': 0, 'count': 0, 'last': 0}}
                self.wp_list[d_name][DEVICE_WALLPAD][d_name] = {'state': 'off', 'set': 'off', 'last': 'state', 'count': 0}
            elif d_name == DEVICE_FAN:
                self.wp_list[d_name] = {}
                self.wp_list[d_name][DEVICE_WALLPAD] = {'scan': {'tick': 0, 'count': 0, 'last': 0}}
                self.wp_list[d_name][DEVICE_WALLPAD]['mode'] = {'state': 'off', 'set': 'off', 'last': 'state', 'count': 0}
                self.wp_list[d_name][DEVICE_WALLPAD]['speed'] = {'state': 'off', 'set': 'off', 'last': 'state', 'count': 0}
            elif d_name == DEVICE_THERMOSTAT:
                self.wp_list[d_name] = {}
                for r_name in KOCOM_ROOM_THERMOSTAT.values():
                    self.wp_list[d_name][r_name] = {'scan': {'tick': 0, 'count': 0, 'last': 0}}
                    self.wp_list[d_name][r_name]['mode'] = {'state': 'off', 'set': 'off', 'last': 'state', 'count': 0}
                    self.wp_list[d_name][r_name]['current_temp'] = {'state': 0, 'set': 0, 'last': 'state', 'count': 0}
                    self.wp_list[d_name][r_name]['target_temp'] = {'state': INIT_TEMP, 'set': INIT_TEMP, 'last': 'state', 'count': 0}
            elif d_name == DEVICE_LIGHT or d_name == DEVICE_PLUG:
                self.wp_list[d_name] = {}
                for r_name in KOCOM_ROOM.values():
                    self.wp_list[d_name][r_name] = {'scan': {'tick': 0, 'count': 0, 'last': 0}}
                    if d_name == DEVICE_LIGHT:
                        for i in range(0, KOCOM_LIGHT_SIZE[r_name] + 1):
                            self.wp_list[d_name][r_name][d_name + str(i)] = {'state': 'off', 'set': 'off', 'last': 'state', 'count': 0}
                    if d_name == DEVICE_PLUG:
                        for i in range(0, KOCOM_PLUG_SIZE[r_name] + 1):
                            self.wp_list[d_name][r_name][d_name + str(i)] = {'state': 'on', 'set': 'on', 'last': 'state', 'count': 0}

        self.d_type = client._type
        if self.d_type == "serial":
            self.d_serial = client._connect[device]
        elif self.d_type == "socket":
            self.d_serial = client._connect
        self.d_mqtt = self.connect_mqtt(self.client._mqtt, name)

        self._t1 = threading.Thread(target=self.get_serial, args=(name, packet_len))
        self._t1.start()
        self._t2 = threading.Thread(target=self.scan_list)
        self._t2.start()

    def connection_lost(self):
        self._t1.join()
        self._t2.join()
        if not self.connected:
            logger.debug('[ERROR] 서버 연결이 끊어져 kocom 클래스를 종료합니다.')
            return False

    def read(self):
        if self.client._connect == False:
            return ''
        try:
            if self.d_type == 'serial':
                if self.d_serial.readable():
                    return self.d_serial.read()
                else:
                    return ''
            elif self.d_type == 'socket':
                return self.d_serial.recv(1)
        except:
            logging.info('[Serial Read] Connection Error')

    def write(self, data):
        if data == False:
            return
        self.tick = time.time()
        if self.client._connect == False:
            return
        try:
            if self.d_type == 'serial':
                return self.d_serial.write(bytearray.fromhex((data)))
            elif self.d_type == 'socket':
                return self.d_serial.send(bytearray.fromhex((data)))
        except:
            logging.info('[Serial Write] Connection Error')

    def connect_mqtt(self, server, name):
        mqtt_client = mqtt.Client()
        mqtt_client.on_message = self.on_message
        #mqtt_client.on_publish = self.on_publish
        mqtt_client.on_subscribe = self.on_subscribe
        mqtt_client.on_connect = self.on_connect

        if server['anonymous'] != 'True':
            if server['server'] == '' or server['username'] == '' or server['password'] == '':
                logger.info('{} 설정을 확인하세요. Server[{}] ID[{}] PW[{}] Device[{}]'.format(CONF_MQTT, server['server'], server['username'], server['password'], name))
                return False
            mqtt_client.username_pw_set(username=server['username'], password=server['password'])
            logger.debug('{} STATUS. Server[{}] ID[{}] PW[{}] Device[{}]'.format(CONF_MQTT, server['server'], server['username'], server['password'], name))
        else:
            logger.debug('{} STATUS. Server[{}] Device[{}]'.format(CONF_MQTT, server['server'], name))

        mqtt_client.connect(server['server'], 1883, 60)
        mqtt_client.loop_start()
        return mqtt_client

    def on_message(self, client, obj, msg):
        _topic = msg.topic.split('/')
        _payload = msg.payload.decode()

        if 'config' in _topic and _topic[0] == 'rs485' and _topic[1] == 'bridge' and _topic[2] == 'config':
            if _topic[3] == 'log_level':
                if _payload == "info": logger.setLevel(logging.INFO)
                if _payload == "debug": logger.setLevel(logging.DEBUG)
                if _payload == "warn": logger.setLevel(logging.WARN)
                logger.info('[From HA]Set Loglevel to {}'.format(_payload))
                return
            elif _topic[3] == 'restart':
                self.homeassistant_device_discovery()
                logger.info('[From HA]HomeAssistant Restart')
                return
            elif _topic[3] == 'remove':
                self.homeassistant_device_discovery(remove=True)
                logger.info('[From HA]HomeAssistant Remove')
                return
            elif _topic[3] == 'scan':
                for d_name in KOCOM_DEVICE.values():
                    if d_name == DEVICE_ELEVATOR or d_name == DEVICE_GAS:
                        self.wp_list[d_name][DEVICE_WALLPAD] = {'scan': {'tick': 0, 'count': 0, 'last': 0}}
                    elif d_name == DEVICE_FAN:
                        self.wp_list[d_name][DEVICE_WALLPAD] = {'scan': {'tick': 0, 'count': 0, 'last': 0}}
                    elif d_name == DEVICE_THERMOSTAT:
                        for r_name in KOCOM_ROOM_THERMOSTAT.values():
                            self.wp_list[d_name][r_name] = {'scan': {'tick': 0, 'count': 0, 'last': 0}}
                    elif d_name == DEVICE_LIGHT or d_name == DEVICE_PLUG:
                        for r_name in KOCOM_ROOM.values():
                            self.wp_list[d_name][r_name] = {'scan': {'tick': 0, 'count': 0, 'last': 0}}
                logger.info('[From HA]HomeAssistant Scan')
                return
            elif _topic[3] == 'packet':
                self.packet_parsing(_payload.lower(), name='HA')
            elif _topic[3] == 'check_sum':
                chksum = self.check_sum(_payload.lower())
                logger.info('[From HA]{} = {}({})'.format(_payload, chksum[0], chksum[1]))
        elif not self.kocom_scan:
            self.parse_message(_topic, _payload)
            return
        logger.info("Message: {} = {}".format(msg.topic, _payload))
        
        if self.ha_registry != False and self.ha_registry == msg.topic and self.kocom_scan:
            self.kocom_scan = False

    def parse_message(self, topic, payload):
        device = topic[1]
        command = topic[3]
        if device == HA_LIGHT or device == HA_SWITCH:
            room_device = topic[2].split('_')
            room = room_device[0]
            sub_device = room_device[1]
            if sub_device.find(DEVICE_LIGHT) != -1:
                device = DEVICE_LIGHT
            if sub_device.find(DEVICE_PLUG) != -1:
                device = DEVICE_PLUG
            if sub_device.find(DEVICE_ELEVATOR) != -1:
                device = DEVICE_ELEVATOR
            if sub_device.find(DEVICE_GAS) != -1:
                device = DEVICE_GAS
            try:
                if device == DEVICE_GAS:
                    if payload == 'on':
                        payload = 'off'
                        logger.info('[From HA]Error GAS Cannot Set to ON')
                    else:
                        self.wp_list[device][room][sub_device][command] = payload
                        self.wp_list[device][room][sub_device]['last'] = command
                elif device == DEVICE_ELEVATOR:
                    if payload == 'off':
                        self.wp_list[device][room][sub_device][command] = payload
                        self.wp_list[device][room][sub_device]['last'] = 'state'
                        self.send_to_homeassistant(device, DEVICE_WALLPAD, payload)
                    else:
                        self.wp_list[device][room][sub_device][command] = payload
                        self.wp_list[device][room][sub_device]['last'] = command
                else:
                    self.wp_list[device][room][sub_device][command] = payload
                    self.wp_list[device][room][sub_device]['last'] = command
                logger.info('[From HA]{}/{}/{}/{} = {}'.format(device, room, sub_device, command, payload))
            except:
                logger.info('[From HA]Error {} = {}'.format(topic, payload))
        elif device == HA_CLIMATE:
            device = DEVICE_THERMOSTAT
            room = topic[2]
            try:
                if command != 'mode':
                    self.wp_list[device][room]['target_temp']['set'] = int(float(payload))
                    self.wp_list[device][room]['mode']['set'] = 'heat'
                    self.wp_list[device][room]['target_temp']['last'] = 'set'
                    self.wp_list[device][room]['mode']['last'] = 'set'
                elif command == 'mode':
                    self.wp_list[device][room]['mode']['set'] = payload
                    self.wp_list[device][room]['mode']['last'] = 'set'
                ha_payload = {
                    'mode': self.wp_list[device][room]['mode']['set'],
                    'target_temp': self.wp_list[device][room]['target_temp']['set'],
                    'current_temp': self.wp_list[device][room]['current_temp']['state']
                }
                logger.info('[From HA]{}/{}/set = [mode={}, target_temp={}]'.format(device, room, self.wp_list[device][room]['mode']['set'], self.wp_list[device][room]['target_temp']['set']))
                self.send_to_homeassistant(device, room, ha_payload)
            except:
                logger.info('[From HA]Error {} = {}'.format(topic, payload))
        elif device == HA_FAN:
            device = DEVICE_FAN
            room = topic[2]
            try:
                if command != 'mode':
                    self.wp_list[device][room]['speed']['set'] = payload
                    self.wp_list[device][room]['mode']['set'] = 'on'
                elif command == 'mode':
                    self.wp_list[device][room]['speed']['set'] = DEFAULT_SPEED if payload == 'on' else 'off'
                    self.wp_list[device][room]['mode']['set'] = payload
                self.wp_list[device][room]['speed']['last'] = 'set'
                self.wp_list[device][room]['mode']['last'] = 'set'
                ha_payload = {
                    'mode': self.wp_list[device][room]['mode']['set'],
                    'speed': self.wp_list[device][room]['speed']['set']
                }
                logger.info('[From HA]{}/{}/set = [mode={}, speed={}]'.format(device, room, self.wp_list[device][room]['mode']['set'], self.wp_list[device][room]['speed']['set']))
                self.send_to_homeassistant(device, room, ha_payload)
            except:
                logger.info('[From HA]Error {} = {}'.format(topic, payload))

    def on_publish(self, client, obj, mid):
        logger.info("Publish: {}".format(str(mid)))

    def on_subscribe(self, client, obj, mid, granted_qos):
        logger.info("Subscribed: {} {}".format(str(mid),str(granted_qos)))

    def on_connect(self, client, userdata, flags, rc):
        if int(rc) == 0:
            logger.info("[MQTT] connected OK")
            self.homeassistant_device_discovery(initial=True)
        elif int(rc) == 1:
            logger.info("[MQTT] 1: Connection refused – incorrect protocol version")
        elif int(rc) == 2:
            logger.info("[MQTT] 2: Connection refused – invalid client identifier")
        elif int(rc) == 3:
            logger.info("[MQTT] 3: Connection refused – server unavailable")
        elif int(rc) == 4:
            logger.info("[MQTT] 4: Connection refused – bad username or password")
        elif int(rc) == 5:
            logger.info("[MQTT] 5: Connection refused – not authorised")
        else:
            logger.info("[MQTT] {} : Connection refused".format(rc))

    def homeassistant_device_discovery(self, initial=False, remove=False):
        subscribe_list = []
        subscribe_list.append(('rs485/bridge/#', 0))
        publish_list = []
        
        self.ha_registry = False
        self.kocom_scan = True

        if self.wp_elevator:
            ha_topic = '{}/{}/{}_{}/config'.format(HA_PREFIX, HA_SWITCH, 'wallpad', DEVICE_ELEVATOR)
            ha_payload = {
                'name': '{}_{}_{}'.format(self._name, 'wallpad', DEVICE_ELEVATOR),
                'cmd_t': '{}/{}/{}_{}/set'.format(HA_PREFIX, HA_SWITCH, 'wallpad', DEVICE_ELEVATOR),
                'stat_t': '{}/{}/{}/state'.format(HA_PREFIX, HA_SWITCH, 'wallpad'),
                'val_tpl': '{{ value_json.' + DEVICE_ELEVATOR + ' }}',
                'ic': 'mdi:elevator',
                'pl_on': 'on',
                'pl_off': 'off',
                'uniq_id': '{}_{}_{}'.format(self._name, 'wallpad', DEVICE_ELEVATOR),
                'device': {
                    'name': 'Kocom {}'.format('wallpad'),
                    'ids': 'kocom_{}'.format('wallpad'),
                    'mf': 'KOCOM',
                    'mdl': 'Wallpad',
                    'sw': SW_VERSION
                }
            }
            subscribe_list.append((ha_topic, 0))
            subscribe_list.append((ha_payload['cmd_t'], 0))
            #subscribe_list.append((ha_payload['stat_t'], 0))
            if remove:
                publish_list.append({ha_topic : ''})
            else:
                publish_list.append({ha_topic : json.dumps(ha_payload)})
        if self.wp_gas:
            ha_topic = '{}/{}/{}_{}/config'.format(HA_PREFIX, HA_SWITCH, 'wallpad', DEVICE_GAS)
            ha_payload = {
                'name': '{}_{}_{}'.format(self._name, 'wallpad', DEVICE_GAS),
                'cmd_t': '{}/{}/{}_{}/set'.format(HA_PREFIX, HA_SWITCH, 'wallpad', DEVICE_GAS),
                'stat_t': '{}/{}/{}_{}/state'.format(HA_PREFIX, HA_SWITCH, 'wallpad', DEVICE_GAS),
                'val_tpl': '{{ value_json.' + DEVICE_GAS + ' }}',
                'ic': 'mdi:gas-cylinder',
                'pl_on': 'on',
                'pl_off': 'off',
                'uniq_id': '{}_{}_{}'.format(self._name, 'wallpad', DEVICE_GAS),
                'device': {
                    'name': 'Kocom {}'.format('wallpad'),
                    'ids': 'kocom_{}'.format('wallpad'),
                    'mf': 'KOCOM',
                    'mdl': 'Wallpad',
                    'sw': SW_VERSION
                }
            }
            subscribe_list.append((ha_topic, 0))
            subscribe_list.append((ha_payload['cmd_t'], 0))
            #subscribe_list.append((ha_payload['stat_t'], 0))
            if remove:
                publish_list.append({ha_topic : ''})
            else:
                publish_list.append({ha_topic : json.dumps(ha_payload)})

            ha_topic = '{}/{}/{}_{}/config'.format(HA_PREFIX, HA_SENSOR, 'wallpad', DEVICE_GAS)
            ha_payload = {
                'name': '{}_{}_{}'.format(self._name, 'wallpad', DEVICE_GAS),
                'stat_t': '{}/{}/{}_{}/state'.format(HA_PREFIX, HA_SENSOR, 'wallpad', DEVICE_GAS),
                'val_tpl': '{{ value_json.' + DEVICE_GAS + ' }}',
                'ic': 'mdi:gas-cylinder',
                'uniq_id': '{}_{}_{}'.format(self._name, 'wallpad', DEVICE_GAS),
                'device': {
                    'name': 'Kocom {}'.format('wallpad'),
                    'ids': 'kocom_{}'.format('wallpad'),
                    'mf': 'KOCOM',
                    'mdl': 'Wallpad',
                    'sw': SW_VERSION
                }
            }
            subscribe_list.append((ha_topic, 0))
            #subscribe_list.append((ha_payload['stat_t'], 0))
            publish_list.append({ha_topic : json.dumps(ha_payload)})
        if self.wp_fan:
            ha_topic = '{}/{}/{}_{}/config'.format(HA_PREFIX, HA_FAN, 'wallpad', DEVICE_FAN)
            ha_payload = {
                'name': '{}_{}_{}'.format(self._name, 'wallpad', DEVICE_FAN),
                'cmd_t': '{}/{}/{}/mode'.format(HA_PREFIX, HA_FAN, 'wallpad'),
                'stat_t': '{}/{}/{}/state'.format(HA_PREFIX, HA_FAN, 'wallpad'),
                'spd_cmd_t': '{}/{}/{}/speed'.format(HA_PREFIX, HA_FAN, 'wallpad'),
                'spd_stat_t': '{}/{}/{}/state'.format(HA_PREFIX, HA_FAN, 'wallpad'),
                'stat_val_tpl': '{{ value_json.mode }}',
                'spd_val_tpl': '{{ value_json.speed }}',
                'pl_on': 'on',
                'pl_off': 'off',
                'spds': ['low', 'medium', 'high', 'off'],
                'uniq_id': '{}_{}_{}'.format(self._name, 'wallpad', DEVICE_FAN),
                'device': {
                    'name': 'Kocom {}'.format('wallpad'),
                    'ids': 'kocom_{}'.format('wallpad'),
                    'mf': 'KOCOM',
                    'mdl': 'Wallpad',
                    'sw': SW_VERSION
                }
            }
            subscribe_list.append((ha_topic, 0))
            subscribe_list.append((ha_payload['cmd_t'], 0))
            #subscribe_list.append((ha_payload['stat_t'], 0))
            subscribe_list.append((ha_payload['spd_cmd_t'], 0))
            if remove:
                publish_list.append({ha_topic : ''})
            else:
                publish_list.append({ha_topic : json.dumps(ha_payload)})
        if self.wp_light:
            for room, r_value in self.wp_list[DEVICE_LIGHT].items():
                if type(r_value) == dict:
                    for sub_device, d_value in r_value.items():
                        if type(d_value) == dict:
                            ha_topic = '{}/{}/{}_{}/config'.format(HA_PREFIX, HA_LIGHT, room, sub_device)
                            ha_payload = {
                                'name': '{}_{}_{}'.format(self._name, room, sub_device),
                                'cmd_t': '{}/{}/{}_{}/set'.format(HA_PREFIX, HA_LIGHT, room, sub_device),
                                'stat_t': '{}/{}/{}/state'.format(HA_PREFIX, HA_LIGHT, room),
                                'val_tpl': '{{ value_json.' + str(sub_device) + ' }}',
                                'pl_on': 'on',
                                'pl_off': 'off',
                                'uniq_id': '{}_{}_{}'.format(self._name, room, sub_device),
                                'device': {
                                    'name': 'Kocom {}'.format(room),
                                    'ids': 'kocom_{}'.format(room),
                                    'mf': 'KOCOM',
                                    'mdl': 'Wallpad',
                                    'sw': SW_VERSION
                                }
                            }
                            subscribe_list.append((ha_topic, 0))
                            subscribe_list.append((ha_payload['cmd_t'], 0))
                            #subscribe_list.append((ha_payload['stat_t'], 0))
                            if remove:
                                publish_list.append({ha_topic : ''})
                            else:
                                publish_list.append({ha_topic : json.dumps(ha_payload)})
        if self.wp_plug:
            for room, r_value in self.wp_list[DEVICE_PLUG].items():
                if type(r_value) == dict:
                    for sub_device, d_value in r_value.items():
                        if type(d_value) == dict:
                            ha_topic = '{}/{}/{}_{}/config'.format(HA_PREFIX, HA_SWITCH, room, sub_device)
                            ha_payload = {
                                'name': '{}_{}_{}'.format(self._name, room, sub_device),
                                'cmd_t': '{}/{}/{}_{}/set'.format(HA_PREFIX, HA_SWITCH, room, sub_device),
                                'stat_t': '{}/{}/{}/state'.format(HA_PREFIX, HA_SWITCH, room),
                                'val_tpl': '{{ value_json.' + str(sub_device) + ' }}',
                                'ic': 'mdi:power-socket-eu',
                                'pl_on': 'on',
                                'pl_off': 'off',
                                'uniq_id': '{}_{}_{}'.format(self._name, room, sub_device),
                                'device': {
                                    'name': 'Kocom {}'.format(room),
                                    'ids': 'kocom_{}'.format(room),
                                    'mf': 'KOCOM',
                                    'mdl': 'Wallpad',
                                    'sw': SW_VERSION
                                }
                            }
                            subscribe_list.append((ha_topic, 0))
                            subscribe_list.append((ha_payload['cmd_t'], 0))
                            #subscribe_list.append((ha_payload['stat_t'], 0))
                            if remove:
                                publish_list.append({ha_topic : ''})
                            else:
                                publish_list.append({ha_topic : json.dumps(ha_payload)})
        if self.wp_thermostat:
            for room, r_list in self.wp_list[DEVICE_THERMOSTAT].items():
                if type(r_list) == dict:
                    ha_topic = '{}/{}/{}/config'.format(HA_PREFIX, HA_CLIMATE, room)
                    ha_payload = {
                        'name': '{}_{}_{}'.format(self._name, room, DEVICE_THERMOSTAT),
                        'mode_cmd_t': '{}/{}/{}/mode'.format(HA_PREFIX, HA_CLIMATE, room),
                        'mode_stat_t': '{}/{}/{}/state'.format(HA_PREFIX, HA_CLIMATE, room),
                        'mode_stat_tpl': '{{ value_json.mode }}',
                        'temp_cmd_t': '{}/{}/{}/target_temp'.format(HA_PREFIX, HA_CLIMATE, room),
                        'temp_stat_t': '{}/{}/{}/state'.format(HA_PREFIX, HA_CLIMATE, room),
                        'temp_stat_tpl': '{{ value_json.target_temp }}',
                        'curr_temp_t': '{}/{}/{}/state'.format(HA_PREFIX, HA_CLIMATE, room),
                        'curr_temp_tpl': '{{ value_json.current_temp }}',
                        'min_temp': 5,
                        'max_temp': 40,
                        'temp_step': 1,
                        'modes': ['off', 'heat', 'fan_only'],
                        'uniq_id': '{}_{}_{}'.format(self._name, room, DEVICE_THERMOSTAT),
                        'device': {
                            'name': 'Kocom {}'.format(room),
                            'ids': 'kocom_{}'.format(room),
                            'mf': 'KOCOM',
                            'mdl': 'Wallpad',
                            'sw': SW_VERSION
                        }
                    }
                    subscribe_list.append((ha_topic, 0))
                    subscribe_list.append((ha_payload['mode_cmd_t'], 0))
                    #subscribe_list.append((ha_payload['mode_stat_t'], 0))
                    subscribe_list.append((ha_payload['temp_cmd_t'], 0))
                    #subscribe_list.append((ha_payload['temp_stat_t'], 0))
                    if remove:
                        publish_list.append({ha_topic : ''})
                    else:
                        publish_list.append({ha_topic : json.dumps(ha_payload)})

        if initial:
            self.d_mqtt.subscribe(subscribe_list)
        for ha in publish_list:
            for topic, payload in ha.items():
                self.d_mqtt.publish(topic, payload)
        self.ha_registry = ha_topic

    def send_to_homeassistant(self, device, room, value):
        v_value = json.dumps(value)
        if device == DEVICE_LIGHT:
            self.d_mqtt.publish("{}/{}/{}/state".format(HA_PREFIX, HA_LIGHT, room), v_value)
            logger.info("[To HA]{}/{}/{}/state = {}".format(HA_PREFIX, HA_LIGHT, room, v_value))
        elif device == DEVICE_PLUG:
            self.d_mqtt.publish("{}/{}/{}/state".format(HA_PREFIX, HA_SWITCH, room), v_value)
            logger.info("[To HA]{}/{}/{}/state = {}".format(HA_PREFIX, HA_SWITCH, room, v_value))
        elif device == DEVICE_THERMOSTAT:
            self.d_mqtt.publish("{}/{}/{}/state".format(HA_PREFIX, HA_CLIMATE, room), v_value)
            logger.info("[To HA]{}/{}/{}/state = {}".format(HA_PREFIX, HA_CLIMATE, room, v_value))
        elif device == DEVICE_ELEVATOR:
            v_value = json.dumps({device: value})
            self.d_mqtt.publish("{}/{}/{}/state".format(HA_PREFIX, HA_SWITCH, room), v_value)
            logger.info("[To HA]{}/{}/{}/state = {}".format(HA_PREFIX, HA_SWITCH, room, v_value))
        elif device == DEVICE_GAS:
            v_value = json.dumps({device: value})
            self.d_mqtt.publish("{}/{}/{}_{}/state".format(HA_PREFIX, HA_SENSOR, room, DEVICE_GAS), v_value)
            logger.info("[To HA]{}/{}/{}_{}/state = {}".format(HA_PREFIX, HA_SENSOR, room, DEVICE_GAS, v_value))
            self.d_mqtt.publish("{}/{}/{}_{}/state".format(HA_PREFIX, HA_SWITCH, room, DEVICE_GAS), v_value)
            logger.info("[To HA]{}/{}/{}_{}/state = {}".format(HA_PREFIX, HA_SWITCH, room, DEVICE_GAS, v_value))
        elif device == DEVICE_FAN:
            self.d_mqtt.publish("{}/{}/{}/state".format(HA_PREFIX, HA_FAN, room), v_value)
            logger.info("[To HA]{}/{}/{}/state = {}".format(HA_PREFIX, HA_FAN, room, v_value))

    def get_serial(self, packet_name, packet_len):
        packet = ''
        start_flag = False
        while True:
            row_data = self.read()
            hex_d = row_data.hex()
            start_hex = ''
            if packet_name == 'kocom':  start_hex = 'aa'
            elif packet_name == 'grex_ventilator':  start_hex = 'd1'
            elif packet_name == 'grex_controller':  start_hex = 'd0'
            if hex_d == start_hex:
                start_flag = True
            if start_flag:
                packet += hex_d

            if len(packet) >= packet_len:
                chksum = self.check_sum(packet)
                if chksum[0]:
                    self.tick = time.time()
                    logger.debug("[From {}]{}".format(packet_name, packet))
                    self.packet_parsing(packet)
                packet = ''
                start_flag = False
            if not self.connected:
                logger.debug('[ERROR] 서버 연결이 끊어져 get_serial Thread를 종료합니다.')
                break

    def check_sum(self, packet):
        sum_packet = sum(bytearray.fromhex(packet)[:17])
        v_sum = int(packet[34:36], 16) if len(packet) >= 36 else 0
        chk_sum = '{0:02x}'.format((sum_packet + 1 + v_sum) % 256)
        orgin_sum = packet[36:38] if len(packet) >= 38 else ''
        return (True, chk_sum) if chk_sum == orgin_sum else (False, chk_sum)

    def parse_packet(self, packet):
        p = {}
        try:
            p['header'] = packet[:4]
            p['type'] = packet[4:7]
            p['order'] = packet[7:8]
            if KOCOM_TYPE.get(p['type']) == 'send':
                p['dst_device'] = packet[10:12]
                p['dst_room'] = packet[12:14]
                p['src_device'] = packet[14:16]
                p['src_room'] = packet[16:18]
            elif KOCOM_TYPE.get(p['type']) == 'ack':
                p['src_device'] = packet[10:12]
                p['src_room'] = packet[12:14]
                p['dst_device'] = packet[14:16]
                p['dst_room'] = packet[16:18]
            p['command'] = packet[18:20]
            p['value'] = packet[20:36]
            p['checksum'] = packet[36:38]
            p['tail'] = packet[38:42]
            return p
        except:
            return False

    def value_packet(self, p):
        v = {}
        if not p:
            return False
        try:
            v['type'] = KOCOM_TYPE.get(p['type'])
            v['command'] = KOCOM_COMMAND.get(p['command'])
            v['src_device'] = KOCOM_DEVICE.get(p['src_device'])
            v['src_room'] = KOCOM_ROOM.get(p['src_room']) if v['src_device'] != DEVICE_THERMOSTAT else KOCOM_ROOM_THERMOSTAT.get(p['src_room'])
            v['dst_device'] = KOCOM_DEVICE.get(p['dst_device'])
            v['dst_room'] = KOCOM_ROOM.get(p['dst_room']) if v['src_device'] != DEVICE_THERMOSTAT else KOCOM_ROOM_THERMOSTAT.get(p['dst_room'])
            v['value'] = p['value']
            if v['src_device'] == DEVICE_FAN:
                v['value'] = self.parse_fan(p['value'])
            elif v['src_device'] == DEVICE_LIGHT or v['src_device'] == DEVICE_PLUG:
                v['value'] = self.parse_switch(v['src_device'], v['src_room'], p['value'])
            elif v['src_device'] == DEVICE_THERMOSTAT:
                v['value'] = self.parse_thermostat(p['value'], self.wp_list[v['src_device']][v['src_room']]['target_temp']['state'])
            elif v['src_device'] == DEVICE_WALLPAD and v['dst_device'] == DEVICE_ELEVATOR:
                v['value'] = 'off'
            elif v['src_device'] == DEVICE_GAS:
                v['value'] = v['command']
            return v
        except:
            return False

    def packet_parsing(self, packet, name='kocom', from_to='From'):
        p = self.parse_packet(packet)
        v = self.value_packet(p)

        try:
            if v['command'] == "조회" and v['src_device'] == DEVICE_WALLPAD:
                if name == 'HA':
                    self.write(self.make_packet(v['dst_device'], v['dst_room'], '조회', '', ''))
                logger.debug('[{} {}]{}({}) {}({}) -> {}({})'.format(from_to, name, v['type'], v['command'], v['src_device'], v['src_room'], v['dst_device'], v['dst_room']))
            else:
                logger.debug('[{} {}]{}({}) {}({}) -> {}({}) = {}'.format(from_to, name, v['type'], v['command'], v['src_device'], v['src_room'], v['dst_device'], v['dst_room'], v['value']))

            if (v['type'] == 'ack' and v['dst_device'] == DEVICE_WALLPAD) or (v['type'] == 'send' and v['dst_device'] == DEVICE_ELEVATOR):
                if v['type'] == 'send' and v['dst_device'] == DEVICE_ELEVATOR:
                    self.set_list(v['dst_device'], DEVICE_WALLPAD, v['value'])
                    self.send_to_homeassistant(v['dst_device'], DEVICE_WALLPAD, v['value'])
                elif v['src_device'] == DEVICE_FAN or v['src_device'] == DEVICE_GAS:
                    self.set_list(v['src_device'], DEVICE_WALLPAD, v['value'])
                    self.send_to_homeassistant(v['src_device'], DEVICE_WALLPAD, v['value'])
                elif v['src_device'] == DEVICE_THERMOSTAT or v['src_device'] == DEVICE_LIGHT or v['src_device'] == DEVICE_PLUG:
                    self.set_list(v['src_device'], v['src_room'], v['value'])
                    self.send_to_homeassistant(v['src_device'], v['src_room'], v['value'])
        except:
            logger.info('[{} {}]Error {}'.format(from_to, name, packet))

    def set_list(self, device, room, value, name='kocom'):
        try:
            logger.info('[From {}]{}/{}/state = {}'.format(name, device, room, value))
            if 'scan' in self.wp_list[device][room] and type(self.wp_list[device][room]['scan']) == dict:
                self.wp_list[device][room]['scan']['tick'] = time.time()
                self.wp_list[device][room]['scan']['count'] = 0
                self.wp_list[device][room]['scan']['last'] = 0
            if device == DEVICE_GAS or device == DEVICE_ELEVATOR:
                self.wp_list[device][room][device]['state'] = value
                self.wp_list[device][room][device]['last'] = 'state'
                self.wp_list[device][room][device]['count'] = 0
            elif device == DEVICE_FAN:
                for sub, v in value.items():
                    try:
                        if sub == 'mode':
                            self.wp_list[device][room][sub]['state'] = v
                            self.wp_list[device][room]['speed']['state'] = 'off' if v == 'off' else DEFAULT_SPEED
                        else:
                            self.wp_list[device][room][sub]['state'] = v
                            self.wp_list[device][room]['mode']['state'] = 'off' if v == 'off' else 'on'
                        if (self.wp_list[device][room][sub]['last'] == 'set' or type(self.wp_list[device][room][sub]['last']) == float) and self.wp_list[device][room][sub]['set'] == self.wp_list[device][room][sub]['state']:
                            self.wp_list[device][room][sub]['last'] = 'state'
                            self.wp_list[device][room][sub]['count'] = 0
                    except:
                        logger.info('[From {}]Error SetListDevice {}/{}/{}/state = {}'.format(name, device, room, sub, v))
            elif device == DEVICE_LIGHT or device == DEVICE_PLUG:
                for sub, v in value.items():
                    try:
                        self.wp_list[device][room][sub]['state'] = v
                        if (self.wp_list[device][room][sub]['last'] == 'set' or type(self.wp_list[device][room][sub]['last']) == float) and self.wp_list[device][room][sub]['set'] == self.wp_list[device][room][sub]['state']:
                            self.wp_list[device][room][sub]['last'] = 'state'
                            self.wp_list[device][room][sub]['count'] = 0
                    except:
                        logger.info('[From {}]Error SetListDevice {}/{}/{}/state = {}'.format(name, device, room, sub, v))
            elif device == DEVICE_THERMOSTAT:
                for sub, v in value.items():
                    try:
                        if sub == 'mode':
                            self.wp_list[device][room][sub]['state'] = v
                        else:
                            self.wp_list[device][room][sub]['state'] = int(float(v))
                            self.wp_list[device][room]['mode']['state'] = 'heat'
                        if (self.wp_list[device][room][sub]['last'] == 'set' or type(self.wp_list[device][room][sub]['last']) == float) and self.wp_list[device][room][sub]['set'] == self.wp_list[device][room][sub]['state']:
                            self.wp_list[device][room][sub]['last'] = 'state'
                            self.wp_list[device][room][sub]['count'] = 0
                    except:
                        logger.info('[From {}]Error SetListDevice {}/{}/{}/state = {}'.format(name, device, room, sub, v))
        except:
            logger.info('[From {}]Error SetList {}/{} = {}'.format(name, device, room, value))

    def scan_list(self):
        while True:
            if not self.kocom_scan:
                now = time.time()
                if now - self.tick > KOCOM_INTERVAL / 1000:
                    try:
                        for device, d_list in self.wp_list.items():
                            if type(d_list) == dict and ((device == DEVICE_ELEVATOR and self.wp_elevator) or (device == DEVICE_FAN and self.wp_fan) or (device == DEVICE_GAS and self.wp_gas) or (device == DEVICE_LIGHT and self.wp_light) or (device == DEVICE_PLUG and self.wp_plug) or (device == DEVICE_THERMOSTAT and self.wp_thermostat)):
                                for room, r_list in d_list.items():
                                    if type(r_list) == dict:
                                        if 'scan' in r_list and type(r_list['scan']) == dict and now - r_list['scan']['tick'] > SCAN_INTERVAL and ((device == DEVICE_FAN and self.wp_fan) or (device == DEVICE_GAS and self.wp_gas) or (device == DEVICE_LIGHT and self.wp_light) or (device == DEVICE_PLUG and self.wp_plug) or (device == DEVICE_THERMOSTAT and self.wp_thermostat)):
                                            if now - r_list['scan']['last'] > 2:
                                                r_list['scan']['count'] += 1
                                                r_list['scan']['last'] = now
                                                self.set_serial(device, room, '', '', cmd='조회')
                                                time.sleep(SCANNING_INTERVAL)
                                            if r_list['scan']['count'] > 4:
                                                r_list['scan']['tick'] = now
                                                r_list['scan']['count'] = 0
                                                r_list['scan']['last'] = 0
                                        else:
                                            for sub_d, sub_v in r_list.items():
                                                if sub_d != 'scan':
                                                    if sub_v['count'] > 4:
                                                        sub_v['count'] = 0
                                                        sub_v['last'] = 'state'
                                                    elif sub_v['last'] == 'set':
                                                        sub_v['last'] = now
                                                        if device == DEVICE_GAS:
                                                            sub_v['last'] += 5
                                                        elif device == DEVICE_ELEVATOR:
                                                            sub_v['last'] = 'state'
                                                        self.set_serial(device, room, sub_d, sub_v['set'])
                                                    elif type(sub_v['last']) == float and now - sub_v['last'] > 1:
                                                        sub_v['last'] = 'set' 
                                                        sub_v['count'] += 1
                    except:
                        logger.debug('[Scan]Error')
            if not self.connected:
                logger.debug('[ERROR] 서버 연결이 끊어져 scan_list Thread를 종료합니다.')
                break
            time.sleep(0.2)

    def set_serial(self, device, room, target, value, cmd='상태'):
        if (time.time() - self.tick) < KOCOM_INTERVAL / 1000:
            return
        if cmd == '상태':
            logger.info('[To {}]{}/{}/{} -> {}'.format(self._name, device, room, target, value))
        elif cmd == '조회':
            logger.info('[To {}]{}/{} -> 조회'.format(self._name, device, room))
        packet = self.make_packet(device, room, '상태', target, value) if cmd == '상태' else  self.make_packet(device, room, '조회', '', '')
        v = self.value_packet(self.parse_packet(packet))

        logger.debug('[To {}]{}'.format(self._name, packet))
        if v['command'] == "조회" and v['src_device'] == DEVICE_WALLPAD:
            logger.debug('[To {}]{}({}) {}({}) -> {}({})'.format(self._name, v['type'], v['command'], v['src_device'], v['src_room'], v['dst_device'], v['dst_room']))
        else:
            logger.debug('[To {}]{}({}) {}({}) -> {}({}) = {}'.format(self._name, v['type'], v['command'], v['src_device'], v['src_room'], v['dst_device'], v['dst_room'], v['value']))
        if device == DEVICE_ELEVATOR:
            self.send_to_homeassistant(DEVICE_ELEVATOR, DEVICE_WALLPAD, 'on')
        self.write(packet)

    def make_packet(self, device, room, cmd, target, value):
        p_header = 'aa5530bc00'
        p_device = KOCOM_DEVICE_REV.get(device)
        p_room = KOCOM_ROOM_REV.get(room) if device != DEVICE_THERMOSTAT else  KOCOM_ROOM_THERMOSTAT_REV.get(room)
        p_dst = KOCOM_DEVICE_REV.get(DEVICE_WALLPAD) + KOCOM_ROOM_REV.get(DEVICE_WALLPAD)
        p_cmd = KOCOM_COMMAND_REV.get(cmd)
        p_value = ''
        if cmd == '조회':
            p_value = '0000000000000000'
        else:
            if device == DEVICE_ELEVATOR:
                p_device = KOCOM_DEVICE_REV.get(DEVICE_WALLPAD)
                p_room = KOCOM_ROOM_REV.get(DEVICE_WALLPAD)
                p_dst = KOCOM_DEVICE_REV.get(device) + KOCOM_ROOM_REV.get(DEVICE_WALLPAD)
                p_cmd = KOCOM_COMMAND_REV.get('on')
                p_value = '0000000000000000'
            elif device == DEVICE_GAS:
                p_cmd = KOCOM_COMMAND_REV.get('off')
                p_value = '0000000000000000'
            elif device == DEVICE_LIGHT or device == DEVICE_PLUG:
                try:
                    all_device = device + str('0')
                    for i in range(1,9):
                        sub_device = device + str(i)
                        if target != sub_device:
                            if target == all_device:
                                if sub_device in self.wp_list[device][room]:
                                    p_value += 'ff' if value == 'on' else str('00')
                                else:
                                    p_value += '00'
                            else:
                                if sub_device in self.wp_list[device][room] and self.wp_list[device][room][sub_device]['state'] == 'on':
                                    p_value += 'ff'
                                else:
                                    p_value += '00'
                        else:
                            p_value += 'ff' if value == 'on' else str('00')
                except:
                    logger.debug('[Make Packet] Error on DEVICE_LIGHT or DEVICE_PLUG')
            elif device == DEVICE_THERMOSTAT:
                try:
                    mode = self.wp_list[device][room]['mode']['set']
                    target_temp = self.wp_list[device][room]['target_temp']['set']
                    if mode == 'heat':
                        p_value += '1100'
                    elif mode == 'off':
                        # p_value += '0001'
                        p_value += '0100'
                    else:
                        p_value += '1101'
                    p_value += '{0:02x}'.format(int(float(target_temp)))
                    p_value += '0000000000'
                except:
                    logger.debug('[Make Packet] Error on DEVICE_THERMOSTAT')
            elif device == DEVICE_FAN:
                try:
                    mode = self.wp_list[device][room]['mode']['set']
                    speed = self.wp_list[device][room]['speed']['set']
                    if mode == 'on':
                        p_value += '1100'
                    elif mode == 'off':
                        p_value += '0001'
                    p_value += KOCOM_FAN_SPEED_REV.get(speed)
                    p_value += '00000000000'
                except:
                    logger.debug('[Make Packet] Error on DEVICE_THERMOSTAT')
        if p_value != '':
            packet = p_header + p_device + p_room + p_dst + p_cmd + p_value
            chk_sum = self.check_sum(packet)[1]
            packet += chk_sum + '0d0d'
            return packet
        return False

    def parse_fan(self, value='0000000000000000'):
        fan = {}
        fan['mode'] = 'on' if value[:2] == '11' else 'off'
        fan['speed'] = KOCOM_FAN_SPEED.get(value[4:5])
        return fan

    def parse_switch(self, device, room, value='0000000000000000'):
        switch = {}
        on_count = 0
        to_i = KOCOM_LIGHT_SIZE.get(room) + 1 if device == DEVICE_LIGHT else KOCOM_PLUG_SIZE.get(room) + 1
        for i in range(1, to_i):
            switch[device + str(i)] = 'off' if value[i*2-2:i*2] == '00' else 'on'
            if value[i*2-2:i*2] != '00':
                on_count += 1
        switch[device + str('0')] = 'on' if on_count > 0 else 'off'
        return switch

    def parse_thermostat(self, value='0000000000000000', init_temp=False):
        thermo = {}
        heat_mode = 'heat' if value[:2] == '11' else 'off'
        away_mode = 'on' if value[2:4] == '01' else 'off'
        thermo['current_temp'] = int(value[8:10], 16)
        if heat_mode == 'heat' and away_mode == 'on':
            thermo['mode'] = 'fan_only'
            thermo['target_temp'] = INIT_TEMP if not init_temp else int(init_temp)
        elif heat_mode == 'heat' and away_mode == 'off':
            thermo['mode'] = 'heat'
            thermo['target_temp'] = int(value[4:6], 16)
        elif heat_mode == 'off':
            thermo['mode'] = 'off'
            thermo['target_temp'] = INIT_TEMP if not init_temp else int(init_temp)
        return thermo

class Grex:
    def __init__(self, client, cont, vent):
        self._name = 'grex'
        self.contoller = cont
        self.ventilator = vent
        self.grex_cont = {'mode': 'off', 'speed': 'off'}
        self.vent_cont = {'mode': 'off', 'speed': 'off'}
        self.mqtt_cont = {'mode': 'off', 'speed': 'off'}

        self.d_mqtt = self.connect_mqtt(client._mqtt, 'GREX')

        _t4 = threading.Thread(target=self.get_serial, args=(self.contoller['serial'], self.contoller['name'], self.contoller['length']))
        _t4.daemon = True
        _t4.start()
        _t5 = threading.Thread(target=self.get_serial, args=(self.ventilator['serial'], self.ventilator['name'], self.ventilator['length']))
        _t5.daemon = True
        _t5.start()

    def connect_mqtt(self, server, name):
        mqtt_client = mqtt.Client()
        mqtt_client.on_message = self.on_message
        #mqtt_client.on_publish = self.on_publish
        mqtt_client.on_subscribe = self.on_subscribe
        mqtt_client.on_connect = self.on_connect

        if server['anonymous'] != 'True':
            if server['server'] == '' or server['username'] == '' or server['password'] == '':
                logger.info('{} 설정을 확인하세요. Server[{}] ID[{}] PW[{}] Device[{}]'.format(CONF_MQTT, server['server'], server['username'], server['password'], name))
                return False
            mqtt_client.username_pw_set(username=server['username'], password=server['password'])
            logger.debug('{} STATUS. Server[{}] ID[{}] PW[{}] Device[{}]'.format(CONF_MQTT, server['server'], server['username'], server['password'], name))
        else:
            logger.debug('{} STATUS. Server[{}] Device[{}]'.format(CONF_MQTT, server['server'], name))

        mqtt_client.connect(server['server'], 1883, 60)
        mqtt_client.loop_start()
        return mqtt_client

    def on_message(self, client, obj, msg):
        _topic = msg.topic.split('/')
        _payload = msg.payload.decode()

        if 'config' in _topic:
            if _topic[0] == 'rs485' and _topic[3] == 'restart':
                self.homeassistant_device_discovery()
                return
        elif _topic[0] == HA_PREFIX and _topic[1] == HA_FAN and _topic[2] == 'grex':
            logger.info("Message Fan: {} = {}".format(msg.topic, _payload))
            if _topic[3] == 'speed' or _topic[3] == 'mode':
                if _topic[3] == 'mode' and self.mqtt_cont[_topic[3]] == 'off' and _payload == 'on' and self.mqtt_cont['speed'] == 'off':
                    self.mqtt_cont['speed'] = 'low'
                self.mqtt_cont[_topic[3]] = _payload

                if self.mqtt_cont['mode'] == 'off' and self.mqtt_cont['speed'] == 'off':
                    self.send_to_homeassistant(HA_FAN, self.mqtt_cont)

    def on_publish(self, client, obj, mid):
        logger.info("Publish: {}".format(str(mid)))

    def on_subscribe(self, client, obj, mid, granted_qos):
        logger.info("Subscribed: {} {}".format(str(mid),str(granted_qos)))

    def on_connect(self, client, userdata, flags, rc):
        if int(rc) == 0:
            logger.info("MQTT connected OK")
            self.homeassistant_device_discovery(initial=True)
        elif int(rc) == 1:
            logger.info("1: Connection refused – incorrect protocol version")
        elif int(rc) == 2:
            logger.info("2: Connection refused – invalid client identifier")
        elif int(rc) == 3:
            logger.info("3: Connection refused – server unavailable")
        elif int(rc) == 4:
            logger.info("4: Connection refused – bad username or password")
        elif int(rc) == 5:
            logger.info("5: Connection refused – not authorised")
        else:
            logger.info(rc, ": Connection refused")

    def homeassistant_device_discovery(self, initial=False):
        subscribe_list = []
        publish_list = []
        subscribe_list.append(('rs485/bridge/#', 0))
        ha_topic = '{}/{}/{}_{}/config'.format(HA_PREFIX, HA_FAN, 'grex', DEVICE_FAN)
        ha_payload = {
            'name': '{}_{}'.format(self._name, DEVICE_FAN),
            'cmd_t': '{}/{}/{}/mode'.format(HA_PREFIX, HA_FAN, 'grex'),
            'stat_t': '{}/{}/{}/state'.format(HA_PREFIX, HA_FAN, 'grex'),
            'spd_cmd_t': '{}/{}/{}/speed'.format(HA_PREFIX, HA_FAN, 'grex'),
            'spd_stat_t': '{}/{}/{}/state'.format(HA_PREFIX, HA_FAN, 'grex'),
            'stat_val_tpl': '{{ value_json.mode }}',
            'spd_val_tpl': '{{ value_json.speed }}',
            'pl_on': 'on',
            'pl_off': 'off',
            'spds': ['low', 'medium', 'high', 'off'],
            'uniq_id': '{}_{}_{}'.format(self._name, 'grex', DEVICE_FAN),
            'device': {
                'name': 'Grex Ventilator',
                'ids': 'grex_ventilator',
                'mf': 'Grex',
                'mdl': 'Ventilator',
                'sw': SW_VERSION
            }
        }
        subscribe_list.append((ha_topic, 0))
        subscribe_list.append((ha_payload['cmd_t'], 0))
        subscribe_list.append((ha_payload['spd_cmd_t'], 0))
        #subscribe_list.append((ha_payload['stat_t'], 0))
        publish_list.append({ha_topic : json.dumps(ha_payload)})

        ha_topic = '{}/{}/{}_{}_mode/config'.format(HA_PREFIX, HA_SENSOR, 'grex', DEVICE_FAN)
        ha_payload = {
            'name': '{}_{}_mode'.format(self._name, DEVICE_FAN),
            'stat_t': '{}/{}/{}_{}/state'.format(HA_PREFIX, HA_SENSOR, 'grex', DEVICE_FAN),
            'val_tpl': '{{ value_json.' + DEVICE_FAN + '_mode }}',
            'ic': 'mdi:play-circle-outline',
            'uniq_id': '{}_{}_{}_mode'.format(self._name, 'grex', DEVICE_FAN),
            'device': {
                'name': 'Grex Ventilator',
                'ids': 'grex_ventilator',
                'mf': 'Grex',
                'mdl': 'Ventilator',
                'sw': SW_VERSION
            }
        }
        subscribe_list.append((ha_topic, 0))
        #subscribe_list.append((ha_payload['stat_t'], 0))
        publish_list.append({ha_topic : json.dumps(ha_payload)})
        ha_topic = '{}/{}/{}_{}_speed/config'.format(HA_PREFIX, HA_SENSOR, 'grex', DEVICE_FAN)
        ha_payload = {
            'name': '{}_{}_speed'.format(self._name, DEVICE_FAN),
            'stat_t': '{}/{}/{}_{}/state'.format(HA_PREFIX, HA_SENSOR, 'grex', DEVICE_FAN),
            'val_tpl': '{{ value_json.' + DEVICE_FAN + '_speed }}',
            'ic': 'mdi:speedometer',
            'uniq_id': '{}_{}_{}_speed'.format(self._name, 'grex', DEVICE_FAN),
            'device': {
                'name': 'Grex Ventilator',
                'ids': 'grex_ventilator',
                'mf': 'Grex',
                'mdl': 'Ventilator',
                'sw': SW_VERSION
            }
        }
        subscribe_list.append((ha_topic, 0))
        #subscribe_list.append((ha_payload['stat_t'], 0))
        publish_list.append({ha_topic : json.dumps(ha_payload)})

        if initial:
            self.d_mqtt.subscribe(subscribe_list)
        for ha in publish_list:
            for topic, payload in ha.items():
                self.d_mqtt.publish(topic, payload)

    def send_to_homeassistant(self, target, value):
        if target == HA_FAN:
            self.d_mqtt.publish("{}/{}/{}/state".format(HA_PREFIX, HA_FAN, 'grex'), json.dumps(value))
            logger.info("[To HA]{}/{}/{}/state = {}".format(HA_PREFIX, HA_FAN, 'grex', json.dumps(value)))
        elif target == HA_SENSOR:
            self.d_mqtt.publish("{}/{}/{}_{}/state".format(HA_PREFIX, HA_SENSOR, 'grex', DEVICE_FAN), json.dumps(value, ensure_ascii = False))
            logger.info("[To HA]{}/{}/{}_{}/state = {}".format(HA_PREFIX, HA_SENSOR, 'grex', DEVICE_FAN, json.dumps(value, ensure_ascii = False)))

    def get_serial(self, ser, packet_name, packet_len):
        buf = []
        start_flag = False
        while True:
            if ser.readable():
                row_data = ser.read()
                hex_d = row_data.hex()
                start_hex = ''
                if packet_name == 'kocom':  start_hex = 'aa'
                elif packet_name == 'grex_ventilator':  start_hex = 'd1'
                elif packet_name == 'grex_controller':  start_hex = 'd0'
                if hex_d == start_hex:
                    start_flag = True
                if start_flag == True:
                    buf.append(hex_d)

                if len(buf) >= packet_len:
                    joindata = ''.join(buf)
                    chksum = self.validate_checksum(joindata, packet_len - 1)
                    #logger.debug("[From {}]{} {} {}".format(packet_name, joindata, str(chksum[0]), str(chksum[1])))
                    if chksum[0]:
                        self.packet_parsing(joindata, packet_name)
                    buf = []
                    start_flag = False

    def packet_parsing(self, packet, packet_name):
        p_prefix = packet[:4]

        if p_prefix == 'd00a':
            m_packet = self.make_response_packet(0)
            m_chksum = self.validate_checksum(m_packet, 11)
            if m_chksum[0]:
                self.contoller['serial'].write(bytearray.fromhex(m_packet))
            logger.debug('[From Grex]error code : E1')
        elif p_prefix == 'd08a':
            control_packet = ''
            response_packet = ''
            p_mode = packet[8:12]
            p_speed = packet[12:16]

            if self.grex_cont['mode'] != GREX_MODE[p_mode] or self.grex_cont['speed'] != GREX_SPEED[p_speed]:
                self.grex_cont['mode'] = GREX_MODE[p_mode]
                self.grex_cont['speed'] = GREX_SPEED[p_speed]
                logger.info('[From {}]mode:{} / speed:{}'.format(packet_name, self.grex_cont['mode'], self.grex_cont['speed']))
                send_to_ha_fan = {'mode': 'off', 'speed': 'off'}
                if self.grex_cont['mode'] != 'off' or (self.grex_cont['mode'] == 'off' and self.mqtt_cont['mode'] == 'on'):
                    send_to_ha_fan['mode'] = 'on'
                    send_to_ha_fan['speed'] = self.grex_cont['speed']
                self.send_to_homeassistant(HA_FAN, send_to_ha_fan)

                send_to_ha_sensor = {'fan_mode': 'off', 'fan_speed': 'off'}
                if self.grex_cont['mode'] != 'off' or (self.grex_cont['mode'] == 'off' and self.mqtt_cont['mode'] == 'on'):
                    if self.grex_cont['mode'] == 'auto':
                        send_to_ha_sensor['fan_mode'] = '자동'
                    elif self.grex_cont['mode'] == 'manual':
                        send_to_ha_sensor['fan_mode'] = '수동'
                    elif self.grex_cont['mode'] == 'sleep':
                        send_to_ha_sensor['fan_mode'] = '취침'
                    elif self.grex_cont['mode'] == 'off' and self.mqtt_cont['mode'] == 'on':
                        send_to_ha_sensor['fan_mode'] = 'HA'
                    if self.grex_cont['speed'] == 'low':
                        send_to_ha_sensor['fan_speed'] = '1단'
                    elif self.grex_cont['speed'] == 'medium':
                        send_to_ha_sensor['fan_speed'] = '2단'
                    elif self.grex_cont['speed'] == 'high':
                        send_to_ha_sensor['fan_speed'] = '3단'
                    elif self.grex_cont['speed'] == 'off':
                        send_to_ha_sensor['fan_speed'] = '대기'
                self.send_to_homeassistant(HA_SENSOR, send_to_ha_sensor)

            if self.grex_cont['mode'] == 'off':
                response_packet = self.make_response_packet(0)
                if self.mqtt_cont['mode'] == 'off' or (self.mqtt_cont['mode'] == 'on' and self.mqtt_cont['speed'] == 'off'):
                    control_packet = self.make_control_packet('off', 'off')
                elif self.mqtt_cont['mode'] == 'on' and self.mqtt_cont['speed'] != 'off':
                    control_packet = self.make_control_packet('manual', self.mqtt_cont['speed'])
            else:
                control_packet = self.make_control_packet(self.grex_cont['mode'], self.grex_cont['speed'])
                if self.grex_cont['speed'] == 'low':
                    response_packet = self.make_response_packet(1)
                elif self.grex_cont['speed'] == 'medium':
                    response_packet = self.make_response_packet(2)
                elif self.grex_cont['speed'] == 'high':
                    response_packet = self.make_response_packet(3)
                elif self.grex_cont['speed'] == 'off':
                    response_packet = self.make_response_packet(0)

            if response_packet != '':
                self.contoller['serial'].write(bytearray.fromhex(response_packet))
                #logger.debug("[Tooo grex_controller]{}".format(response_packet))
            if control_packet != '':
                self.ventilator['serial'].write(bytearray.fromhex(control_packet))
                #logger.debug("[Tooo grex_ventilator]{}".format(control_packet))

        elif p_prefix == 'd18b':
            p_speed = packet[8:12]
            if self.vent_cont['speed'] != GREX_SPEED[p_speed]:
                self.vent_cont['speed'] = GREX_SPEED[p_speed]
                logger.info('[From {}]speed:{}'.format(packet_name, self.vent_cont['speed']))

                send_to_ha_fan = {'mode': 'off', 'speed': 'off'}
                if self.grex_cont['mode'] != 'off' or (self.grex_cont['mode'] == 'off' and self.mqtt_cont['mode'] == 'on'):
                    send_to_ha_fan['mode'] = 'on'
                    send_to_ha_fan['speed'] = self.vent_cont['speed']
                self.send_to_homeassistant(HA_FAN, send_to_ha_fan)

                send_to_ha_sensor = {'fan_mode': 'off', 'fan_speed': 'off'}
                if self.grex_cont['mode'] != 'off' or (self.grex_cont['mode'] == 'off' and self.mqtt_cont['mode'] == 'on'):
                    if self.grex_cont['mode'] == 'auto':
                        send_to_ha_sensor['fan_mode'] = '자동'
                    elif self.grex_cont['mode'] == 'manual':
                        send_to_ha_sensor['fan_mode'] = '수동'
                    elif self.grex_cont['mode'] == 'sleep':
                        send_to_ha_sensor['fan_mode'] = '취침'
                    elif self.grex_cont['mode'] == 'off' and self.mqtt_cont['mode'] == 'on':
                        send_to_ha_sensor['fan_mode'] = 'HA'
                    if self.vent_cont['speed'] == 'low':
                        send_to_ha_sensor['fan_speed'] = '1단'
                    elif self.vent_cont['speed'] == 'medium':
                        send_to_ha_sensor['fan_speed'] = '2단'
                    elif self.vent_cont['speed'] == 'high':
                        send_to_ha_sensor['fan_speed'] = '3단'
                    elif self.vent_cont['speed'] == 'off':
                        send_to_ha_sensor['fan_speed'] = '대기'
                self.send_to_homeassistant(HA_SENSOR, send_to_ha_sensor)

    def make_control_packet(self, mode, speed):
        prefix = 'd08ae022'
        if mode == 'off':
            packet_mode = '0000'
        elif mode == 'auto':
            packet_mode = '0100'
        elif mode == 'manual':
            packet_mode = '0200'
        elif mode == 'sleep':
            packet_mode = '0300'
        else:
            return ''
        if speed == 'off':
            packet_speed = '0000'
        elif speed == 'low':
            packet_speed = '0101'
        elif speed == 'medium':
            packet_speed = '0202'
        elif speed == 'high':
            packet_speed = '0303'
        else:
            return ''
        if ((mode == 'auto' or mode == 'sleep') and (speed == 'off')) or (speed == 'low' or speed == 'medium' or speed == 'high'):
            postfix = '0001'
        else:
            postfix = '0000'

        packet = prefix + packet_mode + packet_speed + postfix
        packet_checksum = self.make_checksum(packet, 10)
        packet = packet + packet_checksum
        return packet

    def make_response_packet(self, speed):
        prefix = 'd18be021'
        if speed == 0:
            packet_speed = '0000'
        elif speed == 1:
            packet_speed = '0101'
        elif speed == 2:
            packet_speed = '0202'
        elif speed == 3:
            packet_speed = '0303'
        if speed == 0:
            postfix = '0000000000'
        elif speed > 0:
            postfix = '0000000100'

        packet = prefix + packet_speed + postfix
        packet_checksum = self.make_checksum(packet, 11)
        packet = packet + packet_checksum
        return packet

    def hex_to_list(self, hex_string):
        slide_windows = 2
        start = 0
        buf = []
        for x in range(int(len(hex_string) / 2)):
            buf.append('0x{}'.format(hex_string[start: slide_windows].lower()))
            slide_windows += 2
            start += 2
        return buf

    def validate_checksum(self, packet, length):
        hex_list = self.hex_to_list(packet)
        sum_buf = 0
        for ix, x in enumerate(hex_list):
            if ix > 0:
                hex_int = int(x, 16)
                if ix == length:
                    chksum_hex = '0x{0:02x}'.format((sum_buf % 256))
                    if hex_list[ix] == chksum_hex:
                        return (True, hex_list[ix])
                    else:
                        return (False, hex_list[ix])
                sum_buf += hex_int

    def make_checksum(self, packet, length):
        hex_list = self.hex_to_list(packet)
        sum_buf = 0
        chksum_hex = 0
        for ix, x in enumerate(hex_list):
            if ix > 0:
                hex_int = int(x, 16)
                sum_buf += hex_int
                if ix == length - 1:
                    chksum_hex = '{0:02x}'.format((sum_buf % 256))
        return str(chksum_hex)

if __name__ == '__main__':
    #logger 인스턴스 생성 및 로그레벨 설정
    logger = logging.getLogger(CONF_LOGNAME)
    logger.setLevel(logging.INFO)
    if CONF_LOGLEVEL == "info": logger.setLevel(logging.INFO)
    if CONF_LOGLEVEL == "debug": logger.setLevel(logging.DEBUG)
    if CONF_LOGLEVEL == "warn": logger.setLevel(logging.WARN)

    # formatter 생성
    logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : Line %(lineno)s - %(message)s')

    # fileHandler, StreamHandler 생성
    file_max_bytes = 100 * 1024 * 10 # 1 MB 사이즈
    logFileHandler = logging.handlers.RotatingFileHandler(filename=log_path, maxBytes=file_max_bytes, backupCount=10, encoding='utf-8')
    logStreamHandler = logging.StreamHandler()

    # handler 에 formatter 설정
    logFileHandler.setFormatter(logFormatter)
    logStreamHandler.setFormatter(logFormatter)
    logFileHandler.suffix = "%Y%m%d"

    logger.addHandler(logFileHandler)
    #logger.addHandler(logStreamHandler)
 
    logging.info('{} 시작'.format(SW_VERSION))
    logger.info('{} 시작'.format(SW_VERSION))

    if DEFAULT_SPEED not in ['low', 'medium', 'high']:
        logger.info('[Error] DEFAULT_SPEED 설정오류로 medium 으로 설정. {} -> medium'.format(DEFAULT_SPEED))
        DEFAULT_SPEED = 'medium'

    _grex_ventilator = False
    _grex_controller = False
    connection_flag = False
    while not connection_flag:
        r = rs485()
        connection_flag = True
        if r._type == 'serial':
            for device in r._device:
                if r._connect[device].isOpen():
                    _name = r._device[device]
                    try:
                        logger.info('[CONFIG] {} 초기화'.format(_name))
                        if _name == 'kocom':
                            kocom = Kocom(r, _name, device, 42)
                        elif _name == 'grex_ventilator':
                            _grex_ventilator = {'serial': r._connect[device], 'name': _name, 'length': 12}
                        elif _name == 'grex_controller':
                            _grex_controller = {'serial': r._connect[device], 'name': _name, 'length': 11}
                    except:
                        logger.info('[CONFIG] {} 초기화 실패'.format(_name))
        elif r._type == 'socket':
            _name = r._device
            if _name == 'kocom':
                kocom = Kocom(r, _name, _name, 42)
                if not kocom.connection_lost():
                    logger.info('[ERROR] 서버 연결이 끊어져 1분 후 재접속을 시도합니다.')
                    time.sleep(60)
                    connection_flag = False
        if _grex_ventilator is not False and _grex_controller is not False:
            _grex = Grex(r, _grex_controller, _grex_ventilator)
