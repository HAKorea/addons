# Google Assistant Webserver for Hassio

![Supports amd64 Architecture][amd64-shield] ![Supports armhf Architecture][armhf-shield] ![Supports armv7 Architecture][armv7-shield] 

## What is this?

This Addon is converted from Google Assistant Webserver for Hassio. Original Code was made by robwolff3
https://github.com/robwolff3/google-assistant-webserver


## About
robwolff3가 만든 구글 어시스턴트 웹서버를 애드온으로 컨버팅한 것입니다. 
자세한 사용법은 [네이버 Homeassistant 카페](https://cafe.naver.com/koreassistant/661) 설정기를 참고하세요. 

## Version : 0.5.2
- asoundrc 추가

## Installation

1. 홈어시스턴트의 Hass.io > ADD-ON STORE에서 Add new repository by URL에 https://github.com/HAKorea/addons 를 입력한 다음 ADD 버튼을 누릅니다.
2. ADD-ON STORE 페이지 하단에서 "Google Assistant Webserver for Hassio" 클릭합니다.
3. "INSTALL" 버튼을 누르면 애드온이 설치됩니다. 최대 약 15분 정도 소요. 
4. INSTALL 버튼위에 설치 애니메이션이 동작하는데 이것이 멈추더라도 REBUILD, START 버튼이 나타나지 않는 경우가 있습니다.
5. 이 애드온은 이미지를 내려받는 것이 아니라 직접 여러분의 Hassio에서 이미지를 만듭니다. 따라서 컴퓨터성능과 인터넷 속도에 따라서 시간이 좀 걸립니다. 
6. INSTALL 버튼을 누른다음 설치 애니메이션이 실행되면 제대로 설치중인 것입니다. INSTALL을 여러번 누르지 마시고 기다리다 지치면 브라우저 페이지를 리프리시 하세요. 
7. 애드온 페이지에서 Config을 본인의 환경에 맞게 수정합니다.
8. 별도로 구글 계정설정이 필요합니다. [네이버 Homeassistant 카페](https://cafe.naver.com/koreassistant/661) 설정기를 참고하세요. 

이 애드온은 용량이 600메가 정도로 좀 큽니다. 네트웍 속도와 컴퓨터의 성능에 따라 설치에 시간이 좀 걸릴 수 있습니다. Debian 이미지를 기초로 애드온을 Building 하는데 중간에 데비안 setup-tools 설치에 대한 Warning이 하나 나옵니다. Docker build에서는 문제가 되지 않지만 HA 애드온에서는 설치 과정에  Failed to install addon, [object Object] 라고 뜨고 진행하지 않는 경우가 생길 수 있습니다. 하지만 애드온은 계속 설치를 진행중이니 기다리시면 됩니다. 

## Configuration

Add-on configuration:

```yaml
    client_secrets: client_secret.json
    project_id: #google-assistant-project-id#
    model_id: #google-assistant-project-model-id#
```

### Option: `client_secret` (필수)
구글 어시스턴트 연동을 위한 credential 파일입니다. [네이버 Homeassistant 카페](https://cafe.naver.com/koreassistant/661) 설정기를 참고.

### Option: `project_id` (필수)
구글 어시스턴트 프로젝트 id 입니다. [네이버 Homeassistant 카페](https://cafe.naver.com/koreassistant/661) 설정기를 참고

### Option: `model_id` (필수)
구글 어시스턴트 모델 id입니다. [네이버 Homeassistant 카페](https://cafe.naver.com/koreassistant/661) 설정기를 참고

### configuration.yaml 추가
아래와 같이 설정해줍니다.

```yaml
notify:
  - name: ga_broadcast
    platform: rest
    resource: http://containerip:5000/broadcast_message
  - name: ga_command
    platform: rest
    resource: http://containerip:5000/command
```

### .asoundrc 설정
필요한 경우 /share/gawebserver 폴더에 .asoundrc 파일을 추가할 수 있습니다. 
/share/gawebserver/.asoundrc 가 존재하면 /root로 복사해서 사용합니다. 

## Support

궁금한 점이 있으신가요??

아래에 문의 하시면 답변을 구하실 수 있습니다.:

- The [Home Assistant Korean Community][github].
- The [Home Assistant 네이버카페][forum].

버그신고는 카페나 깃허브로 해주세요 [open an issue on our GitHub][issue].

## RELEASE NOTES

0.5.1 첫 배포


[forum]: https://cafe.naver.com/koreassistant
[github]: https://github.com/HAKorea/addons
[issue]: https://github.com/zooil/wallpad/issues
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg

