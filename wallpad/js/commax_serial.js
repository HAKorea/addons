/**
 * RS485 Homegateway for Commax
 * @소스 공개 : Daehwan, Kang
 * @삼성 홈넷용으로 수정 : erita
 * @수정일 2019-01-11
 * @코맥스 홈넷용으로 수정 : 그레고리하우스
 * @수정일 2019-06-01
 */

const util = require('util');
const SerialPort = require('serialport');
const net = require('net');     // Socket
const mqtt = require('mqtt');

const CONFIG = require('/data/options.json');  //**** 애드온의 옵션을 불러옵니다. 이후 CONFIG.mqtt.username 과 같이 사용가능합니다. 

const CONST = {
    // 포트이름 설정/dev/ttyUSB0
    portName: process.platform.startsWith('win') ? "COM6" : CONFIG.serial.port,
    // SerialPort 전송 Delay(ms)
    sendDelay: CONFIG.sendDelay,
    // MQTT 브로커
    mqttBroker: 'mqtt://'+CONFIG.mqtt.server, // *************** 환경에 맞게 수정하세요! **************
    // MQTT 수신 Delay(ms)
    mqttDelay: CONFIG.mqtt.receiveDelay,

    mqttUser: CONFIG.mqtt.username,  // *************** 환경에 맞게 수정하세요! **************
    mqttPass: CONFIG.mqtt.password, // *************** 환경에 맞게 수정하세요! **************

    clientID: CONFIG.model+'-homenet',

    // 기기별 상태 및 제어 코드(HEX)
    DEVICE_STATE: [
    {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(8,'B0000100000000B1','hex'), power: 'OFF'},
    {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(8,'B0010100000000B2','hex'), power: 'ON'},
    {deviceId: 'Light', subId: '2', stateHex: Buffer.alloc(8,'B0000200000000B2','hex'), power: 'OFF'},
    {deviceId: 'Light', subId: '2', stateHex: Buffer.alloc(8,'B0010200000000B3','hex'), power: 'ON'},
    {deviceId: 'Light', subId: '3', stateHex: Buffer.alloc(8,'B0000300000000B3','hex'), power: 'OFF'},
    {deviceId: 'Light', subId: '3', stateHex: Buffer.alloc(8,'B0010300000000B4','hex'), power: 'ON'},
    {deviceId: 'Light', subId: '4', stateHex: Buffer.alloc(8,'B0000400000000B4','hex'), power: 'OFF'},
    {deviceId: 'Light', subId: '4', stateHex: Buffer.alloc(8,'B0010400000000B5','hex'), power: 'ON'},
    {deviceId: 'Light', subId: '5', stateHex: Buffer.alloc(8,'B0000500000000B5','hex'), power: 'OFF'},
    {deviceId: 'Light', subId: '5', stateHex: Buffer.alloc(8,'B0010500000000B6','hex'), power: 'ON'},

    {deviceId: 'Power', subId: '1', stateHex: Buffer.alloc(8,'F90001110000000B','hex'), power: 'OFF'},
    {deviceId: 'Power', subId: '1', stateHex: Buffer.alloc(8,'F90101110000000C','hex'), power: 'ON'},

    {deviceId: 'BatchSwitch', subId: '1', stateHex: Buffer.alloc(8,'A0000100001500B6','hex'), power: 'OFF'},
    {deviceId: 'BatchSwitch', subId: '1', stateHex: Buffer.alloc(8,'A0010100001500B7','hex'), power: 'ON'},

//        {deviceId: 'Ev', subId: '1', stateHex: Buffer.alloc(8,'2D0000000000002D','hex'), power: 'ON'},		

    {deviceId: 'Thermo', subId: '1', stateHex: Buffer.alloc(3,'828101','hex'), power: 'heat' , setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '1', stateHex: Buffer.alloc(3,'828401','hex'), power: 'off', setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '2', stateHex: Buffer.alloc(3,'828102','hex'), power: 'heat' , setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '2', stateHex: Buffer.alloc(3,'828402','hex'), power: 'off', setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '3', stateHex: Buffer.alloc(3,'828103','hex'), power: 'heat' , setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '3', stateHex: Buffer.alloc(3,'828403','hex'), power: 'off', setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '4', stateHex: Buffer.alloc(3,'828104','hex'), power: 'heat' , setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '4', stateHex: Buffer.alloc(3,'828404','hex'), power: 'off', setTemp: '', curTemp: ''},

//        {deviceId: 'Fan', subId: '1', stateHex: Buffer.alloc(8,'F6000100000000F7','hex'), power: 'OFF', speed: 'low' },
//        {deviceId: 'Fan', subId: '1', stateHex: Buffer.alloc(8,'F6040101000000FC','hex'), power: 'ON', speed: 'low' },
//        {deviceId: 'Fan', subId: '1', stateHex: Buffer.alloc(8,'F6040102000000FD','hex'), power: 'ON', speed: 'mid' },
//        {deviceId: 'Fan', subId: '1', stateHex: Buffer.alloc(8,'F6040103000000FE','hex'), power: 'ON', speed: 'high'},
//        {deviceId: 'Fan', subId: '1', stateHex: Buffer.alloc(8,'F6020101000000FA','hex'), power: 'ON', speed: 'auto'}, //제어신호는 없음
//        {deviceId: 'Fan', subId: '1', stateHex: Buffer.alloc(8,'F6060101000000FE','hex'), power: 'ON', speed: 'night'}, //제어신호는 없음

//        {deviceId: 'Gas', subId: '1', stateHex: Buffer.alloc(8,'9048480000000020','hex'), power: 'OFF'},
//        {deviceId: 'Gas', subId: '1', stateHex: Buffer.alloc(8,'9040400000000010','hex'), power: 'ON'},
//        {deviceId: 'Gas', subId: '1', stateHex: Buffer.alloc(8,'9080800000000090','hex'), power: 'ON'}
],

DEVICE_COMMAND: [
        {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(8,'3101000000000032','hex'), ackHex: Buffer.alloc(8,'B1000100000000B2','hex'), power: 'OFF'}, //거실1--off
        {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(8,'3101010000000033','hex'), ackHex: Buffer.alloc(8,'B1010100000000B3','hex'), power: 'ON' }, //거실1--on
        {deviceId: 'Light', subId: '2', commandHex: Buffer.alloc(8,'3102000000000033','hex'), ackHex: Buffer.alloc(8,'B1000200000000B3','hex'), power: 'OFF'}, //거실2--off
        {deviceId: 'Light', subId: '2', commandHex: Buffer.alloc(8,'3102010000000034','hex'), ackHex: Buffer.alloc(8,'B1010200000000B4','hex'), power: 'ON' }, //거실2--on
        {deviceId: 'Light', subId: '3', commandHex: Buffer.alloc(8,'3103000000000034','hex'), ackHex: Buffer.alloc(8,'B1000300000000B4','hex'), power: 'OFF'}, //거실3--off
        {deviceId: 'Light', subId: '3', commandHex: Buffer.alloc(8,'3103010000000035','hex'), ackHex: Buffer.alloc(8,'B1010300000000B5','hex'), power: 'ON' }, //거실3--on
        {deviceId: 'Light', subId: '4', commandHex: Buffer.alloc(8,'3104000000000035','hex'), ackHex: Buffer.alloc(8,'B1000400000000B5','hex'), power: 'OFF'}, //거실4--off
        {deviceId: 'Light', subId: '4', commandHex: Buffer.alloc(8,'3104010000000036','hex'), ackHex: Buffer.alloc(8,'B1010400000000B6','hex'), power: 'ON' }, //거실4--on
        {deviceId: 'Light', subId: '5', commandHex: Buffer.alloc(8,'3105000000000036','hex'), ackHex: Buffer.alloc(8,'B1000500000000B6','hex'), power: 'OFF'}, //거실5--off
        {deviceId: 'Light', subId: '5', commandHex: Buffer.alloc(8,'3105010000000037','hex'), ackHex: Buffer.alloc(8,'B1010500000000B7','hex'), power: 'ON' }, //거실5--on

        {deviceId: 'BatchSwitch', subId: '1', commandHex: Buffer.alloc(8,'2201000100000024','hex'), ackHex: Buffer.alloc(8,'A2000100001500B8','hex'), power: 'OFF' }, //거실5--on
        {deviceId: 'BatchSwitch', subId: '1', commandHex: Buffer.alloc(8,'2201010100000025','hex'), ackHex: Buffer.alloc(8,'A2010100001500B9','hex'), power: 'ON' }, //거실5--on

		{deviceId: 'Power', subId: '1', commandHex: Buffer.alloc(8,'7A0101000000007C','hex'), ackHex: Buffer.alloc(8,'FA0001110000000C','hex'), power: 'OFF' }, //거실5--on
        {deviceId: 'Power', subId: '1', commandHex: Buffer.alloc(8,'7A0101010000007D','hex'), ackHex: Buffer.alloc(8,'FA0101110000000D','hex'), power: 'ON' }, //거실5--on

//        {deviceId: 'Ev', subId: '1', commandHex: Buffer.alloc(8,'200101000815003F','hex'), ackHex: Buffer.alloc(8,'220140070000006A','hex'), power: 'ON' }, //거실5--on

        {deviceId: 'Thermo', subId: '1', commandHex: Buffer.alloc(8,'040104810000008a','hex'), power: 'heat' }, // 온도조절기1-on
        {deviceId: 'Thermo', subId: '1', commandHex: Buffer.alloc(8,'0401040000000009','hex'), power: 'off'}, // 온도조절기1-off
        {deviceId: 'Thermo', subId: '2', commandHex: Buffer.alloc(8,'040204810000008b','hex'), power: 'heat' },
        {deviceId: 'Thermo', subId: '2', commandHex: Buffer.alloc(8,'040204000000000a','hex'), power: 'off'},
        {deviceId: 'Thermo', subId: '3', commandHex: Buffer.alloc(8,'040304810000008c','hex'), power: 'heat' },
        {deviceId: 'Thermo', subId: '3', commandHex: Buffer.alloc(8,'040304000000000b','hex'), power: 'off'},
        {deviceId: 'Thermo', subId: '4', commandHex: Buffer.alloc(8,'040404810000008d','hex'), power: 'heat' },
        {deviceId: 'Thermo', subId: '4', commandHex: Buffer.alloc(8,'040404000000000c','hex'), power: 'off'},
        {deviceId: 'Thermo', subId: '1', commandHex: Buffer.alloc(8,'040103FF000000FF','hex'), setTemp: ''}, // 온도조절기1-온도설정
        {deviceId: 'Thermo', subId: '2', commandHex: Buffer.alloc(8,'040203FF000000FF','hex'), setTemp: ''},
        {deviceId: 'Thermo', subId: '3', commandHex: Buffer.alloc(8,'040303FF000000FF','hex'), setTemp: ''}, 
        {deviceId: 'Thermo', subId: '4', commandHex: Buffer.alloc(8,'040403FF000000FF','hex'), setTemp: ''},

//        {deviceId: 'Fan', subId: '1', commandHex: Buffer.alloc(8,'780101000000007A','hex'), ackHex: Buffer.alloc(8,'F8000100000000F9','hex'), power: 'OFF' }, //꺼짐
//        {deviceId: 'Fan', subId: '1', commandHex: Buffer.alloc(8,'780101040000007E','hex'), ackHex: Buffer.alloc(8,'F8040101000000FE','hex'), power: 'ON'  }, //켜짐
//        {deviceId: 'Fan', subId: '1', commandHex: Buffer.alloc(8,'780102010000007C','hex'), ackHex: Buffer.alloc(8,'F8040101000000FE','hex'), speed: 'low'   }, //약(켜짐)
//        {deviceId: 'Fan', subId: '1', commandHex: Buffer.alloc(8,'780102020000007D','hex'), ackHex: Buffer.alloc(8,'F8040102000000FF','hex'), speed: 'medium'}, //중(켜짐)
//        {deviceId: 'Fan', subId: '1', commandHex: Buffer.alloc(8,'780102030000007E','hex'), ackHex: Buffer.alloc(8,'F804010300000000','hex'), speed: 'high'  }, //강(켜짐)

//        {deviceId: 'Gas', subId: '1', commandHex: Buffer.alloc(8,'1101800000000092','hex'), ackHex: Buffer.alloc(8,'9148480000000021','hex'), power: 'OFF' } //꺼짐
],

    // 상태 Topic (/homenet/${deviceId}${subId}/${property}/state/ = ${value})
    // 명령어 Topic (/homenet/${deviceId}${subId}/${property}/command/ = ${value})
    TOPIC_PRFIX: 'homenet',
    STATE_TOPIC: 'homenet/%s%s/%s/state', //상태 전달
    DEVICE_TOPIC: 'homenet/+/+/command' //명령 수신

};


// 로그 표시
var log = (...args) => console.log('[' + new Date().toLocaleString('ko-KR', {timeZone: 'Asia/Seoul'}) + ']', args.join(' '));

//////////////////////////////////////////////////////////////////////////////////////
// 홈컨트롤 상태
var homeStatus = {};
var lastReceive = new Date().getTime();
var mqttReady = false;
var queue = new Array();

//////////////////////////////////////////////////////////////////////////////////////
// MQTT-Broker 연결
const client  = mqtt.connect(CONST.mqttBroker, {clientId: CONST.clientID,
                                                username: CONST.mqttUser,
                                                password: CONST.mqttPass});
client.on('connect', () => {
    client.subscribe(CONST.DEVICE_TOPIC, (err) => {if (err) log('MQTT Subscribe fail! -', CONST.DEVICE_TOPIC) });
});

//-----------------------------------------------------------
// SerialPort 모듈 초기화
log('Initializing: SERIAL');    
const port = new SerialPort(CONST.portName, {
    baudRate: CONFIG.serial.baudrate,
    dataBits: 8,
    parity: CONFIG.serial.parity,
    stopBits: 1,
    autoOpen: false,
    encoding: 'hex'
});

port.on('open', () => log('Success open port:', CONST.portName));
port.open((err) => {
    if (err) {
        return log('Error opening port:', err.message);
    }
});

//////////////////////////////////////////////////////////////////////////////////////
// 홈넷에서 SerialPort로 상태 정보 수신
port.on('data', function (data) {
    //console.log('Receive interval: ', (new Date().getTime())-lastReceive, 'ms ->', data.toString('hex'));
    lastReceive = new Date().getTime();

    switch (data[0]) {
        case 0xb0: case 0xa0: case 0xf9:  //case 0x2d:// 조명, 환풍기, 가스밸브 상태 정보
        var objFound = CONST.DEVICE_STATE.find(obj => data.equals(obj.stateHex));
        if(objFound)
            updateStatus(objFound);
        break;
        case 0x82: // 온도조절기 상태 정보
            var objFound = CONST.DEVICE_STATE.find(obj => data.includes(obj.stateHex)); // 메시지 앞부분 매칭(온도부분 제외)
            if(objFound) {
                objFound.curTemp = data[3].toString(16); // 현재 온도
                objFound.setTemp = data[4].toString(16); // 설정 온도
                updateStatus(objFound);
            }
            break;
        // 제어 명령 Ack 메시지 : 조명, 환풍기, 가스밸브
        case 0xb1: case 0xa2: case 0xfa: //case 0x6a:
            // Ack 메시지를 받은 명령은 제어 성공하였으므로 큐에서 삭제
            var objFoundIdx = queue.findIndex(obj => obj.ackHex.includes(data));
            if(objFoundIdx > -1) {
                log('[Serial] Success command:', data.toString('hex'));
                queue.splice(objFoundIdx, 1);
            }
            break;
        // 제어 명령 Ack 메시지 : 난방
        case 0x84:
            // Ack 메시지를 받은 명령은 제어 성공하였으므로 큐에서 삭제
            let req = Buffer.alloc(8,'04FFFFFF000000FF','hex');
            req[1] = data[2];
            if ( data[1] == 0x81 ){ //켜기, 온도조절
                req[2] = 0x03; //온도조절
                req[3] = data[4];
                req[7] = req[0] + req[1] + req[2] + req[3];
                var objFoundIdx = queue.findIndex(obj => obj.commandHex.includes(req));
                if(objFoundIdx > -1) {
                    log('[Serial] Success command:', data.toString('hex'));
                    queue.splice(objFoundIdx, 1);
                } else {
                    req[2] = 0x04; //켜기
                    req[3] = 0x81;
                    req[7] = req[0] + req[1] + req[2] + req[3];
                    objFoundIdx = queue.findIndex(obj => obj.commandHex.includes(req));
                    if(objFoundIdx > -1) {
                        log('[Serial] Success command:', data.toString('hex'));
                        queue.splice(objFoundIdx, 1);
                    }
                }
            } else if ( data[1] == 0x84 ){ //끄기
                req[2] = 0x04;
                req[3] = 0x00;
                req[7] = req[0] + req[1] + req[2]
                var objFoundIdx = queue.findIndex(obj => obj.commandHex.includes(req));
                if(objFoundIdx > -1) {
                    log('[Serial] Success command:', data.toString('hex'));
                    queue.splice(objFoundIdx, 1);
                } else {
                    log('[req]', req.toString('hex'),  ' / [data]', data.toString('hex'));
                }
            }
            break;
        }

    });

//////////////////////////////////////////////////////////////////////////////////////
// MQTT로 HA에 상태값 전송

var updateStatus = (obj) => {
    var arrStateName = Object.keys(obj);
    // 상태값이 아닌 항목들은 제외 [deviceId, subId, stateHex, commandHex, ackHex, sentTime]
    const arrFilter = ['deviceId', 'subId', 'stateHex', 'commandHex', 'ackHex', 'sentTime'];
    arrStateName = arrStateName.filter(stateName => !arrFilter.includes(stateName));

    // 상태값별 현재 상태 파악하여 변경되었으면 상태 반영 (MQTT publish)
    arrStateName.forEach( function(stateName) {
        // 상태값이 없거나 상태가 같으면 반영 중지
        var curStatus = homeStatus[obj.deviceId+obj.subId+stateName];
        if(obj[stateName] == null || obj[stateName] === curStatus) return;
        // 미리 상태 반영한 device의 상태 원복 방지
        if(queue.length > 0) {
            var found = queue.find(q => q.deviceId+q.subId === obj.deviceId+obj.subId && q[stateName] === curStatus);
            if(found != null) return;
        }
        // 상태 반영 (MQTT publish)
        homeStatus[obj.deviceId+obj.subId+stateName] = obj[stateName];
        var topic = util.format(CONST.STATE_TOPIC, obj.deviceId, obj.subId, stateName);
        client.publish(topic, obj[stateName], {retain: true});
        log('[MQTT] Send to HA:', topic, '->', obj[stateName]);
    });
}

//////////////////////////////////////////////////////////////////////////////////////
// HA에서 MQTT로 제어 명령 수신
client.on('message', (topic, message) => {
    if(mqttReady) {
        var topics = topic.split('/');
        var value = message.toString(); // message buffer이므로 string으로 변환
        var objFound = null;

        if(topics[0] === CONST.TOPIC_PRFIX) {
            // 온도설정 명령의 경우 모든 온도를 Hex로 정의해두기에는 많으므로 온도에 따른 시리얼 통신 메시지 생성
            if(topics[2]==='setTemp') { //040X03FF000000FF
                objFound = CONST.DEVICE_COMMAND.find(obj => obj.deviceId+obj.subId === topics[1] && obj.hasOwnProperty('setTemp'));
                objFound.commandHex[3] = parseInt(value,16);
                objFound.setTemp = String(Number(value)); // 온도값은 소수점이하는 버림
                var checkSum = objFound.commandHex[0] + objFound.commandHex[1] + objFound.commandHex[2] + objFound.commandHex[3]
                objFound.commandHex[7] = checkSum; // 마지막 Byte는 CHECKSUM
            }
            // 다른 명령은 미리 정의해놓은 값을 매칭
            else {
                objFound = CONST.DEVICE_COMMAND.find(obj => obj.deviceId+obj.subId === topics[1] && obj[topics[2]] === value);
            }
        }

        if(objFound == null) {
            log('[MQTT] Receive Unknown Msg.: ', topic, ':', value);
            return;
        }

        // 현재 상태와 같으면 Skip
        if(value === homeStatus[objFound.deviceId+objFound.subId+objFound[topics[2]]]) {
            log('[MQTT] Receive & Skip: ', topic, ':', value);
        }
        // Serial메시지 제어명령 전송 & MQTT로 상태정보 전송
        else {
            log('[MQTT] Receive from HA:', topic, ':', value);
            // 최초 실행시 딜레이 없도록 sentTime을 현재시간 보다 sendDelay만큼 이전으로 설정
            objFound.sentTime = (new Date().getTime())-CONST.sendDelay;
            queue.push(objFound);   // 실행 큐에 저장
            updateStatus(objFound); // 처리시간의 Delay때문에 미리 상태 반영
        }
    }
});

//////////////////////////////////////////////////////////////////////////////////////
// SerialPort로 제어 명령 전송

const commandProc = () => {
    // 큐에 처리할 메시지가 없으면 종료
    if(queue.length == 0) return;

    // 기존 홈넷 RS485 메시지와 충돌하지 않도록 Delay를 줌
    var delay = (new Date().getTime())-lastReceive;
    if(delay < CONST.sendDelay) return;

    // 큐에서 제어 메시지 가져오기
    var obj = queue.shift();
    port.write(obj.commandHex, (err) => {if(err)  return log('[Serial] Send Error: ', err.message); });
    lastReceive = new Date().getTime();
    obj.sentTime = lastReceive;     // 명령 전송시간 sentTime으로 저장
    log('[Serial] Send to Device:', obj.deviceId, obj.subId, '->', obj.state, '('+delay+'ms) ', obj.commandHex.toString('hex'));

    // 다시 큐에 저장하여 Ack 메시지 받을때까지 반복 실행
    queue.push(obj);
};

setTimeout(() => {mqttReady=true; log('MQTT Ready...')}, CONST.mqttDelay);
setInterval(commandProc, 20);

