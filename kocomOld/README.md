# Hass.io Add-on: Kocom Wallpad Controller with RS485 

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armhf Architecture][armhf-shield] ![Supports armv7 Architecture][armv7-shield] ![Supports i386 Architecture][i386-shield]

## About
시놀로지 구버전 supervisor 2021.1 버전용 config.json auto_uart 버전입니다.

## Version : 1.1.0
- alpine linux images를 python3 이미지로 교체
- CPU 최적화 및 딜레이 수정

## Installation

1. 홈어시스턴트의 Hass.io > ADD-ON STORE에서 Add new repository by URL에 https://github.com/HAKorea/addons 를 입력한 다음 ADD 버튼을 누릅니다.
2. ADD-ON STORE 페이지 하단에서 "Kocom Wallpad Controller with RS485" 클릭합니다.
3. "INSTALL" 버튼을 누르면 애드온이 설치됩니다. 최대 약 10분 정도 소요. 
4. INSTALL 버튼위에 설치 애니메이션이 동작하는데 이것이 멈추더라도 REBUILD, START 버튼이 나타나지 않는 경우가 있습니다.
5. 이 애드온은 이미지를 내려받는 것이 아니라 직접 여러분의 Hassio에서 이미지를 만듭니다. 따라서 컴퓨터성능과 인터넷 속도에 따라서 시간이 좀 걸립니다. 
6. INSTALL 버튼을 누른다음 설치 애니메이션이 실행되면 제대로 설치중인 것입니다. INSTALL을 여러번 누르지 마시고 기다리다 지치면 브라우저 페이지를 리프리시 하세요. 
7. 애드온 페이지에서 Config을 본인의 환경에 맞게 수정합니다.
8. "START" 버튼으로 애드온을 실행합니다.

만일 rs485.py 파일을 수정하시려면 한번 실행한 후 애드온을 Stop 하시고 share/kocom/ 폴더에 있는 파일을 알맞게 수정하신 다음 애드온을 Start 하시면 이후부터는 수정된 파일을 적용합니다.

## Configuration

Add-on configuration:

```yaml
RS485:
  type: Serial
Socket:
  server: 192.168.x.x
  port: 8899
SocketDevice:
  device: kocom
Serial:
  port1: /dev/ttyUSB0
SerialDevice:
  port1: kocom
MQTT:
  anonymous: false
  server: 192.168.x.x
  username: id
  password: pw
Wallpad:
  light: false
  plug: false
  thermostat: false
  fan: false
  gas: false
  elevator: false
Advanced:
  INIT_TEMP: 22
  SCAN_INTERVAL: 300
  SCANNING_INTERVAL: 0.8
  DEFAULT_SPEED: medium
  LOGLEVEL: info
KOCOM_LIGHT_SIZE:
  - name: livingroom
    number: 3
  - name: bedroom
    number: 2
  - name: room1
    number: 2
  - name: room2
    number: 2
  - name: kitchen
    number: 3
KOCOM_PLUG_SIZE:
  - name: livingroom
    number: 3
  - name: bedroom
    number: 2
  - name: room1
    number: 2
  - name: room2
    number: 2
  - name: kitchen
    number: 3
KOCOM_ROOM:
  - livingroom
  - bedroom
  - room1
  - room2
  - kitchen
KOCOM_ROOM_THERMOSTAT:
  - livingroom
  - bedroom
  - room1
  - room2
```

### Option: `RS485` (required)
```yaml
type: Serial                    // Serial 혹은 Socket
```
### Option: `Socket` (required)
```yaml
server: 192.168.x.x           // Socket 쓸 경우 socket IP주소
port: 8899                        // Socket 쓸 경우 socket PORT번호
```
### Option: `SocketDevice` (required)
```yaml
device: kocom               // socket 쓸 경우 월패드 이름{{장치이름}}
```
### Option: `Serial` (required)
```yaml
port1: /dev/ttyUSB0        // serial 쓸 경우 (월패드 혹은 그렉스)의 장치경로 작성
port2: /dev/ttyUSB1        // serial 쓸 경우 (월패드 혹은 그렉스)의 장치경로 작성
port3: /dev/ttyUSB2        // serial 쓸 경우 (월패드 혹은 그렉스)의 장치경로 작성
```
port2, port3는 추가,삭제 가능

### Option `SerialDevice` (required)
```yaml
port1: kocom               // serial 쓸 경우 (월패드 이름 혹은 그렉스 이름) 작성{{장치이름}}
port2: grex_ventilator     // serial 쓸 경우 (월패드 이름 혹은 그렉스 이름) 작성{{장치이름}}
port3: grex_controller     // serial 쓸 경우 (월패드 이름 혹은 그렉스 이름) 작성{{장치이름}}
```
port2, port3는 추가,삭제 가능

{{장치이름}}
kocom = 코콤월패드
grex_ventilator = 그렉스 환기장치
grex_controller = 그렉스 환기장치의 리모콘(환기모드, 정지 등)

### Option `MQTT` (required)
```yaml
anonymous: false           // MQTT 설정
server: 192.168.x.xx         // MQTT 서버
username: id                 // MQTT ID
password: pw                // MQTT PW
```

### Option `Wallpad` (required)
```yaml
light: true                    // 조명 
plug: true                    // 플러그 
thermostat: true            // 난방 
fan: true                     // 환기팬 
gas: true                     // 가스 
elevator: true               // 엘레베이터 
```

### Option `Advanced` (required)
```yaml
INIT_TEMP: 22           // 보일러 초기값
SCAN_INTERVAL: 300      // 월패드의 상태값 조회 간격
SCANNING_INTERVAL: 0.5  // 상태값 조회 시 패킷전송 간격
DEFAULT_SPEED: medium   //환풍기 초기속도 low, medium, high
LOGLEVEL: info , debug, info, warn 중에 하나
```
### Option `KOCOM_LIGHT_SIZE` (optional)
name은 방이름, number는 조명 개수. 본인의 집 수량만큼 추가 가능.

```yaml
KOCOM_LIGHT_SIZE:
  - name: livingroom
    number: 3
  - name: bedroom
    number: 2
```
### Option `KOCOM_PLUG_SIZE` (optional)
name은 방이름, number는 플러그 개수. 본인의 집 수량만큼 추가 가능.

```yaml
KOCOM_PLUG_SIZE:
  - name: livingroom
    number: 3
  - name: bedroom
    number: 2
```
### Option `KOCOM_ROOM` (optional)
방이름을 배열로 개수만큼 추가

```yaml
KOCOM_ROOM:
  - livingroom
  - bedroom
  - room1
```
방 패킷에 따른 방이름 패킷 이름은 00부터 01, 02로 시작하는 순서와 방이름이 매칭되어야 함
월패드에서 장치를 작동하며 방이름(livingroom, bedroom, room1  등)을 확인하여 본인의 상황에 맞게 바꾸세요

### Option `KOCOM_ROOM_THERMOSTAT` (optional)
```yaml
KOCOM_ROOM_THERMOSTAT:
  - livingroom
  - bedroom
  - room1
```
조명/콘센트와 난방의 방패킷이 달라서 두개로 나뉘어있습니다.
방 패킷에 따른 방이름 패킷 이름은 00부터 01, 02로 시작하는 순서와 방이름이 매칭되어야 함
월패드에서 장치를 작동하며 방이름(livingroom, bedroom, room1  등)을 확인하여 본인의 상황에 맞게 바꾸세요

## Support

Got questions?

You have several options to get them answered:

- The [Korea Wallpad Controller][github].
- The [Home Assistant 네이버카페][forum].

버그신고는 카페나 깃허브로 해주세요 [open an issue on our GitHub][issue].


[forum]: https://cafe.naver.com/koreassistant
[github]: https://github.com/HAKorea/addons
[issue]: https://github.com/zooil/wallpadRS485/issues
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg

