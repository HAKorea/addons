# first written by Nandflash("저장장치") <github@printk.info> since 2020-06-25

import socket
import serial
import paho.mqtt.client as paho_mqtt
import json
import sys
import time

####################
# 가상의 현관 스위치로 동작하는 부분
ENTRANCE_SWITCH = {
	# 평상시 다양한 응답
	'default': {
		'init':  { 'header': 0xAD5A, 'resp': 0xB05A006A, }, # 처음 전기가 들어왔거나 한동안 응답을 안했을 때, 이것부터 해야 함
		'query': { 'header': 0xAD41, 'resp': 0xB0560066, }, # 여기에 0xB0410071로 응답하면 gas valve 상태는 전달받지 않음
		'gas':   { 'header': 0xAD56, 'resp': 0xB0410071, }, # 0xAD41에 항상 0xB041로 응답하면 이게 실행될 일은 없음
		'light': { 'header': 0xAD52, 'resp': 0xB0520163, 'ON': 0xB0520063, 'OFF': 0xB0520162, },
		},

	# 0xAD41에 다르게 응답하는 방법들, 이 경우 월패드가 다시 ack를 보내준다
	'trigger': {
		'gas':   { 'ack': 0xAD55, 'ON': 0xB0550164, },
		'light': { 'ack': 0xAD54, 'ON': 0xB0540064, 'OFF':  0xB0540165, }, # ON: 일괄소등(차단), OFF: 해제
		'ev':    { 'ack': 0xAD2F, 'ON': 0xB02F011E, },
		},
}

####################
# 기존 월패드 애드온의 역할하는 부분
RS485_DEVICE = {
	# 전등 스위치
	'light': {
		'query':    { 'header': 0xAC79, 'length':  5, 'id': 2, },
		'state':    { 'header': 0xB079, 'length':  5, 'id': 2, 'parse': {('power', 3, 'bitmap')} },
		'last':     { },

		'power':    { 'header': 0xAC7A, 'length':  5, 'id': 2, 'pos': 3, },
		},

	# 환기장치 (전열교환기)
	'fan': {
		'query':    { 'header': 0xC24E, 'length':  6, },
		'state':    { 'header': 0xB04E, 'length':  6, 'parse': {('power', 4, 'fan_toggle'), ('speed', 2, 'value')} },
		'last':     { },

		'power':    { 'header': 0xC24F, 'length':  6, 'pos': 2, },
		'speed':    { 'header': 0xC24F, 'length':  6, 'pos': 2, },
		},

	# 각방 난방 제어
	'thermostat': {
		'query':    { 'header': 0xAE7C, 'length':  8, 'id': 2, },
		'state':    { 'header': 0xB07C, 'length':  8, 'id': 2, 'parse': {('power', 3, 'heat_toggle'), ('target', 4, 'value'), ('current', 5, 'value')} },
		'last':     { },

		'power':    { 'header': 0xAE7D, 'length':  8, 'id': 2, 'pos': 3, },
		'target':   { 'header': 0xAE7F, 'length':  8, 'id': 2, 'pos': 3, },
		},

	# 대기전력차단 스위치 (전력사용량 확인)
	'plug': {
		'query':    { 'header': 0xC64A, 'length': 10, 'id': 2, },
		'state':    { 'header': 0xB04A, 'length': 10, 'id': 2, 'parse': {('power', 3, 'toggle'), ('idlecut', 3, 'toggle2'), ('current', 5, '2Byte')} },
		'last':     { },

		'power':    { 'header': 0xC66E, 'length': 10, 'id': 2, 'pos': 3, },
		'idlecut':  { 'header': 0xC64B, 'length': 10, 'id': 2, 'pos': 3, },
		},

	# 일괄조명: 현관 스위치 살아있으면...
	'cutoff': {
		'query':    { 'header': 0xAD52, 'length':  4, },
		'state':    { 'header': 0xB052, 'length':  4, 'parse': {('power', 2, 'toggle')} }, # 1: 정상, 0: 일괄소등
		'last':     { },

		'power':    { 'header': 0xAD53, 'length':  4, 'pos': 2, },
		},

	# 부엌 가스 밸브
	'gas_valve': {
		'query':    { 'header': 0xAB41, 'length':  4, },
		#'state':    { 'header': 0xB041, 'length':  4, 'parse': {('power', 2, 'toggle')} }, # 0: 정상, 1: 차단; 0xB041은 공용 ack이므로 처리하기 복잡함
		'state':    { 'header': 0xAD56, 'length':  4, 'parse': {('power', 2, 'toggle')} }, # 0: 정상, 1: 차단; 월패드가 현관 스위치에 보내주는 정보로 확인 가능
		'last':     { },

		'power':    { 'header': 0xAB78, 'length':  4, }, # 0 으로 잠그기만 가능
		},

	# 실시간에너지 0:전기, 1:가스, 2:수도
	'energy': {
		'query':    { 'header': 0xAA6F, 'length':  4, 'id': 2, },
		'state':    { 'header': 0xB06F, 'length':  7, 'id': 2, 'parse': {('current', 3, '4_2decimal')} },
		'last':     { },
		},
}

DISCOVERY_ENTRANCE = [ {
	'~': "{}/entrance/ev",
	'name': "{}_elevator",
	'stat_t': "~/state",
	'cmd_t': "~/command",
	'icon': "mdi:elevator",
	},
	{
	'~': "{}/entrance/gas",
	'name': "{}_gas_cutoff",
	'stat_t': "~/state",
	'cmd_t': "~/command",
	'icon': "mdi:valve",
	},
	{
	'~': "{}/entrance/light",
	'name': "{}_entrance_all_light",
	'stat_t': "~/state",
	'cmd_t': "~/command",
	'icon': "mdi:lightbulb-group-off",
	},
	]

DISCOVERY_PAYLOAD = {
	'light': [ {
		'_type': 'light',
		'~': "{prefix}/light",
		'name': "_",
		'stat_t': "~/{id}/power{bit}/state",
		'cmd_t': "~/{id2}/power/command",
		} ],
	'fan': [ {
		'_type': 'fan',
		'~': "{prefix}/fan/{id}",
		'name': "{prefix}_fan_{id}",
		'stat_t': "~/power/state",
		'cmd_t': "~/power/command",
		'spd_stat_t': "~/speed/state",
		'spd_cmd_t': "~/speed/command",
		'pl_on': 5,
		'pl_off': 6,
		'pl_lo_spd': 3,
		'pl_med_spd': 2,
		'pl_hi_spd': 1,
		'spds': ['low', 'medium', 'high'],
		} ],
	'thermostat': [ {
		'_type': 'climate',
		'~': "{prefix}/thermostat/{id}",
		'name': "{prefix}_thermostat_{id}",
		'mode_stat_t': "~/power/state",
		'mode_cmd_t': "~/power/command",
		'temp_stat_t': "~/target/state",
		'temp_cmd_t': "~/target/command",
		'curr_temp_t': "~/current/state",
		'modes': [ 'off', 'heat' ],
		'min_temp': 15,
		'max_temp': 30,
		} ],
	'plug': [ {
		'_type': 'switch',
		'~': "{prefix}/plug/{id}/power",
		'name': "{prefix}_plug_{id}",
		'stat_t': "~/state",
		'cmd_t': "~/command",
		'icon': "mdi:power-plug",
		},
		{
		'_type': 'switch',
		'~': "{prefix}/plug/{id}/idlecut",
		'name': "{prefix}_plug_{id}_standby_cutoff",
		'stat_t': "~/state",
		'cmd_t': "~/command",
		'icon': "mdi:leaf",
		},
		{
		'_type': 'sensor',
		'~': "{prefix}/plug/{id}",
		'name': "{prefix}_plug_{id}_power_usage",
		'stat_t': "~/current/state",
		'unit_of_meas': "W",
		} ],
	'cutoff': [ {
		'_type': 'switch',
		'~': "{prefix}/cutoff/{id}/power",
		'name': "{prefix}_light_cutoff_{id}",
		'stat_t': "~/state",
		'cmd_t': "~/command",
		} ],
	'gas_valve': [ {
		'_type': 'binary_sensor',
		'~': "{prefix}/gas_valve/{id}",
		'name': "{prefix}_gas_valve_{id}",
		'stat_t': "~/current/state",
		} ],
	'energy': [ {
		'_type': 'sensor',
		'~': "{prefix}/plug/{id}",
		'name': "_",
		'stat_t': "~/current/state",
		'unit_of_meas': "_",
		} ]
	}

DEVICE_HEADER = 0xB0
STATE_HEADER = { prop['state']['header']:(device, prop['state']['length']) for device, prop in RS485_DEVICE.items()
		if 'state' in prop }
QUERY_HEADER = { prop['query']['header']:(device, prop['query']['length']) for device, prop in RS485_DEVICE.items()
		if 'query' in prop }

# human error를 로그로 찍기 위해서 그냥 전부 구독하자
#SUB_LIST = { "{}/{}/+/+/command".format(Options['mqtt']['prefix'], device) for device in RS485_DEVICE } |\
#		{ "{}/entrance/{}/trigger/command".format(Options['mqtt']['prefix'], trigger) for trigger in ENTRANCE_SWITCH['trigger'] }

entrance_watch = {}
entrance_trigger = {}
entrance_ack = {}

serial_queue = {}
serial_ack = {}

last_topic_list = {}

ser = serial.Serial()
mqtt = paho_mqtt.Client()
mqtt_connected = False

def init_entrance():
	if Options['entrance_mode'] == 'full':
		global entrance_watch
		entrance_watch = { prop['header']:prop['resp'].to_bytes(4, 'big') for prop in ENTRANCE_SWITCH['default'].values() }
		# full 모드에서 일괄소등 제어는 가상 현관스위치가 담당
		STATE_HEADER.pop(RS485_DEVICE['cutoff']['state']['header'])
		RS485_DEVICE.pop('cutoff')

	elif Options['entrance_mode'] == 'minimal':
		# minimal 모드에서 일괄소등은 월패드 애드온에서만 제어 가능
		ENTRANCE_SWITCH['trigger'].pop('light')

def mqtt_add_entrance():
	if Options['entrance_mode'] == 'off': return

	prefix = Options['mqtt']['prefix']
	for payloads in DISCOVERY_ENTRANCE:
		payload = payloads.copy()
		payload['~'] = payload['~'].format(prefix)
		payload['name'] = payload['name'].format(prefix)

		# discovery에 등록
		topic = "homeassistant/switch/{}/config".format(payload['name'])
		print("Add new device: ", topic)
		mqtt.publish(topic, json.dumps(payload), retain=True)

def mqtt_entrance(topics, payload):
	triggers = ENTRANCE_SWITCH['trigger']
	trigger = topics[2]

	# HA에서 잘못 보내는 경우 체크
	if len(topics) != 4:
		print("    invalid topic length!"); return
	if trigger not in triggers:
		print("    invalid trigger!"); return

	# OFF가 없는데(ev, gas) OFF가 오면, 이전 ON 명령의 시도 중지
	if payload not in triggers[trigger]:
		entrance_pop(trigger, 'ON')
		return

	# 오류 체크 끝났으면 queue 에 넣어둠
	entrance_trigger[(trigger, payload)] = Options['rs485']['max_retry']
	entrance_ack[triggers[trigger]['ack']] = (trigger, payload)

	# ON만 있는 명령은, 명령이 queue에 있는 동안 switch를 ON으로 표시
	prefix = Options['mqtt']['prefix']
	if 'OFF' not in triggers[trigger]:
		topic = "{}/entrance/{}/state".format(prefix, trigger)
		print("publish to HA:  ", topic, "=", 'ON')
		mqtt.publish(topic, 'ON')
	# ON/OFF 있는 명령은, 마지막으로 받은 명령대로 표시
	else:
		topic = "{}/entrance/{}/state".format(prefix, trigger)
		print("publish to HA:  ", topic, "=", payload)
		mqtt.publish(topic, payload, retain=True)

	# 그동안 조용히 있었어도, 이젠 가로채서 응답해야 함
	if Options['entrance_mode'] == 'minimal':
		query = ENTRANCE_SWITCH['default']['query']
		entrance_watch[query['header']] = query['resp']
	else:
		# 응답 패턴을 바꾸어야 하는 경우 (일괄소등)
		if trigger in ENTRANCE_SWITCH['default'] and payload in ENTRANCE_SWITCH['default'][device]:
			entrance_watch[ENTRANCE_SWITCH['default'][device]['header']] = ENTRANCE_SWITCH['default'][device][payload]

def mqtt_device(topics, payload):
	device = topics[1]
	id = topics[2]
	cmd = topics[3]

	# HA에서 잘못 보내는 경우 체크
	if device not in RS485_DEVICE:
		print("    unknown device!"); return
	if cmd not in RS485_DEVICE[device]:
		print("    unknown command!"); return
	if payload == '':
		print("    no payload!"); return

	# ON, OFF인 경우만 1, 0으로 변환, 복잡한 경우 (fan 등) 는 yaml 에서 하자
	if payload == 'ON': payload = '1'
	elif payload == 'OFF': payload = '0'
	elif payload == 'heat': payload = '1'
	elif payload == 'off': payload = '0'

	# 오류 체크 끝났으면 serial 메시지 생성
	cmd = RS485_DEVICE[device][cmd]

	packet = bytearray(cmd['length'])
	packet[0] = cmd['header'] >> 8
	packet[1] = cmd['header'] & 0xFF
	packet[cmd['pos']] = int(float(payload))

	if 'id' in cmd: packet[cmd['id']] = int(id)

	packet[-1] = serial_generate_checksum(packet)
	ack = packet[0:3]
	ack[0] = 0xB0

	# queue 에 넣어둠
	packet = bytes(packet)
	ack = int.from_bytes(ack, 'big')

	serial_queue[packet] = Options['rs485']['max_retry']
	serial_ack[ack] = packet

def mqtt_on_message(mqtt, userdata, msg):
	topics = msg.topic.split('/')
	payload = msg.payload.decode()

	print("recv. from HA:  ", msg.topic, "=", payload)

	device = topics[1]
	if device == "entrance":
		mqtt_entrance(topics, payload)
	else:
		mqtt_device(topics, payload)

def mqtt_on_connect(mqtt, userdata, flags, rc):
	if rc == 0:
		print("MQTT connect successful!")
		global mqtt_connected
		mqtt_connected = True
	else:
		print("MQTT connection return with: ", connack_string(rc))

def start_mqtt_loop():
	mqtt.on_message = mqtt_on_message
	mqtt.on_connect = mqtt_on_connect

	if Options['mqtt']['need_login']:
		mqtt.username_pw_set(Options['mqtt']['user'], Options['mqtt']['passwd'])
	mqtt.connect(Options['mqtt']['server'], Options['mqtt']['port'])

	mqtt.loop_start()

	delay = 1
	while not mqtt_connected:
		print("waiting MQTT connected ...")
		time.sleep(delay)
		delay = min(delay*2, 30)
	print("Done!")

	prefix = Options['mqtt']['prefix']
	if Options['entrance_mode'] != 'off':
		mqtt.subscribe("{}/entrance/+/command".format(prefix), 0)
	if Options['wallpad_mode'] != 'off':
		mqtt.subscribe("{}/+/+/+/command".format(prefix), 0)

def entrance_pop(trigger, cmd):
	query = ENTRANCE_SWITCH['default']['query']
	triggers = ENTRANCE_SWITCH['trigger']

	entrance_trigger.pop((trigger, cmd), None)
	entrance_ack.pop(triggers[trigger]['ack'], None)

	# ON만 있는 명령은, 명령이 queue에서 빠지면 OFF로 표시
	if 'OFF' not in triggers[trigger]:
		prefix = Options['mqtt']['prefix']
		topic = "{}/entrance/{}/state".format(prefix, trigger)
		print("publish to HA:  ", topic, "=", 'OFF')
		mqtt.publish(topic, 'OFF', retain=True)

	# minimal 모드일 때, 조용해질지 여부
	if not entrance_trigger and Options['entrance_mode'] == 'minimal':
		entrance_watch.pop(query['header'], None)

def entrance_query(header):
	query = ENTRANCE_SWITCH['default']['query']
	triggers = ENTRANCE_SWITCH['trigger']

	# 아직 2Byte 덜 받았으므로 올때까지 기다리는게 정석 같지만,
	# 조금 일찍 시작하는게 성공률이 더 높은거 같기도 하다.
	length = 2 - Options['rs485']['early_response']
	if length > 0:
		while ser.in_waiting < length: pass

	if entrance_trigger and header == query['header']:
		# 하나 뽑아서 보내봄
		trigger, cmd = next(iter(entrance_trigger))
		resp = triggers[trigger][cmd].to_bytes(4, 'big')
		send(resp)

		# retry count 관리, 초과했으면 제거
		retry = entrance_trigger[trigger, cmd]
		print("send to wallpad: {} (life {})".format(resp.hex(), retry))
		if not retry:
			print("    {} max retry count exceeded!".format(resp.hex()))
			entrance_pop(trigger, cmd)
		else:
			entrance_trigger[trigger, cmd] = retry - 1

	# full 모드일 때, 일상 응답
	else:
		resp = entrance_watch[header]
		send(resp)

def entrance_clear(header):
	query = ENTRANCE_SWITCH['default']['query']

	print("ack frm wallpad:", hex(header))

	# 성공한 명령을 지움
	entrance_pop(*entrance_ack[header])
	entrance_ack.pop(header, None)

	# 뒷부분 꺼내서 버림
	recv(2)

def serial_verify_checksum(packet):
	# 모든 byte를 XOR
	checksum = 0
	for b in packet:
		checksum ^= b

	# parity의 최상위 bit는 항상 0
	if checksum >= 0x80: checksum -= 0x80

	# checksum이 안맞으면 로그만 찍고 무시
	if checksum:
		print("checksum fail! {}, {:02x}".format(packet.hex(), checksum))
		return False

	# 정상
	return True

def serial_generate_checksum(packet):
	# 모든 byte를 XOR
	checksum = 0
	for b in packet:
		checksum ^= b

	# parity의 최상위 bit는 항상 0
	if checksum >= 0x80: checksum -= 0x80

	return checksum

def serial_peek_value(parse, packet):
	attr, pos, pattern = parse
	value = packet[pos]

	if pattern == 'bitmap':
		res = []
		for i in range(1,8+1):
			res += [('{}{}'.format(attr, i), 'ON' if value & 1 else 'OFF')]
			value >>= 1
		return res
	elif pattern == 'toggle':
		value = 'ON' if value & 1 else 'OFF'
	elif pattern == 'toggle2':
		value = 'ON' if value & 0x10 else 'OFF'
	elif pattern == 'fan_toggle':
		value = 5 if value == 0 else 6
	elif pattern == 'heat_toggle':
		value = 'heat' if value & 1 else 'off'
	elif pattern == 'value':
		pass
	elif pattern == '2Byte':
		value += packet[pos-1] * 0x100
	elif pattern == '4_2decimal':
		value = float(packet[pos:pos+3].hex()) / 100

	return [(attr, value)]

def serial_new_device(device, id, packet, last_query):
	prefix = Options['mqtt']['prefix']

	# 조명은 두 id를 조합해서 개수와 번호를 정해야 함
	if device == 'light':
		id2 = last_query[3]
		num = id >> 4
		id = int('{:x}'.format(id))

		for bit in range(0, num):
			payload = DISCOVERY_PAYLOAD[device][0].copy()
			payload['~'] = payload['~'].format(prefix=prefix, id=id)
			payload['name'] = "{}_light_{}".format(prefix, id2+bit)
			payload['stat_t'] = payload['stat_t'].format(id=id, bit=bit+1)
			payload['cmd_t'] = payload['cmd_t'].format(id2=id2+bit)

			# discovery에 등록
			topic = "homeassistant/{}/{}/config".format(payload['_type'], payload['name'])
			payload.pop('_type')
			print("Add new device: ", topic)
			mqtt.publish(topic, json.dumps(payload), retain=True)

	elif device in DISCOVERY_PAYLOAD:
		for payloads in DISCOVERY_PAYLOAD[device]:
			payload = payloads.copy()
			payload['~'] = payload['~'].format(prefix=prefix, id=id)
			payload['name'] = payload['name'].format(prefix=prefix, id=id)

			# 실시간 에너지 사용량에는 적절한 이름과 단위를 붙여준다 (단위가 없으면 그래프로 출력이 안됨)
			if device == 'energy':
				payload['name'] = "{}_{}_consumption".format(prefix, ('power', 'gas', 'water')[id])
				payload['unit_of_meas'] = ('Wh', 'm³', 'm³')[id]

			# discovery에 등록
			topic = "homeassistant/{}/{}/config".format(payload['_type'], payload['name'])
			payload.pop('_type')
			print("Add new device: ", topic)
			mqtt.publish(topic, json.dumps(payload), retain=True)

def serial_receive_state(device, packet):
	form = RS485_DEVICE[device]['state']
	last = RS485_DEVICE[device]['last']

	if form.get('id') != None:
		id = packet[form['id']]
	else:
		id = 1

	# 해당 ID의 이전 상태와 같은 경우 바로 무시
	if last.get(id) == packet:
		return
	# 처음 받은 상태인 경우, discovery 용도로 등록한다.
	elif Options['mqtt']['discovery'] and not last.get(id):
		# 전등 때문에 last query도 필요... 지금 패킷과 일치하는지 검증
		if last_query[1] == packet[1]:
			serial_new_device(device, id, packet, last_query)
			last[id] = packet
	else:
		last[id] = packet

	# device 종류에 따라 전송할 데이터 정리
	value_list = []
	for parse in form['parse']:
		value_list += serial_peek_value(parse, packet)

	# MQTT topic 형태로 변환, 이전 상태와 같은지 한번 더 확인해서 무시하거나 publish
	for attr, value in value_list:
		prefix = Options['mqtt']['prefix']
		topic = "{}/{}/{:x}/{}/state".format(prefix, device, id, attr)
		if last_topic_list.get(topic) == value: continue

		if attr != 'current': # 전력사용량이나 현재온도는 너무 자주 바뀌어서 로그 제외
			print("publish to HA:   {} = {} ({})".format(topic, value, packet.hex()))
		mqtt.publish(topic, value, retain=True)
		last_topic_list[topic] = value

def serial_get_header():
	try:
		# 0x80보다 큰 byte가 나올 때까지 대기
		while 1:
			header_0 = recv(1)[0]
			if header_0 >= 0x80: break

		# 중간에 corrupt되는 data가 있으므로 연속으로 0x80보다 큰 byte가 나오면 먼젓번은 무시한다
		while 1:
			header_1 = recv(1)[0]
			if header_1 < 0x80: break
			header_0 = header_1

	except (OSError, serial.SerialException):
		print("ignore exception!")
		header_0 = header_1 = 0

	# 헤더 반환
	return header_0, header_1

def serial_ack_command(packet):
	print("ack from device: {} ({:x})".format(serial_ack[packet].hex(), packet))

	# 성공한 명령을 지움
	if serial_ack[packet] in serial_queue:
		serial_queue.pop(serial_ack[packet])
	serial_ack.pop(packet)

def serial_send_command():
	pop_list = []

	# 한번에 여러개 보내면 응답이랑 꼬여서 망함
	cmd = next(iter(serial_queue))
	send(cmd)

	# retry count 관리, 초과했으면 제거
	retry = serial_queue[cmd]
	print("send to device:  {} (life {})".format(cmd.hex(), retry))
	if not retry:
		print("    cmd {} max retry count exceeded!".format(cmd.hex()))
		ack = bytearray(cmd[0:3])
		ack[0] = 0xB0
		ack = int.from_bytes(ack, 'big')

		serial_queue.pop(cmd)
		serial_ack.pop(ack)
	else:
		serial_queue[cmd] = retry - 1

def init_socket():
	addr = Options['socket']['address']
	port = Options['socket']['port']

	soc = socket.socket()
	soc.connect((addr, port))

	global recv
	global send
	recv = soc.recv
	send = soc.sendall

def init_serial():
	ser.port = Options['serial']['port']
	ser.baudrate = Options['serial']['baudrate']
	ser.bytesize = Options['serial']['bytesize']
	ser.parity = Options['serial']['parity']
	ser.stopbits = Options['serial']['stopbits']

	ser.close()
	ser.open()

	global recv
	global send
	recv = ser.read
	send = ser.write

def serial_loop():
	print("[Info] start loop ...")

	while True:
		# 로그 출력
		sys.stdout.flush()

		# 첫 Byte만 0x80보다 큰 두 Byte를 찾음
		header_0, header_1 = serial_get_header()
		header = (header_0 << 8) | header_1

		# 현관 스위치로써 응답해야 할 header인지 확인
		if header in entrance_watch:
			entrance_query(header)

		elif header in entrance_ack:
			entrance_clear(header)

		# device로부터의 state 응답이면 확인해서 필요시 HA로 전송해야 함
		if header in STATE_HEADER:
			packet = bytes([header_0, header_1])

			# 몇 Byte짜리 패킷인지 확인
			device, length = STATE_HEADER[header]

			# 해당 길이만큼 읽음
			packet += recv(length - 2)

			# checksum 오류 없는지 확인
			if not serial_verify_checksum(packet): pass

			# 적절히 처리한다
			serial_receive_state(device, packet)

		elif header_0 == DEVICE_HEADER:
			# 한 byte 더 뽑아서, 보냈던 명령의 ack인지 확인
			header_2 = recv(1)[0]
			header = (header << 8) | header_2

			if header in serial_ack:
				serial_ack_command(header)

		# 마지막으로 받은 query를 저장해둔다 (조명 discovery에 필요)
		elif header in QUERY_HEADER:
			# 나머지 더 뽑아서 저장
			global last_query
			packet = recv(QUERY_HEADER[header][1] - 2)
			packet = header.to_bytes(2, 'big') + packet
			last_query = packet

		# 명령을 보낼 타이밍인지 확인
		if format(header, 'x') == Options['rs485']['last_packet'][0:4].lower():
			if serial_queue:
				serial_send_command()

if __name__ == '__main__':
	if len(sys.argv) == 1:
		option_file = "./options_standalone.json"
	else:
		option_file = sys.argv[1]

	global Options
	with open(option_file) as f:
		Options = json.load(f)

	init_entrance()

	if Options['serial_mode'] == 'socket':
		print("initialize socket...")
		init_socket()
	else:
		print("initialize serial...")
		init_serial()

	start_mqtt_loop()
	mqtt_add_entrance()

	serial_loop()
