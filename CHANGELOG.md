## 수정 내역

### (latest)

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
