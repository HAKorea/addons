# Universal Wallpad Controller with RS485 

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armhf Architecture][armhf-shield] ![Supports armv7 Architecture][armv7-shield] ![Supports i386 Architecture][i386-shield]

## About
그레고리 하우스님이 만든 nodejs 월패드 프로그램을 애드온으로 만든 것입니다.
기본은 코콤으로 동작합니다만 커스텀으로 js 파일을 변경하시면 삼성, 대림 등 다른 아파트 월패드를 동작시킬 수 있는 nodejs 서버입니다. 

## Version : 0.3

## Installation

1. 홈어시스턴트의 Hass.io > ADD-ON STORE에서 Add new repository by URL에 https://github.com/HAKorea/addons 를 입력한 다음 ADD 버튼을 누릅니다.
2. ADD-ON STORE 페이지 하단에서 "Universal Wallpad Controller with RS485" 클릭합니다.
3. "INSTALL" 버튼을 누르면 애드온이 설치됩니다. 최대 약 10분 정도 소요. 
4. INSTALL 버튼위에 설치 애니메이션이 동작하는데 이것이 멈추더라도 REBUILD, START 버튼이 나타나지 않는 경우가 있습니다.
5. 이 애드온은 이미지를 내려받는 것이 아니라 직접 여러분의 Hassio에서 이미지를 만듭니다. 따라서 컴퓨터성능과 인터넷 속도에 따라서 시간이 좀 걸립니다. 
6. INSTALL 버튼을 누른다음 설치 애니메이션이 실행되면 제대로 설치중인 것입니다. INSTALL을 여러번 누르지 마시고 기다리다 지치면 브라우저 페이지를 리프리시 하세요. 
7. 애드온 페이지에서 Config을 본인의 환경에 맞게 수정합니다.
8. "START" 버튼으로 애드온을 실행합니다.

애드온을 최초 실행하면 share/wallpad.js 파일이 생성됩니다. 만일 wallpad.js 파일은 본인의 월패드에 맞게 수정하셔도 됩니다. 수정한 후 애드온을 재실행하면 수정한 js 파일로 실행됩니다. 



## Configuration

Add-on configuration:

```json
{
    "serial":{
      "port": "/dev/ttyUSB0",
      "baudrate": 9600,
      "parity" : "none",
      "senddelay": 150
    },
    "mqtt": {
      "server": "192.168.x.x",
      "username": "id",
      "password": "pw",
      "receivedelay": 10000
    }
}
```

### Option: `serial` (required)

* "port": "/dev/ttyUSB0" 	// 시리얼포트명
* "baudrate": 9600 		// 시리얼 통신 속도
* "parity" : "none"		// 패리티 체크 (none, even, odd 중 한 값)
* "senddelay": 150		// 전송 딜레이 1/1000초 단위

### Option `MQTT` (required)

* "server": "192.168.x.xx"	// MQTT 서버
* "username": "id"			// MQTT ID
* "password": "pw"			// MQTT PW
* "receivedelay": 10000		// 전송후 메시지 수신 지연 시간 1/1000초 단위


### Option: `customefile` (optional)

"customfile": "mygateway.js" 와 같이 설정하고
share/mygateway.js 파일을 넣어두면 모든 설정을 무시하고 해당 파일로 nodejs를 실행함
로그창에 Initializing mygateway.js... 과 같이 이름이 표시됨
```json
{ 
	//- 중략 -

	"mqtt": {
		
	//- 중략 -

      "receivedelay": 10000
    },
    "customfile": "mygateway.js"
}
```
### JS 파일의 수정
본인이 사용중인 월패드용 js 파일이 있다면 해당 파일을 그대로 쓰셔도 됩니다. 다만 customfile 옵션에 파일명을 작성하지 않으면 기본 파일은 share/wallpad.js 입니다. 

애드온의 옵션을 월패드 js에서 사용하려면 다음과 같습니다.
```js
const CONFIG = require('/data/options.json');  //**** 애드온의 옵션을 불러옵니다. 옵션 파일의 위치는 변경 불가합니다. 
// 이후 CONFIG.mqtt.username 과 같이 사용가능합니다. 
// 사용가능한 옵션
CONFIG.serial.port
CONFIG.serial.baudrate
CONFIG.serial.parity
CONFIG.serial.senddelay
CONFIG.mqtt.server
CONFIG.mqtt.username
CONFIG.mqtt.password
CONFIG.mqtt.receivedelay

//------------ 적용 예시 ------------
const CONST = {
    // 포트이름 설정
    portName: process.platform.startsWith('win') ? "COM6" : CONFIG.serial.port, 
    sendDelay: CONFIG.serial.senddelay,
    mqttBroker: 'mqtt://'+CONFIG.mqtt.server, 
    mqttDelay: CONFIG.mqtt.receivedelay,
    mqttUser: CONFIG.mqtt.username, 
    mqttPass: CONFIG.mqtt.password, 
//------------ 적용 예시 ------------
}
```

## Support

Got questions?

You have several options to get them answered:

- The [Korean Community Addons Github][github].
- The [Home Assistant 네이버카페][forum].

버그신고는 카페나 깃허브로 해주세요 [open an issue on our GitHub][issue].


[forum]: https://cafe.naver.com/koreassistant
[github]: https://github.com/HAKorea/addons
[issue]: https://github.com/zooil/commaxRS485/issues
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg

