# Webdav addon for file storage in HA Supervised

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armhf Architecture][armhf-shield] ![Supports armv7 Architecture][armv7-shield] ![Supports i386 Architecture][i386-shield]

## About
[Alexander](https://alexonepath.github.io/category/docker/guide/container-1-home.html
)님이 만드신 도커로 Webdav 서버 구축 방법을 HA 애드온으로 컨버팅한 것입니다. 

- The [Home Assistant Korean Community][github].
- The [Home Assistant 네이버카페][forum].

버그신고는 카페나 깃허브로 해주세요 [open an issue on our GitHub][issue].

## Version : 0.5.0


# Configuration

Add-on configuration:

```yaml
username: webdavUsername
password: webdavPassword
```

네트워크 포트는 사용할 웹데브 포트를 써주시면 됩니다.

nginx reverse proxy 작성

/share/nginx_proxy_default.conf 파일에 아래 내용을 추가하면 
mydomain.duckdns.org/webdev 로 접근가능합니다. 
```
location /webdav {                                    
     proxy_pass http://homeassistant.local.hass.io:5515;
     proxy_set_header Host $host;                
     proxy_redirect http:// https://;            
     proxy_http_version 1.1;                                                       
     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;                  
     proxy_set_header Upgrade $http_upgrade;                                       
     proxy_set_header Connection $connection_upgrade;                              
}
```
/share/webdev/photo
같이 하위 디렉토리를 생성한다면 파일의 오너쉽을 
```
chown www-data:www-data photo
```
명령으로 오너쉽을 바꿔준 다음 스마트폰앱에서 webdev 접근 경로로 
```
mydomain.duckdns.org/webdev/photo
```
를 적으시면 됩니다. 

## RELEASE NOTES
2021.01.10 첫번째 배포

[forum]: https://cafe.naver.com/koreassistant
[github]: https://github.com/HAKorea/addons
[issue]: https://github.com/zooil/wallpad/issues
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg

