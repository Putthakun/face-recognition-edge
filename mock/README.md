# Mock RTSP Stream บน Mac

## ติดตั้ง ffmpeg

```bash
brew install ffmpeg
```

## Stream ไฟล์วิดีโอผ่าน RTSP ด้วย MediaMTX

1. ดาวน์โหลด [MediaMTX](https://github.com/bluenviron/mediamtx/releases) (ชื่อเดิม rtsp-simple-server)

2. รัน MediaMTX:
```bash
./mediamtx
```

3. Push วิดีโอเข้า stream:
```bash
ffmpeg -re -stream_loop -1 -i your_video.mp4 \
  -c:v libx264 -preset ultrafast -tune zerolatency \
  -f rtsp rtsp://localhost:8554/face-test
```

4. ตั้งค่า `.env`:
```
STREAM_SOURCE=rtsp://localhost:8554/face-test
```

## ทดสอบดู stream

```bash
ffplay rtsp://localhost:8554/face-test
```
