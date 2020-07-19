/**
 * Y-City Home Controller
 * @author Daehwan, Kang
 * @since 2018-09-18
 */

const util = require('util');
const SerialPort = require('serialport');
const net = require('net');   // Socket
const Delimiter = require('@serialport/parser-delimiter')
const mqtt = require('mqtt');

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
  DEVICE: [
    {deviceId: 'Ventilator', subId: ''   , state: 'OFF', st: 'off', name: '환풍기'   , stateHex: new Buffer([0xf7, 0x0c, 0x01, 0x2b, 0x04, 0x40, 0x11, 0x00, 0x02, 0x00, 0x86]), commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x2b, 0x02, 0x40, 0x11, 0x02, 0x00, 0x87, 0xee])}, //꺼짐
    {deviceId: 'Ventilator', subId: ''   , state: 'ON' , st: 'on' , name: '환풍기'   , stateHex: new Buffer([0xf7, 0x0c, 0x01, 0x2b, 0x04, 0x40, 0x11, 0x00, 0x01, 0x07, 0x82]), commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x2b, 0x02, 0x40, 0x11, 0x01, 0x00, 0x84, 0xee])}, //켜짐(강)
    {deviceId: 'Ventilator', subId: ''   , state: 'ON2', st: 'on' , name: '환풍기'   , stateHex: new Buffer([0xf7, 0x0c, 0x01, 0x2b, 0x04, 0x40, 0x11, 0x00, 0x01, 0x03, 0x86]), commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x2b, 0x02, 0x42, 0x11, 0x03, 0x00, 0x84, 0xee])}, //켜짐(중)
    {deviceId: 'Ventilator', subId: ''   , state: 'ON3', st: 'on' , name: '환풍기'   , stateHex: new Buffer([0xf7, 0x0c, 0x01, 0x2b, 0x04, 0x40, 0x11, 0x00, 0x01, 0x01, 0x84]), commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x2b, 0x02, 0x42, 0x11, 0x01, 0x00, 0x86, 0xee])}, //켜짐(약)
    {deviceId: 'Light'     , subId: '1-1', state: 'OFF', st: 'off', name: '거실전등1', stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x11, 0x00, 0x02, 0xb3])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x11, 0x02, 0x00, 0xb5, 0xee])}, //거실1--off
    {deviceId: 'Light'     , subId: '1-1', state: 'ON' , st: 'on' , name: '거실전등1', stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x11, 0x00, 0x01, 0xb0])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x11, 0x01, 0x00, 0xb6, 0xee])}, //거실1--on
    {deviceId: 'Light'     , subId: '1-2', state: 'OFF', st: 'off', name: '거실전등2', stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x12, 0x00, 0x02, 0xb0])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x12, 0x02, 0x00, 0xb6, 0xee])}, //거실2--off
    {deviceId: 'Light'     , subId: '1-2', state: 'ON' , st: 'on' , name: '거실전등2', stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x12, 0x00, 0x01, 0xb3])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x12, 0x01, 0x00, 0xb5, 0xee])}, //거실2--on
    {deviceId: 'Light'     , subId: '1-3', state: 'OFF', st: 'off', name: '통로등'   , stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x13, 0x00, 0x02, 0xb1])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x13, 0x02, 0x00, 0xb7, 0xee])}, //통로등--off
    {deviceId: 'Light'     , subId: '1-3', state: 'ON' , st: 'on' , name: '통로등'   , stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x13, 0x00, 0x01, 0xb2])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x13, 0x01, 0x00, 0xb4, 0xee])}, //통로등--on
    {deviceId: 'Light'     , subId: '1-4', state: 'OFF', st: 'off', name: '비상조명' , stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x14, 0x00, 0x02, 0xb6])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x14, 0x02, 0x00, 0xb0, 0xee])}, //비상조명--off
    {deviceId: 'Light'     , subId: '1-4', state: 'ON' , st: 'on' , name: '비상조명' , stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x14, 0x00, 0x01, 0xb5])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x14, 0x01, 0x00, 0xb3, 0xee])}, //비상조명--on
    {deviceId: 'Light'     , subId: '2-1', state: 'OFF', st: 'off', name: '안방전등1', stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x21, 0x00, 0x02, 0x83])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x21, 0x02, 0x00, 0x85, 0xee])}, //전등1--off
    {deviceId: 'Light'     , subId: '2-1', state: 'ON' , st: 'on' , name: '안방전등1', stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x21, 0x00, 0x01, 0x80])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x21, 0x01, 0x00, 0x86, 0xee])}, //전등1--on
    {deviceId: 'Light'     , subId: '2-2', state: 'OFF', st: 'off', name: '안방전등2', stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x22, 0x00, 0x02, 0x80])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x22, 0x02, 0x00, 0x86, 0xee])}, //전등2--off
    {deviceId: 'Light'     , subId: '2-2', state: 'ON' , st: 'on' , name: '안방전등2', stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x22, 0x00, 0x01, 0x83])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x22, 0x01, 0x00, 0x85, 0xee])}, //전등2--on
    {deviceId: 'Light'     , subId: '2-3', state: 'OFF', st: 'off', name: '발코니'   , stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x23, 0x00, 0x02, 0x81])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x23, 0x02, 0x00, 0x87, 0xee])}, //발코니--off
    {deviceId: 'Light'     , subId: '2-3', state: 'ON' , st: 'on' , name: '발코니'   , stateHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x04, 0x40, 0x23, 0x00, 0x01, 0x82])      , commandHex: new Buffer([0xf7, 0x0b, 0x01, 0x19, 0x02, 0x40, 0x23, 0x01, 0x00, 0x84, 0xee])}  //발코니--on
  ],


  // 상태 Prefix 상수
  STATE_PREFIX: ['f70c012b', 'f70b0119'],

  // 상태 Topic (/homenet/${deviceId}${subId}/${property}/state/ = ${value})
  // 명령어 Topic (/homenet/${deviceId}${subId}/${property}/command/ = ${value})
  TOPIC_PRFIX: 'homenet',
  STATE_TOPIC: 'homenet/%s%s/%s/state', //상태 전달
  DEVICE_TOPIC: 'homenet/+/+/command' //명령 수신

};
var log = (...args) => console.log('[' + new Date().toLocaleString('ko-KR', {timeZone: 'Asia/Seoul'}) + ']', args.join(' '));


///////////////////////////////////////////
// 홈컨트롤 상태
var homeStatus = {};
var lastReceive = new Date().getTime();
var mqttReady = false;
var queue = new Array();
///////////////////////////////////////////

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
const parser = port.pipe(new Delimiter({ delimiter: new Buffer([0xee]) }))
port.on('open', () => log('Success open port:', CONST.portName));
port.open((err) => {
  if (err) {
    return log('Error opening port:', err.message);
  }
});

//////////////////////////////////////////////////////////////////////////////////////


// SerialPort에서 데이터 수신
parser.on('data', buffer => {
  //console.log('Receive interval: ', (new Date().getTime())-lastReceive, 'ms ->', buffer);
  lastReceive = new Date().getTime();
  
  if(CONST.STATE_PREFIX.includes(buffer.toString('hex',0,4))) {
    var objFound = CONST.DEVICE.find(obj => buffer.equals(obj.stateHex));
    if(objFound) updateStatus(objFound);
  }
});



// MQTT 수신
client.on('message', (topic, message) => {
  if(mqttReady) {
    var topics = topic.split('/');
    var msg = message.toString(); // message is Buffer
    var objFound = null;
    if(topics[0] === CONST.TOPIC_PRFIX) {
      objFound = CONST.DEVICE.find(obj => topics[1] === obj.deviceId+obj.subId && msg === obj.state);
    }
    else if(topics[0] === CONST.ST_TOPIC_PREFIX) { // SmartThings
      objFound = CONST.DEVICE.find(obj => topics[1] === obj.name && msg === obj.st);
    }

    if(objFound == null) {
      log('MQTT Message Unknow=>', topic, ':', msg);
      return;
    }

    if(objFound.state === homeStatus[objFound.deviceId+objFound.subId]) {
      log('MQTT Message Skip=>', topic, ':', msg);
    }
    else {
      log('MQTT Message=>', topic, ':', msg);
      //commandProc(objFound);
      queue.push(objFound);
      updateStatus(objFound); // 처리시간의 Delay때문에 미리 상태 반영
    }

    
  }
})


//////////////////////////////////
// 상태값 업데이트 (MQTT로 전송)
//////////////////////////////////
var updateStatus = obj => {
  var current = homeStatus[obj.deviceId+obj.subId];
  // 상태가 변경되면 publish
  if(current == null || current != obj.state) {
    // 미리 상태 반영한 device의 상태 원복 방지
    if(queue.length > 0) {
      var found = queue.find(q => q.deviceId+q.subId === obj.deviceId+obj.subId && q.state === current);
      if(found != null) return;
    }
    // 그외 상태반영
    homeStatus[obj.deviceId+obj.subId] = obj.state;
    
    var topic = util.format(CONST.STATE_TOPIC, obj.deviceId, obj.subId);
    var st_topic = util.format(CONST.ST_STATE_TOPIC, obj.name);
    if(obj.deviceId === 'Ventilator') {
      var msg = util.format('{"power":"%s","speed":"%s"}', obj.state.startsWith("ON") ? "ON" : obj.state, obj.state)
      client.publish(topic, msg, {retain: true}); // HomeAssistant
      client.publish(st_topic, obj.st, {retain: true}); // SmartThings
      log('Status update:', topic, '->', msg);
      log('Status update:', st_topic, '->', obj.st);
    }
    else {
      client.publish(topic, obj.state, {retain: true}); // HomeAssistant
      client.publish(st_topic, obj.st, {retain: true}); // SmartThings
      log('Status update:', topic, '->', obj.state);
      log('Status update:', st_topic, '->', obj.st);
    }
  }
}


//////////////////////////////////
// 수신명령 처리 (MQTT에서 수신)
//////////////////////////////////
const commandProc = () => {
  if(queue.length == 0) return;

  // RS485는 전체 Device가 동일한 메시지를 수신하므로 일정시간 Delay를 줌
  var delay = (new Date().getTime())-lastReceive;
  if(delay < CONST.sendDelay) return;

  // 큐에 쌓인 메시지 처리
  var obj = queue.shift();
  port.write(obj.commandHex, (err) => {if(err)  return log('SerialPort Send Error: ', err.message); });
  lastReceive = new Date().getTime();

  log('SerialPort Send:', obj.name, '->', obj.state, '('+delay+'ms)');
}



setTimeout(() => {mqttReady=true; log('MQTT Ready...')}, CONST.mqttDelay);
setInterval(commandProc, 20);
