/**
 * RS485 Homegateway for Samsung Homenet
 * @소스 공개 : Daehwan, Kang
 * @삼성 홈넷용으로 수정 : erita
 * @수정일 2019-01-11
 */
 
const util = require('util');
const SerialPort = require('serialport');
const net = require('net');		// Socket
const mqtt = require('mqtt');

const CONFIG = require('/data/options.json');  //**** 애드온의 옵션을 불러옵니다. 이후 CONFIG.mqtt.username 과 같이 사용가능합니다. 

// 커스텀 파서
var Transform = require('stream').Transform;
util.inherits(CustomParser, Transform);

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

    aswDelay: 1000,
  	// 메시지 Prefix 상수
  	MSG_PREFIX: [0xb0, 0xac, 0xae, 0xc2, 0xad, 0xab],

  // 기기별 상태 및 제어 코드(HEX)
   DEVICE_STATE: [
    {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b079310078','hex'), power1: 'OFF', power2: 'OFF', power3: 'OFF', power4: 'OFF', power5: 'OFF', power6: 'OFF'}, //상태-00
    {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b079310179','hex'), power1: 'ON' , power2: 'OFF', power3: 'OFF', power4: 'OFF', power5: 'OFF', power6: 'OFF'}, //상태-01
    {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b07931027a','hex'), power1: 'OFF', power2: 'ON' , power3: 'OFF', power4: 'OFF', power5: 'OFF', power6: 'OFF'}, //상태-02
    {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b07931037b','hex'), power1: 'ON' , power2: 'ON' , power3: 'OFF', power4: 'OFF', power5: 'OFF', power6: 'OFF'}, //상태-03
    {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b07931047c','hex'), power1: 'OFF', power2: 'OFF', power3: 'ON', power4: 'OFF', power5: 'OFF', power6: 'OFF' }, //상태-04
    {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b07931057d','hex'), power1: 'ON' , power2: 'OFF', power3: 'ON', power4: 'OFF', power5: 'OFF', power6: 'OFF' }, //상태-05
    {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b07931067e','hex'), power1: 'OFF', power2: 'ON' , power3: 'ON', power4: 'OFF', power5: 'OFF', power6: 'OFF' }, //상태-06
    {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b07931077f','hex'), power1: 'ON' , power2: 'ON' , power3: 'ON', power4: 'OFF', power5: 'OFF', power6: 'OFF' }, //상태-07
	{deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b079310870','hex'), power1: 'OFF', power2: 'OFF' , power3: 'OFF', power4: 'ON', power5: 'OFF', power6: 'OFF'}, //상태-08
	{deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b079311088','hex'), power1: 'OFF', power2: 'OFF' , power3: 'OFF', power4: 'OFF', power5: 'ON', power6: 'OFF'}, //상태-09
    {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b079312058','hex'), power1: 'OFF', power2: 'OFF' , power3: 'OFF', power4: 'OFF', power5: 'OFF', power6: 'ON'}, //상태-10
	{deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b079311880','hex'), power1: 'OFF', power2: 'OFF' , power3: 'OFF', power4: 'ON', power5: 'ON', power6: 'OFF'}, //상태-11
	{deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b079312850','hex'), power1: 'OFF', power2: 'OFF' , power3: 'OFF', power4: 'ON', power5: 'OFF', power6: 'ON'}, //상태-12
	{deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b079313068','hex'), power1: 'OFF', power2: 'OFF' , power3: 'OFF', power4: 'OFF', power5: 'ON', power6: 'ON'}, //상태-13
	//{deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b07c04000a','hex'), power1: 'ON', power2: 'OFF' , power3: 'OFF', power4: 'OFF', power5: 'OFF', power6: 'ON'}, //상태-08
  //  {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b07c03000a','hex'), power1: 'OFF', power2: 'ON' , power3: 'OFF', power4: 'OFF', power5: 'OFF', power6: 'ON'}, //상태-08
 //   {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b07931240c','hex'), power1: 'OFF', power2: 'OFF' , power3: 'ON', power4: 'OFF', power5: 'OFF', power6: 'ON'}, //상태-08
  //  {deviceId: 'Light', subId: '1', stateHex: Buffer.alloc(5,'b079413f17','hex'), power1: 'ON', power2: 'ON' , power3: 'ON', power4: 'ON', power5: 'ON', power6: 'ON'}, //상태-08 거실 6개 조명 상태 다넣는건 포기..그냥 작동은 됨..
 	{deviceId: 'Fan', subId: '1', stateHex: Buffer.alloc(6,'b04e0300017c','hex'), power: 'OFF', speed: 'low' },
    {deviceId: 'Fan', subId: '1', stateHex: Buffer.alloc(6,'b04e0200007c','hex'), power: 'ON' , speed: 'mid' },
    {deviceId: 'Fan', subId: '1', stateHex: Buffer.alloc(6,'b04e0100007f','hex'), power: 'ON' , speed: 'high'},
    {deviceId: 'Thermo', subId: '1', stateHex: Buffer.alloc(4,'b07c0101','hex'), power: 'heat' , setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '1', stateHex: Buffer.alloc(4,'b07c0100','hex'), power: 'off', setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '2', stateHex: Buffer.alloc(4,'b07c0201','hex'), power: 'heat' , setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '2', stateHex: Buffer.alloc(4,'b07c0200','hex'), power: 'off', setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '3', stateHex: Buffer.alloc(4,'b07c0301','hex'), power: 'heat' , setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '3', stateHex: Buffer.alloc(4,'b07c0300','hex'), power: 'off', setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '4', stateHex: Buffer.alloc(4,'b07c0401','hex'), power: 'heat' , setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '4', stateHex: Buffer.alloc(4,'b07c0400','hex'), power: 'off', setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '5', stateHex: Buffer.alloc(4,'b07c0501','hex'), power: 'heat' , setTemp: '', curTemp: ''},
    {deviceId: 'Thermo', subId: '5', stateHex: Buffer.alloc(4,'b07c0500','hex'), power: 'off', setTemp: '', curTemp: ''},
	{deviceId: 'light', subId: '1', stateHex: Buffer.alloc(4,'ad540178','hex'), alllight: 'OFF'}, //일괄소등 off
    {deviceId: 'light', subId: '1', stateHex: Buffer.alloc(4,'ad540079','hex'), alllight: 'ON'}, //일괄소등 on
  ],

  DEVICE_COMMAND: [
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a010057','hex'), power1: 'OFF'}, //거실1--off
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a010156','hex'), power1: 'ON' }, //거실1--on
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a020054','hex'), power2: 'OFF'}, //거실2--off
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a020155','hex'), power2: 'ON' }, //거실2--on
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a030055','hex'), power3: 'OFF'}, //거실3--off
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a030154','hex'), power3: 'ON' }, //거실3--on
	{deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a040052','hex'), power4: 'OFF'}, //거실4--off
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a040153','hex'), power4: 'ON' }, //거실4--on
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a050053','hex'), power5: 'OFF'}, //거실5--off
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a050152','hex'), power5: 'ON' }, //거실5--on
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a060050','hex'), power6: 'OFF'}, //거실6--off
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a050151','hex'), power6: 'ON' }, //거실6--on
	{deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a070051','hex'), power7: 'OFF'}, //거실7--off
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a070150','hex'), power7: 'ON' }, //거실7--on
	{deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a08005e','hex'), power8: 'OFF'}, //거실8--off
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a08015f','hex'), power8: 'ON' }, //거실8--on
	{deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a08005e','hex'), power9: 'OFF'}, //거실9--off
    {deviceId: 'Light', subId: '1', commandHex: Buffer.alloc(5,'ac7a09015e','hex'), power9: 'ON' }, //거실9--on
	{deviceId: 'Fan', subId: '1', commandHex: Buffer.alloc(6, 'c24f05000008','hex'), power: 'ON'    }, //켜짐
    {deviceId: 'Fan', subId: '1', commandHex: Buffer.alloc(6, 'c24f0600000b','hex'), power: 'OFF'   }, //꺼짐
    {deviceId: 'Fan', subId: '1', commandHex: Buffer.alloc(6, 'c24f0300000e','hex'), speed: 'low'   }, //약(켜짐)
    {deviceId: 'Fan', subId: '1', commandHex: Buffer.alloc(6, 'c24f0200000f','hex'), speed: 'medium'}, //중(켜짐)
    {deviceId: 'Fan', subId: '1', commandHex: Buffer.alloc(6, 'c24f0100000c','hex'), speed: 'high'  }, //강(켜짐)
    {deviceId: 'Thermo', subId: '1', commandHex: Buffer.alloc(8, 'ae7d010100000053','hex'), power: 'heat' }, // 온도조절기1-on
    {deviceId: 'Thermo', subId: '1', commandHex: Buffer.alloc(8, 'ae7d010000000052','hex'), power: 'off'}, // 온도조절기1-off
    {deviceId: 'Thermo', subId: '2', commandHex: Buffer.alloc(8, 'ae7d020100000050','hex'), power: 'heat' },
    {deviceId: 'Thermo', subId: '2', commandHex: Buffer.alloc(8, 'ae7d020000000051','hex'), power: 'off'},
    {deviceId: 'Thermo', subId: '3', commandHex: Buffer.alloc(8, 'ae7d030100000051','hex'), power: 'heat' },
    {deviceId: 'Thermo', subId: '3', commandHex: Buffer.alloc(8, 'ae7d030000000050','hex'), power: 'off'},
    {deviceId: 'Thermo', subId: '4', commandHex: Buffer.alloc(8, 'ae7d040100000056','hex'), power: 'heat' },
    {deviceId: 'Thermo', subId: '4', commandHex: Buffer.alloc(8, 'ae7d040000000057','hex'), power: 'off'},
    {deviceId: 'Thermo', subId: '5', commandHex: Buffer.alloc(8, 'ae7d050100000057','hex'), power: 'heat' },
    {deviceId: 'Thermo', subId: '5', commandHex: Buffer.alloc(8, 'ae7d050000000056','hex'), power: 'off'},
    {deviceId: 'Thermo', subId: '1', commandHex: Buffer.alloc(8, 'ae7f01FF000000FF','hex'), setTemp: ''}, // 온도조절기1-온도설정
    {deviceId: 'Thermo', subId: '2', commandHex: Buffer.alloc(8, 'ae7f02FF000000FF','hex'), setTemp: ''},
    {deviceId: 'Thermo', subId: '3', commandHex: Buffer.alloc(8, 'ae7f03FF000000FF','hex'), setTemp: ''},
    {deviceId: 'Thermo', subId: '4', commandHex: Buffer.alloc(8, 'ae7f04FF000000FF','hex'), setTemp: ''},
    {deviceId: 'Thermo', subId: '5', commandHex: Buffer.alloc(8, 'ae7f05FF000000FF','hex'), setTemp: ''},
	{deviceId: 'light', subId: '1', commandHex: Buffer.alloc(4,'ad53007e','hex'), alllight: 'OFF'}, //일괄소등 off
	{deviceId: 'light', subId: '1', commandHex: Buffer.alloc(4,'ad53017f','hex'), alllight: 'ON'}, //일광소등 on
  ],
  
  // 상태 Topic (/homenet/${deviceId}${subId}/${property}/state/ = ${value})
  // 명령어 Topic (/homenet/${deviceId}${subId}/${property}/command/ = ${value})
  TOPIC_PRFIX: 'homenet',
  STATE_TOPIC: 'homenet/%s%s/%s/state', //상태 전달
  DEVICE_TOPIC: 'homenet/+/+/command' //명령 수신

};


//////////////////////////////////////////////////////////////////////////////////////
// 삼성 홈넷용 시리얼 통신 파서 : 메시지 길이나 구분자가 불규칙하여 별도 파서 정의
function CustomParser(options) {
	if (!(this instanceof CustomParser))
		return new CustomParser(options);
	Transform.call(this, options);
	this._queueChunk = [];
	this._msgLenCount = 0;
	this._msgLength = 8;
	this._msgTypeFlag = false;
}

CustomParser.prototype._transform = function(chunk, encoding, done) {
	var start = 0;
	for (var i = 0; i < chunk.length; i++) {
		if(CONST.MSG_PREFIX.includes(chunk[i])) {			// 청크에 구분자(MSG_PREFIX)가 있으면
			this._queueChunk.push( chunk.slice(start, i) );	// 구분자 앞부분을 큐에 저장하고
			this.push( Buffer.concat(this._queueChunk) );	// 큐에 저장된 메시지들 합쳐서 내보냄
			this._queueChunk = [];	// 큐 초기화
			this._msgLenCount = 0;
			start = i;
			this._msgTypeFlag = true;	// 다음 바이트는 메시지 종류
		} 
		// 메시지 종류에 따른 메시지 길이 파악
		else if(this._msgTypeFlag) {
			switch (chunk[i]) {
				case 0x41: case 0x52: case 0x53: case 0x54: case 0x55: case 0x56: case 0x78: case 0x2f: case 0x41:
					this._msgLength = 4;	break;
				case 0x79: case 0x7A:
					this._msgLength = 5;	break;
				case 0x4e: case 0x4f:
					this._msgLength = 6;	break;
				default:
					this._msgLength = 8;
			}
			this._msgTypeFlag = false;
		}
		this._msgLenCount++;
	}
	// 구분자가 없거나 구분자 뒷부분 남은 메시지 큐에 저장
	this._queueChunk.push(chunk.slice(start));
	
	// 메시지 길이를 확인하여 다 받았으면 내보냄
	if(this._msgLenCount >= this._msgLength) {
		this.push( Buffer.concat(this._queueChunk) );	// 큐에 저장된 메시지들 합쳐서 내보냄
		this._queueChunk = [];	// 큐 초기화
		this._msgLenCount = 0;
	}
	
	done();
};
//////////////////////////////////////////////////////////////////////////////////////


// 로그 표시 
var log = (...args) => console.log('[' + new Date().toLocaleString('ko-KR', {timeZone: 'Asia/Seoul'}) + ']', args.join(' '));

//////////////////////////////////////////////////////////////////////////////////////
// 홈컨트롤 상태
var homeStatus = {};
var lastReceive = new Date().getTime();
var mqttReady = false;
var queue = new Array();
var queueSent = new Array();

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

const parser = port.pipe(new CustomParser());

port.on('open', () => log('[Serial] Success open port:', CONST.portName));
port.open((err) => {
	if (err) {
		return log('Error opening port:', err.message);
	}
});


//////////////////////////////////////////////////////////////////////////////////////
// 홈넷에서 SerialPort로 상태 정보 수신
parser.on('data', function (data) {
	// console.log('Receive interval: ', (new Date().getTime())-lastReceive, 'ms ->', data.toString('hex'));
	lastReceive = new Date().getTime();
	
	// 첫번째 바이트가 'b0'이면 응답 메시지
	if(data[0] == 0xad ) {
	switch (data[1]) {
		case 0x56: 	// 가스, ev 상태 정보
			var objFound = CONST.DEVICE_STATE.find(obj => data.equals(obj.stateHex));
			if(objFound)
				updateStatus(objFound);
			break;
		 case 0x2f:
		 	// Ack 메시지를 받은 명령은 제어 성공하였으므로 큐에서 삭제
			const ack1 = Buffer.alloc(1);
			data.copy(ack1, 0, 1, 2);
			var objFoundIdx = queue.findIndex(obj => obj.commandHex.includes(ack1));
			if(objFoundIdx > -1) {
				log('[Serial] Success command:', data.toString('hex'));
				queue.splice(objFoundIdx, 1);
			}
			break;
	}}
	if(data[0] != 0xb0 )	return;
	switch (data[1]) {
		case 0x79: case 0x4e: case 0x56: case 0x41:	// 조명,환풍기,상태 정보
			var objFound = CONST.DEVICE_STATE.find(obj => data.equals(obj.stateHex));
			if(objFound)
				updateStatus(objFound);
			break;
		case 0x7c: 	// 온도조절기 상태 정보
			var objFound = CONST.DEVICE_STATE.find(obj => data.includes(obj.stateHex));	// 메시지 앞부분 매칭(온도부분 제외)
			if(objFound && data.length===8) {		// 메시지 길이 확인
				objFound.setTemp = data[4].toString();		// 설정 온도
				objFound.curTemp = data[5].toString();		// 현재 온도
				updateStatus(objFound);
			}
			break;
		// 제어 명령 Ack 메시지 : 조명, 난방, 난방온도, 환풍기
		case 0x7a: case 0x7d: case 0x7f: case 0x4f: case 0x78:
			// Ack 메시지를 받은 명령은 제어 성공하였으므로 큐에서 삭제
			const ack2 = Buffer.alloc(2);
			data.copy(ack2, 0, 1, 3);
			var objFoundIdx = queue.findIndex(obj => obj.commandHex.includes(ack2));
			if(objFoundIdx > -1) {
				log('[Serial] Success command:', data.toString('hex'));
				queue.splice(objFoundIdx, 1);
			}
			break;		
	}
	
});

//////////////////////////////////////////////////////////////////////////////////////
// MQTT로 HA에 상태값 전송

var updateStatus = (obj) => {
	var arrStateName = Object.keys(obj);
	// 상태값이 아닌 항목들은 제외 [deviceId, subId, stateHex, commandHex, sentTime]
	const arrFilter = ['deviceId', 'subId', 'stateHex', 'commandHex', 'sentTime'];
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
		var objFound1 = null;
		if(topics[0] === CONST.TOPIC_PRFIX) {
			// 온도설정 명령의 경우 모든 온도를 Hex로 정의해두기에는 많으므로 온도에 따른 시리얼 통신 메시지 생성
			if(topics[2]==='setTemp') {
				objFound = CONST.DEVICE_COMMAND.find(obj => obj.deviceId+obj.subId === topics[1] && obj.hasOwnProperty('setTemp'));
				objFound.commandHex[3] = Number(value);
				objFound.setTemp = String(Number(value)); // 온도값은 소수점이하는 버림
				var xorSum = objFound.commandHex[0] ^ objFound.commandHex[1] ^ objFound.commandHex[2] ^ objFound.commandHex[3] ^ 0x80
				objFound.commandHex[7] = xorSum; // 마지막 Byte는 XOR SUM
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
			queue.push(objFound);	// 실행 큐에 저장
			updateStatus(objFound); // 처리시간의 Delay때문에 미리 상태 반영
		}
	}
})

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
	if(CONFIG.type == 'socket'){
		sock.write(obj.commandHex, (err) => {if(err)  return log('[Socket] Send Error: ', err.message); });  // Socket
	}
	else{
		port.write(obj.commandHex, (err) => {if(err)  return log('[Serial] Send Error: ', err.message); });
	}
	lastReceive = new Date().getTime();
	obj.sentTime = lastReceive;	// 명령 전송시간 sentTime으로 저장
	log('Send to Device:', obj.deviceId, obj.subId, '->', obj.state, '('+delay+'ms) ', obj.commandHex.toString('hex'));
	
	// 다시 큐에 저장하여 Ack 메시지 받을때까지 반복 실행  // 일괄소등(Light) 아니면 // 일괄소등이면 조명1상태 읽기
	if((obj.deviceId == 'Light') && (obj.subId == '')){
		allSWSend = new Date().getTime();
		allsw_flag = true;
	}
	else{
		//queue.push(obj);
	}
}

setTimeout(() => {mqttReady=true; log('MQTT Ready...')}, CONST.mqttDelay);
setInterval(commandProc, 20);
