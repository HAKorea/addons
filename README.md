# Korean Community Add-ons for Hassio

* 본 애드온은 더이상 업데이트하지 않습니다. 기존 사용자를 위해 운용하는 것이며 일부 수정 가능한 범위내에서 업데이트를 진행합니다. 메이저 버전에서 동작하지 않을 수 있습니다. 



애드온 스토어에서 Repository URL을 `https://github.com/HAKorea/addons` 으로 입력하고 애드온을 추가하세요.



### Kocom Wallpad Controller with RS485 (kocomRS485)

 랜이님이 만든 코콤 월패드 파이썬 프로그램을 애드온으로 포팅한 것입니다.

### Universal Wallpad Controller with RS485 (wallpad)

 그레고리하우스님이 만든 코맥스 월패드 nodejs 프로그램을 애드온으로 포팅한 것입니다.
 기본적으로 코맥스로 동작하며 커스터마이징이 가능한 애드온으로 다른 아파트 nodejs 파일을 사용할 수 있습니다. 
 현재 삼성, 대림, 코맥스, 현대 월패드를 지원하면 ew11 같은 무선 소켓 연결도 지원합니다. 

### USB Video Connector Addon with Motion Server (motion4hassio)

 웹캠이나 USB 카메라를 mjpeg motion server를 통해 HA에 통합 가능한 애드온입니다.

### Owntracks Recorder for Hassio (owntracks4hassio)

Owntracks Recorder를 애드온으로 만든 것입니다. ingress를 사용하여 사이드 패널에 추가할 수 있습니다. 

### Google Assistant Webserver

robwolff3가 만든 구글 어시스턴트 웹서버를 애드온으로 컨버팅한 것입니다. 
구글 어시스턴트를 HA에서 텍스트 명령으로 컨트롤 할 수 있는 스위치, 자동화 등을 제작할 수 있습니다. 
자세한 사용법은 [네이버 Homeassistant 카페 설정기](https://cafe.naver.com/koreassistant/661)를 참고하세요.

### 삼성SDS 월패드 RS485 Add-on (엘리베이터 호출 지원)

n-andFlash님이 만든 SDS월패드 애드온입니다. 
삼성SDS 월패드를 사용하는 집에서, RS485를 이용해 여러 장치들을 제어할 수 있는 애드온입니다.
현관 스위치를 대신하여 엘리베이터를 호출하는 기능이 있습니다.
MQTT discovery를 이용, 장치별로 yaml 파일을 직접 작성하지 않아도 집에 있는 모든 장치가 HA에 자동으로 추가됩니다.

### Webdav addon for file storage in HA supervisor

Webdav를 HA에서 생성하여 /share/webdav 폴더로 사용하는 애드온입니다. 파일 저장소가 HA에 통합되어 백업을 HA와 같이 사용할 수 있습니다. nginx reverse proxy 설정이 필요합니다. 

### 문의
네이버카페 : https://cafe.naver.com/koreassistant

