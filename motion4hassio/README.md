# USB Video Connector Addon

## About
USB 웹캠 또는 Easycap 을 사용하여 Composite 비디오를 사용하게 만드는 영상 서버입니다.
영상 서버는 Motion을 사용했습니다.
Motion : https://motion-project.github.io/

## Configuration
애드온을 설치한 후 영상/이미지를 저장할 디렉토리(target_dir)를 지정 해야 합니다. 

기본 설정은 Motion 과 동일하지만 일부 설정을 애드온에서 변경 가능하도록 제작했습니다.
https://motion-project.github.io/motion_config.html

```yaml
videodevice: /dev/video0
width: 720
height: 480
framerate: 5
text_right: '%Y-%m-%d %T-%q'
rotate: 0
target_dir: /config/www/video
on_event_start: /config/scripts/motion/start.sh
on_event_end: /config/scripts/motion/end.sh
on_movie_end: /config/scripts/motion/movie.sh %f
movie_output: 'on'
movie_max_time: 40
movie_quality: 80
movie_codec: mp4
snapshot_interval: 0
snapshot_name: '%v-%Y%m%d%H%M%S-snapshot'
picture_output: 'off'
picture_name: '%v-%Y%m%d%H%M%S-%q'
webcontrol_local: 'off'
```

on_event_start, on_event_end, on_movie_end 는 삭제 가능합니다. 
설치를 바로하면 /config/scripts/motion/안에 start.sh, movie.sh, end.sh 3가지 쉘스크립트 파일이 들어있습니다. 이것은 이벤트가 발생하면 애드온 로그에 아래와 같이 나타납니다. 
``` log
[1:Unknown] [NTC] [EVT] event_newfile: File of type 8 saved 
  to: /config/www/video/0-01-20200112233458.mp4
[1:Unknown] [NTC] [ALL] motion_detected: Motion detected 
  - starting event 1
[Info] Motion Start  ### start.sh 실행
[1:Unknown] [NTC] [ALL] mlp_actions: End of event 1
[Info] Movie End     ### movie.sh 실행
[Info] Motion End    ### end.sh 실행
```
이 파일들을 수정하여 사용하시거나 다른 파일을 config에서 연결하시면 됩니다. 이 파일을 수정하면 업데이트를 하더라도 그대로 유지됩니다. 

## configuration.yaml
``` configuration
camera:
  - platform: mjpeg
    name: yourCameraName
    mjpeg_url: http://your.ip.add.ress:8081/
```
```
http://your.ip.add.ress:8080/ 으로 브라우저에서 접속하면 Motion 웹관리 화면으로 접근 가능합니다.
```

## 문제해결

연결된 USB 비디오 장치가 없으면 실행할 수 없습니다.
문제가 생기면 
```sh
$ docker logs hassio_supervisor
```
명령을 실행하면 서버 에러 로그를 볼 수 있습니다. 
```log
20-02-01 14:30:47 ERROR (SyncWorker_9) [hassio.docker] Can't start 
addon_25b6f150_motion: 500 Server Error: Internal Server Error 
("error gathering device information while adding custom device 
"/dev/video0": no such file or directory")
```