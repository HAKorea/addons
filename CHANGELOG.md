## 수정 내역

#### 3.3

* 초인종 때문에 인터폰 상태 바뀔때 죽는 부분 수정
* MQTT로 임의의 serial packet 보내는 기능 추가 (디버그용)

#### 3.2

* 같은 장치에 대한 명령을 동시에 여러개 받았을 때 죽는 경우 수정
* entrance_mode: full 일때 가스밸브 상태 못받아오는 부분 수정

#### 3.1

* 처음 설정하시는 분의 접근성을 위해 entrance\_mode 기본값을 off로 변경
  * 엘리베이터 호출을 사용하시려면 현관스위치 RS485 분리 후 entrance\_mode를 full로 변경하면 됩니다.
* 로그파일이 매 시간 덮어써지는 문제 수정

### 3

* 현관, 공동현관 초인종 이벤트 추가 (부엌/화장실 인터폰 있는 경우)
* dump 기능 추가
  * 패킷 분석이 필요할 때, 애드온 시작 전 정해진 시간 동안 패킷을 로깅할 수 있습니다.
* 로그를 share 디렉토리에 파일로 남기는 기능 추가

#### 2.7

* gas\_valve sensor 수정
* checksum fail된 state는 반영하지 않도록 개선
* 시작할때 가끔 last\_query 없어서 죽는 현상 수정
* 특정 option이 없으면 default값으로 시도하도록 개선

#### 2.4

* 실시간에너지 discovery 장치 오류 수정

#### 2.3

* 명령 전송 타이밍 최적화
  * "last\_packet" 옵션은 삭제하였습니다.
* 몇몇 예외상황 처리

#### 2.2

* 현관 스위치 기능들 discovery 추가
* 전등 discovery 오류 수정

#### 2.1

* 실행 시 KeyError: 'prefix' 오류 수정
  * 업데이트 후 Configuration을 default로 돌렸다가 다시 설정하세요.
* share로 복사하는 동작 삭제

### 2

* serial 대신 **EW11 socket 통신 사용 가능**하도록 추가
  * socket 사용 시 엘리베이터 호출은 지원하지 않음
* **MQTT discovery 지원**, 이제 yaml을 만들 필요가 없습니다
* prefix 변경 옵션 추가

### 1

* HA Addon 등록 가능한 형태로 정리
* 설정 json 파일 분리

### 0

* .py 최초 공개
