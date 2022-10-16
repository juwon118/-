import pygame
import time
import RPi.GPIO as GPIO
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import datetime
import os
from pyfcm import FCMNotification
APIKEY = "AAAAwa-pUpg:APA91bGhPEixe8jcEeup_YmtgB1nSTWIOHAlGFHnsMUc6d_xc6xozie_d-dmn9-lTrPoOMC-2a6iXUHLNWGXXQ-RN67KDvJfROaPCNRkrqwkd9rCZMjDQmVUuAyWaxT8f6dxcuS8JlFB"
TOKEN = "eyNwrCUeQYGYTfhQ-qzIue:APA91bFnMhry20XfqdV4SrksOl3KtQNNlS-rAkOb4Y5ZYCFBS1qOp5enY9PuzJ-ziYJCql8OvvQ1CukQzFjub8BsDpljDDopyYUobapHYO2HE7-En1AbfauckdO0wk8jLtlGzMX0BRjT"

push_service = FCMNotification(APIKEY)
#푸시알림
def sendMessage(body, title):
    data_message = {
        "body":body,
        "title":title
        }
    result = push_service.single_device_data_message(registration_id=TOKEN, data_message=data_message)
    print(result)
#파이어베이스 데이터베이스업로드
cred = credentials.Certificate('firestore_dust_service.json')
firebase_admin.initialize_app(cred)
db = firestore.client() 
doc_ref = db.collection(u'final')

# 로드셀
import sys

EMULATE_HX711=False


if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711
else:
    from emulated_hx711 import HX711

hx = HX711(16, 20)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(10)

hx.reset()

hx.tare()
#

GPIO.setmode (GPIO.BCM)

GPIO.setup (18, GPIO.IN)

TouchCount1 = 0
TouchCount2 = 0
LoadCellCount1 = 0
LoadCellCount2 = 0
pygame.init()

try:

    while True :
        
        TouchSensor = GPIO.input(18)
        LoadCellVal = hx.get_weight() #로드셀 무게값 저장
        print(LoadCellVal)
        hx.power_down()
        hx.power_up()
        time.sleep(0.1)
        
        if TouchSensor == 1 and TouchCount2 == 0:   #터치첸서 1회입력
            TouchCount1 = 1
            time.sleep(1)

        if TouchSensor == 1 and TouchCount2 == 1:   #터치센서 2회입력
            TouchCount1 = 2
            time.sleep(1)    

        if TouchSensor == 1 and TouchCount2 == 2:   #터치센서 3회입력
            TouchCount1 = 3
            time.sleep(1)

        if TouchSensor == 1 and TouchCount2 == 3:   #터치센서 4회입력(초기화)
            TouchCount1 = 0
            TouchCount2 = 0
            time.sleep(1)    

        if (LoadCellVal > 1000 or LoadCellVal < -1000) and LoadCellCount2 == 0: # 무게가 1000이넘거나 -1000미만일경우 발판에 올라갔다고 판단.
            LoadCellCount1 = 1
            print('f')

        if (-500 <= LoadCellVal <= 500) and (TouchCount2== 1 or TouchCount2 == 2 or TouchCount2 == 3): # 무게가 -500~500사이일경우 종료
            LoadCellCount1 = 2
            print('f2')
        
        if LoadCellCount1 == 1: #(시작모드) 무게가 감지된후 원하는 씻기모드를 선택하도록 음성메세지 출력 
            pygame.mixer.music.load("Start.mp3")
            pygame.mixer.music.play()
            sendMessage("Start", "Start")
            print('Start Washing')
            LoadCellCount1 = 3
            LoadCellCount2 = 1
        
        if LoadCellCount1 == 3 and TouchCount1 == 1:    #(양치모드) 터치센서에 입력이 1회일 경우 양치하기 모드 시작
            print('Brush Teeth')
            mode = "양치하기"
            timestamp_start = time.time()
            time_str=datetime.datetime.fromtimestamp(timestamp_start).strftime('%H시 %M분')
            time.sleep(1)
            pygame.mixer.music.load("TeethClean.mp3")
            pygame.mixer.music.play()
            sendMessage("Teeth", "양치를 시작했어요.")  #푸시알림
            TouchCount1 = 0
            TouchCount2 = 1
            
        if LoadCellCount1 == 3 and TouchCount1 == 2:    #(손씻기모드) 터치센서에 입력이 2회일 경우 손씻기 모드 시작
            print("'Wash One's Hands")
            mode = "손씻기"
            timestamp_start = time.time()
            time_str=datetime.datetime.fromtimestamp(timestamp_start).strftime('%H시 %M분')
            time.sleep(1)
            pygame.mixer.music.load("HandsClean.mp3")
            pygame.mixer.music.play()
            sendMessage("Hands", "손씻기를 시작했어요.") #푸시알림
            TouchCount1 = 0
            TouchCount2 = 2
            
        if LoadCellCount1 == 3 and TouchCount1 == 3:    #(세수모드) 터치센서에 입력이 3회일 경우 세수하기 모드 시작
            print("'Wash One's Face")
            mode = "세수하기"
            timestamp_start = time.time()
            time_str=datetime.datetime.fromtimestamp(timestamp_start).strftime('%H시 %M분')
            time.sleep(1)
            pygame.mixer.music.load("FaceClean.mp3")
            pygame.mixer.music.play()
            sendMessage("Face", "세수를 시작했어요.") #푸시알림
            TouchCount1 = 0
            TouchCount2 = 3
        
        if LoadCellCount1 == 2:   #(종료) 발판에서 내려갈경우 종료
            print('Stop')
            pygame.mixer.music.stop()
            sendMessage("Stop", "씻기를 끝마쳤어요.") #푸시알림
            timestamp_stop = time.time()
            date = datetime.date.today()
            time.sleep(1)
            doc_ref.add({
                    u'date':str(date),
                    u'mode':str(mode),
                    u'start':timestamp_start,
                    u'stop':timestamp_stop,
                    u'time_str':str(time_str)
            })
            TouchCount1 = 0
            TouchCount2 = 0
            LoadCellCount1 = 0
            LoadCellCount2 = 0
            
        
except KeyboardInterrupt:

    GPIO.cleanup
    

            





