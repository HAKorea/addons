# first written by Nandflash("저장장치") <github@printk.info> since 2020-06-25

import socket
import serial
import paho.mqtt.client as paho_mqtt
import json

import sys
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import os.path

####################
# 가상의 현관 스위치로 동작하는 부분
ENTRANCE_SWITCH = {
    # 평상시 다양한 응답
    "default": {
        "init":  { "header": 0xAD5A, "resp": 0xB05A006A, }, # 처음 전기가 들어왔거나 한동안 응답을 안했을 때, 이것부터 해야 함
        "query": { "header": 0xAD41, "resp": 0xB0560066, }, # 여기에 0xB0410071로 응답하면 gas valve 상태는 전달받지 않음
        "gas":   { "header": 0xAD56, "resp": 0xB0410071, }, # 0xAD41에 항상 0xB041로 응답하면 이게 실행될 일은 없음
        "light": { "header": 0xAD52, "resp": 0xB0520163, "ON": 0xB0520063, "OFF": 0xB0520162, },
    },

    # 0xAD41에 다르게 응답하는 방법들, 이 경우 월패드가 다시 ack를 보내준다
    "trigger": {
        "gas":   { "ack": 0xAD55, "ON": 0xB0550164, },
        "light": { "ack": 0xAD54, "ON": 0xB0540064, "OFF":  0xB0540165, }, # ON: 일괄소등(차단), OFF: 해제
        "ev":    { "ack": 0xAD2F, "ON": 0xB02F011E, },
    },
}

####################
# 기존 월패드 애드온의 역할하는 부분
RS485_DEVICE = {
    # 전등 스위치
    "light": {
        "query":    { "header": 0xAC79, "length":  5, "id": 2, },
        "state":    { "header": 0xB079, "length":  5, "id": 2, "parse": {("power", 3, "bitmap")} },
        "last":     { },

        "power":    { "header": 0xAC7A, "length":  5, "id": 2, "pos": 3, },
    },

    # 환기장치 (전열교환기)
    "fan": {
        "query":    { "header": 0xC24E, "length":  6, },
        "state":    { "header": 0xB04E, "length":  6, "parse": {("power", 4, "fan_toggle"), ("speed", 2, "value")} },
        "last":     { },

        "power":    { "header": 0xC24F, "length":  6, "pos": 2, },
        "speed":    { "header": 0xC24F, "length":  6, "pos": 2, },
    },

    # 각방 난방 제어
    "thermostat": {
        "query":    { "header": 0xAE7C, "length":  8, "id": 2, },
        "state":    { "header": 0xB07C, "length":  8, "id": 2, "parse": {("power", 3, "heat_toggle"), ("target", 4, "value"), ("current", 5, "value")} },
        "last":     { },

        "power":    { "header": 0xAE7D, "length":  8, "id": 2, "pos": 3, },
        "target":   { "header": 0xAE7F, "length":  8, "id": 2, "pos": 3, },
    },

    # 대기전력차단 스위치 (전력사용량 확인)
    "plug": {
        "query":    { "header": 0xC64A, "length": 10, "id": 2, },
        "state":    { "header": 0xB04A, "length": 10, "id": 2, "parse": {("power", 3, "toggle"), ("idlecut", 3, "toggle2"), ("current", 5, "2Byte")} },
        "last":     { },

        "power":    { "header": 0xC66E, "length": 10, "id": 2, "pos": 3, },
        "idlecut":  { "header": 0xC64B, "length": 10, "id": 2, "pos": 3, },
    },

    # 일괄조명: 현관 스위치 살아있으면...
    "cutoff": {
        "query":    { "header": 0xAD52, "length":  4, },
        "state":    { "header": 0xB052, "length":  4, "parse": {("power", 2, "toggle")} }, # 1: 정상, 0: 일괄소등
        "last":     { },

        "power":    { "header": 0xAD53, "length":  4, "pos": 2, },
    },

    # 부엌 가스 밸브
    "gas_valve": {
        "query":    { "header": 0xAB41, "length":  4, },
        #"state":    { "header": 0xB041, "length":  4, "parse": {("power", 2, "toggle")} }, # 0: 정상, 1: 차단; 0xB041은 공용 ack이므로 처리하기 복잡함
        "state":    { "header": 0xAD56, "length":  4, "parse": {("power", 2, "gas_toggle")} }, # 0: 정상, 1: 차단; 월패드가 현관 스위치에 보내주는 정보로 확인 가능
        "last":     { },

        "power":    { "header": 0xAB78, "length":  4, }, # 0 으로 잠그기만 가능
    },

    # 실시간에너지 0:전기, 1:가스, 2:수도
    "energy": {
        "query":    { "header": 0xAA6F, "length":  4, "id": 2, },
        "state":    { "header": 0xB06F, "length":  7, "id": 2, "parse": {("current", 3, "4_2decimal")} },
        "last":     { },
    },
}

RS485_EVENT = {
    "phone1": {
        "header": 0xA5, "length": 4, "normal": 0x41, "last": {},
        "text": { 0x41: "대기중", 0x3E: "대기중", 0x31: "현관", 0x32: "공동현관", }
    },
    "phone2": {
        "header": 0xA6, "length": 4, "normal": 0x41, "last": {},
        "text": { 0x41: "대기중", 0x3E: "대기중", 0x31: "현관", 0x32: "공동현관", }
    },
}

DISCOVERY_ENTRANCE = [
    {
        "~": "{}/entrance/ev",
        "name": "{}_elevator",
        "stat_t": "~/state",
        "cmd_t": "~/command",
        "icon": "mdi:elevator",
    },
    {
        "~": "{}/entrance/gas",
        "name": "{}_gas_cutoff",
        "stat_t": "~/state",
        "cmd_t": "~/command",
        "icon": "mdi:valve",
    },
    {
        "~": "{}/entrance/light",
        "name": "{}_entrance_all_light",
        "stat_t": "~/state",
        "cmd_t": "~/command",
        "icon": "mdi:lightbulb-group-off",
    },
]

DISCOVERY_PAYLOAD = {
    "light": [ {
        "_type": "light",
        "~": "{prefix}/light",
        "name": "_",
        "stat_t": "~/{idn}/power{bit}/state",
        "cmd_t": "~/{id2}/power/command",
    } ],
    "fan": [ {
        "_type": "fan",
        "~": "{prefix}/fan/{idn}",
        "name": "{prefix}_fan_{idn}",
        "stat_t": "~/power/state",
        "cmd_t": "~/power/command",
        "spd_stat_t": "~/speed/state",
        "spd_cmd_t": "~/speed/command",
        "pl_on": 5,
        "pl_off": 6,
        "pl_lo_spd": 3,
        "pl_med_spd": 2,
        "pl_hi_spd": 1,
        "spds": ["low", "medium", "high"],
    } ],
    "thermostat": [ {
        "_type": "climate",
        "~": "{prefix}/thermostat/{idn}",
        "name": "{prefix}_thermostat_{idn}",
        "mode_stat_t": "~/power/state",
        "mode_cmd_t": "~/power/command",
        "temp_stat_t": "~/target/state",
        "temp_cmd_t": "~/target/command",
        "curr_temp_t": "~/current/state",
        "modes": [ "off", "heat" ],
        "min_temp": 10,
        "max_temp": 30,
    } ],
    "plug": [ {
        "_type": "switch",
        "~": "{prefix}/plug/{idn}/power",
        "name": "{prefix}_plug_{idn}",
        "stat_t": "~/state",
        "cmd_t": "~/command",
        "icon": "mdi:power-plug",
    },
    {
        "_type": "switch",
        "~": "{prefix}/plug/{idn}/idlecut",
        "name": "{prefix}_plug_{idn}_standby_cutoff",
        "stat_t": "~/state",
        "cmd_t": "~/command",
        "icon": "mdi:leaf",
    },
    {
        "_type": "sensor",
        "~": "{prefix}/plug/{idn}",
        "name": "{prefix}_plug_{idn}_power_usage",
        "stat_t": "~/current/state",
        "unit_of_meas": "W",
    } ],
    "cutoff": [ {
        "_type": "switch",
        "~": "{prefix}/cutoff/{idn}/power",
        "name": "{prefix}_light_cutoff_{idn}",
        "stat_t": "~/state",
        "cmd_t": "~/command",
    } ],
    "gas_valve": [ {
        "_type": "sensor",
        "~": "{prefix}/gas_valve/{idn}",
        "name": "{prefix}_gas_valve_{idn}",
        "stat_t": "~/power/state",
    } ],
    "energy": [ {
        "_type": "sensor",
        "~": "{prefix}/energy/{idn}",
        "name": "_",
        "stat_t": "~/current/state",
        "unit_of_meas": "_",
    } ],
}

DISCOVERY_EVENT = {
    "phone1": {
        "_type": "sensor",
        "~": "{prefix}/phone1/{idn}",
        "name": "{prefix}_phone1",
        "stat_t": "~/event/state",
    },
    "phone2": {
        "_type": "sensor",
        "~": "{prefix}/phone2/{idn}",
        "name": "{prefix}_phone2",
        "stat_t": "~/event/state",
    },
}

STATE_HEADER = {
    prop["state"]["header"]: (device, prop["state"]["length"] - 2)
    for device, prop in RS485_DEVICE.items()
    if "state" in prop
}
QUERY_HEADER = {
    prop["query"]["header"]: (device, prop["query"]["length"] - 2)
    for device, prop in RS485_DEVICE.items()
    if "query" in prop
}
EVENT_HEADER = {
    prop["header"]: (event, prop["length"] - 2)
    for event, prop in RS485_EVENT.items()
}

HEADER_0_STATE = 0xB0
HEADER_0_FIRST = 0xA1
HEADER_1_SCAN = 0x5A
header_0_first_candidate = [ 0xAB, 0xAC, 0xAD, 0xAE, 0xC2, 0xA5 ]


# human error를 로그로 찍기 위해서 그냥 전부 구독하자
#SUB_LIST = { "{}/{}/+/+/command".format(Options["mqtt"]["prefix"], device) for device in RS485_DEVICE } |\
#           { "{}/entrance/{}/trigger/command".format(Options["mqtt"]["prefix"], trigger) for trigger in ENTRANCE_SWITCH["trigger"] }

entrance_watch = {}
entrance_trigger = {}
entrance_ack = {}

serial_queue = {}
serial_ack = {}

last_query = int(0).to_bytes(2, "big")
last_topic_list = {}

ser = serial.Serial()
mqtt = paho_mqtt.Client()
mqtt_connected = False

logger = logging.getLogger(__name__)
formatter = logging.Formatter(fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%H:%M:%S")


def init_logger():
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def init_logger_file():
    if Options["log"]["to_file"]:
        filename = Options["log"]["filename"]
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        handler = TimedRotatingFileHandler(os.path.abspath(Options["log"]["filename"]), when="midnight", backupCount=7)
        handler.setFormatter(formatter)
        handler.suffix = '%Y%m%d'
        logger.addHandler(handler)


def init_option(argv):
    # option 파일 선택
    if len(argv) == 1:
        option_file = "./options_standalone.json"
    else:
        option_file = argv[1]

    # configuration이 예전 버전이어도 최대한 동작 가능하도록,
    # 기본값에 해당하는 파일을 먼저 읽고나서 설정 파일로 업데이트 한다.
    global Options

    # 기본값 파일은 .py 와 같은 경로에 있음
    default_file = os.path.join(os.path.dirname(os.path.abspath(argv[0])), "options_example.json")

    with open(default_file) as f:
        Options = json.load(f)
    with open(option_file) as f:
        Options2 = json.load(f)

    # 업데이트
    for k, v in Options.items():
        if type(v) is dict and k in Options2:
            Options[k].update(Options2[k])
            for k2 in Options[k].keys():
                if k2 not in Options2[k].keys():
                    logging.warning("no configuration value for '{}:{}'! try default value ({})...".format(k, k2, Options[k][k2]))
        else:
            if k not in Options2:
                logging.warning("no configuration value for '{}'! try default value ({})...".format(k, Options[k]))
            else:
                Options[k] = Options2[k]


def init_entrance():
    if Options["entrance_mode"] == "full":
        global entrance_watch
        entrance_watch = {
            prop["header"]: prop["resp"].to_bytes(4, "big")
            for prop in ENTRANCE_SWITCH["default"].values()
        }
        # full 모드에서 일괄소등 제어는 가상 현관스위치가 담당
        STATE_HEADER.pop(RS485_DEVICE["cutoff"]["state"]["header"])
        RS485_DEVICE.pop("cutoff")

    elif Options["entrance_mode"] == "minimal":
        # minimal 모드에서 일괄소등은 월패드 애드온에서만 제어 가능
        ENTRANCE_SWITCH["trigger"].pop("light")


def mqtt_add_entrance():
    if Options["entrance_mode"] == "off": return

    prefix = Options["mqtt"]["prefix"]
    for payloads in DISCOVERY_ENTRANCE:
        payload = payloads.copy()
        payload["~"] = payload["~"].format(prefix)
        payload["name"] = payload["name"].format(prefix)

        # discovery에 등록
        topic = "homeassistant/switch/{}/config".format(payload["name"])
        logger.info("Add new device:  {}".format(topic))
        mqtt.publish(topic, json.dumps(payload), retain=True)


def mqtt_entrance(topics, payload):
    triggers = ENTRANCE_SWITCH["trigger"]
    trigger = topics[2]

    # HA에서 잘못 보내는 경우 체크
    if len(topics) != 4:
        logger.error("    invalid topic length!"); return
    if trigger not in triggers:
        logger.error("    invalid trigger!"); return

    # OFF가 없는데(ev, gas) OFF가 오면, 이전 ON 명령의 시도 중지
    if payload not in triggers[trigger]:
        entrance_pop(trigger, "ON")
        return

    # 오류 체크 끝났으면 queue 에 넣어둠
    entrance_trigger[(trigger, payload)] = Options["rs485"]["max_retry"]

    # ON만 있는 명령은, 명령이 queue에 있는 동안 switch를 ON으로 표시
    prefix = Options["mqtt"]["prefix"]
    if "OFF" not in triggers[trigger]:
        topic = "{}/entrance/{}/state".format(prefix, trigger)
        logger.info("publish to HA:   {} = {}".format(topic, "ON"))
        mqtt.publish(topic, "ON")
    # ON/OFF 있는 명령은, 마지막으로 받은 명령대로 표시
    else:
        topic = "{}/entrance/{}/state".format(prefix, trigger)
        logger.info("publish to HA:   {} = {}".format(topic, payload))
        mqtt.publish(topic, payload, retain=True)

    # 그동안 조용히 있었어도, 이젠 가로채서 응답해야 함
    if Options["entrance_mode"] == "minimal":
        query = ENTRANCE_SWITCH["default"]["query"]
        entrance_watch[query["header"]] = query["resp"]
    else:
        # 응답 패턴을 바꾸어야 하는 경우 (일괄소등)
        if trigger in ENTRANCE_SWITCH["default"] and payload in ENTRANCE_SWITCH["default"][device]:
            entrance_watch[ENTRANCE_SWITCH["default"][device]["header"]] = ENTRANCE_SWITCH["default"][device][payload]

def mqtt_device(topics, payload):
    device = topics[1]
    idn = topics[2]
    cmd = topics[3]

    # HA에서 잘못 보내는 경우 체크
    if device not in RS485_DEVICE:
        logger.error("    unknown device!"); return
    if cmd not in RS485_DEVICE[device]:
        logger.error("    unknown command!"); return
    if payload == "":
        logger.error("    no payload!"); return

    # ON, OFF인 경우만 1, 0으로 변환, 복잡한 경우 (fan 등) 는 yaml 에서 하자
    if payload == "ON": payload = "1"
    elif payload == "OFF": payload = "0"
    elif payload == "heat": payload = "1"
    elif payload == "off": payload = "0"

    # 오류 체크 끝났으면 serial 메시지 생성
    cmd = RS485_DEVICE[device][cmd]

    packet = bytearray(cmd["length"])
    packet[0] = cmd["header"] >> 8
    packet[1] = cmd["header"] & 0xFF
    packet[cmd["pos"]] = int(float(payload))

    if "id" in cmd: packet[cmd["id"]] = int(idn)

    # parity 생성 후 queue 에 넣어둠
    packet[-1] = serial_generate_checksum(packet)
    packet = bytes(packet)

    serial_queue[packet] = Options["rs485"]["max_retry"]


def mqtt_on_message(mqtt, userdata, msg):
    topics = msg.topic.split("/")
    payload = msg.payload.decode()

    logger.info("recv. from HA:   {} = {}".format(msg.topic, payload))

    device = topics[1]
    if device == "entrance":
        mqtt_entrance(topics, payload)
    else:
        mqtt_device(topics, payload)


def mqtt_on_connect(mqtt, userdata, flags, rc):
    if rc == 0:
        logger.info("MQTT connect successful!")
        global mqtt_connected
        mqtt_connected = True
    else:
        logger.error("MQTT connection return with:  {}".format(connack_string(rc)))


def start_mqtt_loop():
    mqtt.on_message = mqtt_on_message
    mqtt.on_connect = mqtt_on_connect

    if Options["mqtt"]["need_login"]:
        mqtt.username_pw_set(Options["mqtt"]["user"], Options["mqtt"]["passwd"])
    mqtt.connect(Options["mqtt"]["server"], Options["mqtt"]["port"])

    mqtt.loop_start()

    delay = 1
    while not mqtt_connected:
        logger.info("waiting MQTT connected ...")
        time.sleep(delay)
        delay = min(delay * 2, 10)

    prefix = Options["mqtt"]["prefix"]
    if Options["entrance_mode"] != "off":
        topic = "{}/entrance/+/command".format(prefix)
        logger.info("subscribe {}".format(topic))
        mqtt.subscribe(topic, 0)
    if Options["wallpad_mode"] != "off":
        topic = "{}/+/+/+/command".format(prefix)
        logger.info("subscribe {}".format(topic))
        mqtt.subscribe(topic, 0)


def entrance_pop(trigger, cmd):
    query = ENTRANCE_SWITCH["default"]["query"]
    triggers = ENTRANCE_SWITCH["trigger"]

    entrance_trigger.pop((trigger, cmd), None)
    entrance_ack.pop(triggers[trigger]["ack"], None)

    # ON만 있는 명령은, 명령이 queue에서 빠지면 OFF로 표시
    if "OFF" not in triggers[trigger]:
        prefix = Options["mqtt"]["prefix"]
        topic = "{}/entrance/{}/state".format(prefix, trigger)
        logger.info("publish to HA:   {} = {}".format(topic, "OFF"))
        mqtt.publish(topic, "OFF", retain=True)

    # minimal 모드일 때, 조용해질지 여부
    if not entrance_trigger and Options["entrance_mode"] == "minimal":
        entrance_watch.pop(query["header"], None)


def entrance_query(header):
    query = ENTRANCE_SWITCH["default"]["query"]
    triggers = ENTRANCE_SWITCH["trigger"]

    # 아직 2Byte 덜 받았으므로 올때까지 기다리는게 정석 같지만,
    # 조금 일찍 시작하는게 성공률이 더 높은거 같기도 하다.
    length = 2 - Options["rs485"]["early_response"]
    if length > 0:
        while ser.in_waiting < length: pass

    if entrance_trigger and header == query["header"]:
        # 하나 뽑아서 보내봄
        trigger, cmd = next(iter(entrance_trigger))
        resp = triggers[trigger][cmd].to_bytes(4, "big")
        send(resp)

        # retry count 관리, 초과했으면 제거
        retry = entrance_trigger[trigger, cmd]
        logger.info("send to wallpad: {} (life {})".format(resp.hex(), retry))
        if not retry:
            logger.error("    {} max retry count exceeded!".format(resp.hex()))
            entrance_pop(trigger, cmd)
        else:
            entrance_trigger[trigger, cmd] = retry - 1
            entrance_ack[triggers[trigger]["ack"]] = (trigger, cmd)

    # full 모드일 때, 일상 응답
    else:
        resp = entrance_watch[header]
        send(resp)


def entrance_clear(header):
    query = ENTRANCE_SWITCH["default"]["query"]

    logger.info("ack frm wallpad: {}".format(hex(header)))

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
        logger.warning("checksum fail! {}, {:02x}".format(packet.hex(), checksum))
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

    if pattern == "bitmap":
        res = []
        for i in range(1, 8+1):
            res += [("{}{}".format(attr, i), "ON" if value & 1 else "OFF")]
            value >>= 1
        return res
    elif pattern == "toggle":
        value = "ON" if value & 1 else "OFF"
    elif pattern == "toggle2":
        value = "ON" if value & 0x10 else "OFF"
    elif pattern == "fan_toggle":
        value = 5 if value == 0 else 6
    elif pattern == "heat_toggle":
        value = "heat" if value & 1 else "off"
    elif pattern == "gas_toggle":
        value = "차단" if value & 1 else "열림"
    elif pattern == "value":
        pass
    elif pattern == "2Byte":
        value += packet[pos-1] * 0x100
    elif pattern == "4_2decimal":
        try:
            value = float(packet[pos : pos+3].hex()) / 100
        except:
            # 어쩌다 깨지면 뻗음...
            logger.warning("invalid packet, {} is not decimal".format(packet.hex()))
            value = 0

    return [(attr, value)]


def serial_new_device(device, idn, packet):
    prefix = Options["mqtt"]["prefix"]

    # 조명은 두 id를 조합해서 개수와 번호를 정해야 함
    if device == "light":
        id2 = last_query[3]
        num = idn >> 4
        idn = int("{:x}".format(idn))

        for bit in range(0, num):
            payload = DISCOVERY_PAYLOAD[device][0].copy()
            payload["~"] = payload["~"].format(prefix=prefix, idn=idn)
            payload["name"] = "{}_light_{}".format(prefix, id2+bit)
            payload["stat_t"] = payload["stat_t"].format(idn=idn, bit=bit+1)
            payload["cmd_t"] = payload["cmd_t"].format(id2=id2+bit)

            # discovery에 등록
            topic = "homeassistant/{}/{}/config".format(payload["_type"], payload["name"])
            payload.pop("_type")
            logger.info("Add new device:  {} ({}: {})".format(topic, last_query.hex(), packet.hex()))
            mqtt.publish(topic, json.dumps(payload), retain=True)

    elif device in DISCOVERY_PAYLOAD:
        for payloads in DISCOVERY_PAYLOAD[device]:
            payload = payloads.copy()
            payload["~"] = payload["~"].format(prefix=prefix, idn=idn)
            payload["name"] = payload["name"].format(prefix=prefix, idn=idn)

            # 실시간 에너지 사용량에는 적절한 이름과 단위를 붙여준다 (단위가 없으면 그래프로 출력이 안됨)
            if device == "energy":
                payload["name"] = "{}_{}_consumption".format(prefix, ("power", "gas", "water")[idn])
                payload["unit_of_meas"] = ("Wh", "m³", "m³")[idn]

            # discovery에 등록
            topic = "homeassistant/{}/{}/config".format(payload["_type"], payload["name"])
            payload.pop("_type")
            logger.info("Add new device:  {}".format(topic))
            mqtt.publish(topic, json.dumps(payload), retain=True)


def serial_new_event(device, packet):
    prefix = Options["mqtt"]["prefix"]
    idn = 1

    if device in DISCOVERY_EVENT:
        payload = DISCOVERY_EVENT[device]
        payload["~"] = payload["~"].format(prefix=prefix, idn=idn)
        payload["name"] = payload["name"].format(prefix=prefix, idn=idn)

        # discovery에 등록
        topic = "homeassistant/{}/{}/config".format(payload["_type"], payload["name"])
        payload.pop("_type")
        logger.info("Add new device:  {}".format(topic))
        mqtt.publish(topic, json.dumps(payload), retain=True)


def serial_receive_state(device, packet):
    form = RS485_DEVICE[device]["state"]
    last = RS485_DEVICE[device]["last"]

    if form.get("id") != None:
        idn = packet[form["id"]]
    else:
        idn = 1

    # 해당 ID의 이전 상태와 같은 경우 바로 무시
    if last.get(idn) == packet:
        return

    # 처음 받은 상태인 경우, discovery 용도로 등록한다.
    if Options["mqtt"]["discovery"] and not last.get(idn):
        # 전등 때문에 last query도 필요... 지금 패킷과 일치하는지 검증
        # gas valve는 일치하지 않는다
        if last_query[1] == packet[1] or device == "gas_valve":
            serial_new_device(device, idn, packet)
            last[idn] = True

        # 장치 등록 먼저 하고, 상태 등록은 그 다음 턴에 한다. (난방 상태 등록 무시되는 현상 방지)
        return

    else:
        last[idn] = packet

    # device 종류에 따라 전송할 데이터 정리
    value_list = []
    for parse in form["parse"]:
        value_list += serial_peek_value(parse, packet)

    # MQTT topic 형태로 변환, 이전 상태와 같은지 한번 더 확인해서 무시하거나 publish
    for attr, value in value_list:
        prefix = Options["mqtt"]["prefix"]
        topic = "{}/{}/{:x}/{}/state".format(prefix, device, idn, attr)
        if last_topic_list.get(topic) == value: continue

        if attr != "current":  # 전력사용량이나 현재온도는 너무 자주 바뀌어서 로그 제외
            logger.info("publish to HA:   {} = {} ({})".format(topic, value, packet.hex()))
        mqtt.publish(topic, value, retain=True)
        last_topic_list[topic] = value


def serial_receive_event(device, packet):
    last = RS485_EVENT[device]["last"]
    text = RS485_EVENT[device]["text"]
    normal = RS485_EVENT[device]["normal"]
    idn = 1

    # 이전 상태와 같은 경우 바로 무시
    if last == packet:
        return

    # 처음 받은 상태인 경우, discovery 용도로 등록한다.
    if Options["mqtt"]["discovery"] and not last.get(idn):
        serial_new_event(device, packet)

        # 장치 등록 먼저 하고, 상태 등록은 그 다음 턴에 한다. (상태 등록 무시되는 현상 방지)
        last[idn] = True
        return

    # 이벤트 형식이므로, 평소 패킷이면 최초를 제외하고는 무시
    elif last[idn] != True and packet[1] == normal:
        last[idn] = packet
        return

    last[idn] = packet

    # payload 결정
    if packet[1] in text:
        payload = text[packet[1]]
    else:
        payload = packet[1].hex()

    # MQTT topic 형태로 변환, publish
    prefix = Options["mqtt"]["prefix"]
    topic = "{}/{}/1/event/state".format(prefix, device)

    logger.info("publish to HA:   {} = {} ({})".format(topic, payload, packet.hex()))
    mqtt.publish(topic, payload)

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
        logger.error("ignore exception!")
        header_0 = header_1 = 0

    # 헤더 반환
    return header_0, header_1


def serial_ack_command(packet):
    logger.info("ack from device: {} ({:x})".format(serial_ack[packet].hex(), packet))

    # 성공한 명령을 지움
    serial_queue.pop(serial_ack[packet], None)
    serial_ack.pop(packet)


def serial_send_command():
    # 한번에 여러개 보내면 응답이랑 꼬여서 망함
    cmd = next(iter(serial_queue))
    send(cmd)

    ack = bytearray(cmd[0:3])
    ack[0] = 0xB0
    ack = int.from_bytes(ack, "big")

    # retry count 관리, 초과했으면 제거
    retry = serial_queue[cmd]
    logger.info("send to device:  {} (life {})".format(cmd.hex(), retry))
    if not retry:
        logger.error("    cmd {} max retry count exceeded!".format(cmd.hex()))

        serial_queue.pop(cmd)
        serial_ack.pop(ack, None)
    else:
        serial_queue[cmd] = retry - 1
        serial_ack[ack] = cmd


def socket_set_timeout(a):
    soc.settimeout(a)


def init_socket():
    addr = Options["socket"]["address"]
    port = Options["socket"]["port"]

    soc = socket.socket()
    soc.connect((addr, port))

    global recv
    global send
    global set_timeout
    recv = soc.recv
    send = soc.sendall
    set_timeout = socket_set_timeout

    # 소켓에 뭐가 떠다니는지 확인
    soc.settimeout(5.0)
    data = recv(1)
    soc.settimeout(None)
    if not data:
        logger.critical("no active packet at this socket!")


def serial_set_timeout(a):
    ser.timeout = a


def init_serial():
    ser.port = Options["serial"]["port"]
    ser.baudrate = Options["serial"]["baudrate"]
    ser.bytesize = Options["serial"]["bytesize"]
    ser.parity = Options["serial"]["parity"]
    ser.stopbits = Options["serial"]["stopbits"]

    ser.close()
    ser.open()

    global recv
    global send
    global set_timeout
    recv = ser.read
    send = ser.write
    set_timeout = serial_set_timeout

    # 시리얼에 뭐가 떠다니는지 확인
    ser.timeout = 5
    data = recv(1)
    ser.timeout = None

    if not data:
        logger.critical("no active packet at this serial port!")


def serial_loop():
    logger.info("start loop ...")
    loop_count = 0
    scan_count = 0
    send_aggressive = False

    start_time = time.time()
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
            device, remain = STATE_HEADER[header]

            # 해당 길이만큼 읽음
            packet += recv(remain)

            # checksum 오류 없는지 확인
            if not serial_verify_checksum(packet):
                continue

            # 적절히 처리한다
            serial_receive_state(device, packet)

        # 초인종 -> 부엌,화장실 인터폰 패킷 캡처
        elif header_0 in EVENT_HEADER:
            packet = bytes([header_0, header_1])

            # 몇 Byte짜리 패킷인지 확인
            device, remain = EVENT_HEADER[header_0]

            # 해당 길이만큼 읽음
            packet += recv(remain)

            # checksum 오류 없는지 확인
            if not serial_verify_checksum(packet):
                continue

            # 적절히 처리한다
            serial_receive_event(device, packet)

        elif header_0 == HEADER_0_STATE:
            # 한 byte 더 뽑아서, 보냈던 명령의 ack인지 확인
            header_2 = recv(1)[0]
            header = (header << 8) | header_2

            if header in serial_ack:
                serial_ack_command(header)

        # 마지막으로 받은 query를 저장해둔다 (조명 discovery에 필요)
        elif header in QUERY_HEADER:
            # 나머지 더 뽑아서 저장
            global last_query
            packet = recv(QUERY_HEADER[header][1])
            packet = header.to_bytes(2, "big") + packet
            last_query = packet

        # 명령을 보낼 타이밍인지 확인: 0xXX5A 는 장치가 있는지 찾는 동작이므로,
        # 아직도 이러고 있다는건 아무도 응답을 안할걸로 예상, 그 타이밍에 끼어든다.
        elif Options["serial_mode"] == "serial" and (header_1 == HEADER_1_SCAN or send_aggressive):
            scan_count += 1
            if serial_queue:
                serial_send_command()

        # 전체 루프 수 카운트
        global HEADER_0_FIRST
        if header_0 == HEADER_0_FIRST:
            loop_count += 1

            # socket은 bulk로 처리되다보니 타이밍 잡는게 의미가 없다. 그냥 한바퀴에 하나씩 보내봄
            if Options["serial_mode"] == "socket":
                if serial_queue:
                    serial_send_command()

            # 돌만큼 돌았으면 상황 판단
            if loop_count == 30:
                # discovery: 가끔 비트가 튈때 이상한 장치가 등록되는걸 막기 위해, 시간제한을 둠
                if Options["mqtt"]["discovery"]:
                    logger.info("Add new device:  All done.")
                    Options["mqtt"]["discovery"] = False
                else:
                    logger.info("running stable...")

                # 스캔이 없거나 적으면, 명령을 내릴 타이밍을 못잡는걸로 판단, 아무때나 닥치는대로 보내봐야한다.
                if Options["serial_mode"] == "serial" and scan_count < 10:
                    logger.warning("    send aggressive mode!", scan_count)
                    send_aggressive = True

        # 루프 카운트 세는데 실패하면 다른 걸로 시도해봄
        if loop_count == 0 and time.time() - start_time > 6:
            logger.warning("check loop count fail: there are no {:X}! try {:X}...".format(HEADER_0_FIRST, header_0_first_candidate[-1]))
            HEADER_0_FIRST = header_0_first_candidate.pop()
            start_time = time.time()
            scan_count = 0


def dump_loop():
    dump_time = Options["rs485"]["dump_time"]

    if dump_time > 0:
        start_time = time.time()
        logger.warning("packet dump for {} seconds!".format(dump_time))

        set_timeout(1)
        logs = []
        while time.time() - start_time < dump_time:
            data = recv(1024)
            for b in data:
                if b == 0xA1 or len(logs) > 500:
                    logger.info("".join(logs))
                    logs = ["{:02X}".format(b)]
                elif b <= 0xA0: logs.append(   "{:02X}".format(b))
                elif b == 0xFF: logs.append(   "{:02X}".format(b))
                elif b == 0xB0: logs.append( ": {:02X}".format(b))
                else:           logs.append(",  {:02X}".format(b))
        logger.info("".join(logs))
        logger.warning("dump done.")
        set_timeout(None)


if __name__ == "__main__":
    # configuration 로드 및 로거 설정
    init_logger()
    init_option(sys.argv)
    init_logger_file()

    # 설정에 따라 현관스위치와 월패드 패킷 겹치는 부분 정리
    init_entrance()

    if Options["serial_mode"] == "socket":
        logger.info("initialize socket...")
        init_socket()
    else:
        logger.info("initialize serial...")
        init_serial()

    dump_loop()

    start_mqtt_loop()
    mqtt_add_entrance()

    try:
        serial_loop()
    except:
        logger.exception("addon finished!")
