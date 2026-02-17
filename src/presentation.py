import cv2
import numpy as np
import mediapipe as mp
import os
import time
import math
from collections import deque
from cvzone.HandTrackingModule import HandDetector
from voice_control import VoiceController
from posture_monitor import PostureMonitor

#posture
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence= 0.6, min_tracking_confidence=0.6)
posture = PostureMonitor(persistence=2, cooldown=5)
posture_alert_until = 0
visual_duration = 1
# currentTime = time.time()
postureEnabled = True

#voice
voice = VoiceController(model_size="small")
voice.start()


#dimensions
width, height = 1280, 720
hs, ws = 120, 213  # webcam size (top-right)
defaultWidth, defaultHeight = 213,120

cap = cv2.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

folderPath = "PPT"
pathImages = sorted(os.listdir(folderPath), key=len)

imgNumber = 0

# Swipe variables
wristPositions = deque(maxlen=6)
swipeThreshold = 150
lastSwipeTime = 0
swipeCooldown = 1  # seconds

# Drawing variables
drawColor = (0, 0, 255)
brushThickness = 12
xp, yp = 0, 0
imgCanvas = None
drawingEnabled = True

resizeMode = False
voiceResize = False
webcamWidth,webcamHeight = defaultWidth,defaultHeight

detector = HandDetector(detectionCon=0.8, maxHands=1)

#main loop
while True:
    currentTime = time.time()
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)

    #process rgb image
    rgb = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    pose_results = pose.process(rgb)

    #Load slide
    pathFullImage = os.path.join(folderPath, pathImages[imgNumber])
    imgCurrent = cv2.imread(pathFullImage)

    if imgCanvas is None or imgCanvas.shape != imgCurrent.shape:
        imgCanvas = np.zeros_like(imgCurrent)

    command = voice.get_command()
    if command:
        print("Voice command: ", command)
    
    if command == "next":
        if imgNumber < len(pathImages) - 1:
            imgNumber += 1
            imgCanvas = np.zeros_like(imgCurrent)
        
    elif command == "previous":
        if imgNumber > 0:
            imgNumber -= 1
            imgCanvas = np.zeros_like(imgCurrent)

    elif command == "red":
        drawColor = (0,0,255)
    
    elif command == "blue":
        drawColor = (255,0,0)

    elif command == "green":
        drawColor = (0,255,0)

    elif command == "start":
        drawingEnabled = True

    elif command == "stop":
        drawingEnabled = False

    elif command == "resize":
        if voiceResize == False:
            voiceResize = True
        elif voiceResize == True:
            voiceResize = False

    elif command == "clear":
        imgCanvas = np.zeros_like(imgCurrent)

    elif command == "posture":
        postureEnabled = not postureEnabled

    

    if postureEnabled:    
        if pose_results.pose_landmarks:
            posture.update(pose_results.pose_landmarks.landmark)
            if currentTime - posture.last_correction_time < 0.1:
                posture_alert_until = currentTime + visual_duration
        else:
            posture.update(None)
           

    hands, img = detector.findHands(img)

    if hands:
        hand = hands[0]
        fingers = detector.fingersUp(hand)
        lmList = hand['lmList']

        rawX, rawY = lmList[8][0], lmList[8][1]

        #interp pointer coords
        x1 = int(np.interp(rawX, [width // 3, width], [0, width]))
        y1 = int(np.interp(rawY, [100, height - 100], [0, height]))

        currentTime = time.time()

        #swipe to next
        if fingers == [1,1,1,1,1]:

            wristX = lmList[0][0]  # wrist base (stable)
            wristPositions.append(wristX)

            if len(wristPositions) == wristPositions.maxlen:
                deltaX = wristPositions[-1] - wristPositions[0]

                if abs(deltaX) > swipeThreshold and (currentTime - lastSwipeTime) > swipeCooldown:

                    xp, yp = 0, 0  # stop drawing

                    if deltaX > 0:
                        #left swipe
                        if imgNumber > 0:
                            imgNumber -= 1
                            imgCanvas = np.zeros_like(imgCurrent)
                        # #right swipe
                        # if imgNumber < len(pathImages) - 1:
                        #     imgNumber += 1
                        #     imgCanvas = np.zeros_like(imgCurrent)
                    else:
                        #right swipe
                        if imgNumber < len(pathImages) - 1:
                            imgNumber += 1
                            imgCanvas = np.zeros_like(imgCurrent)
                        # #left swipe
                        # if imgNumber > 0:
                        #     imgNumber -= 1
                        #     imgCanvas = np.zeros_like(imgCurrent)

                    lastSwipeTime = currentTime
                    wristPositions.clear()

        else:
            wristPositions.clear()

        #resize
        if fingers == [1,1,0,0,0] and voiceResize:
            resizeMode = True
        else:
            resizeMode = False

        if resizeMode:
            xThumb,yThumb = lmList[4][0], lmList[4][1]
            xIndex,yIndex = lmList[8][0], lmList[8][1]

            length = math.hypot(xIndex-xThumb, yIndex-yThumb)
            newWidth = int(np.interp(length, [30,250], [defaultWidth,width]))
            newHeight = int(newWidth * height / width)   #keep aspect ratio

            webcamWidth, webcamHeight = min(newWidth,width), min(newHeight,height) #makes sure it doesnt go beyond 1280x720
            
        #pointer
        if fingers == [0, 1, 1, 0, 0]:
            cv2.circle(imgCurrent, (x1, y1), 12, (0, 0, 255), cv2.FILLED)
            xp, yp = 0, 0

        #drawing
        if fingers == [0, 1, 0, 0, 0] and drawingEnabled:
            if xp == 0 and yp == 0:
                xp, yp = x1, y1

            cv2.line(imgCanvas, (xp, yp), (x1, y1), drawColor, brushThickness)
            xp, yp = x1, y1
        else:
            xp, yp = 0, 0

    #canvas-slide merge
    imgGray = cv2.cvtColor(imgCanvas, cv2.COLOR_BGR2GRAY)
    _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
    imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)

    imgCurrent = cv2.bitwise_and(imgCurrent, imgInv)
    imgCurrent = cv2.bitwise_or(imgCurrent, imgCanvas)

    #webcam
    imgSmall = cv2.resize(img, (webcamWidth, webcamHeight))

    hSmall, wSmall, _ = imgSmall.shape
    hSlide, wSlide, _ = imgCurrent.shape

    # Ensure webcam fits inside slide
    wSmall = min(wSmall, wSlide)
    hSmall = min(hSmall, hSlide)
    imgSmall = imgSmall[0:hSmall, 0:wSmall]
    imgCurrent[0:hSmall, wSlide-wSmall:wSlide] = imgSmall   #put webcam top right

    statustext = "Drawing: ON" if drawingEnabled else "Drawing: OFF"
    resizeText = "Resize Mode: ON" if voiceResize else "Resize: OFF"

    #posture button
    if currentTime < posture_alert_until:
        hSlide, wSlide, _ = imgCurrent.shape
        circle_x = wSlide - 25
        circle_y = 25
        cv2.circle(imgCurrent, (circle_x, circle_y), 10, (0, 0, 255), cv2.FILLED)
        text_x = circle_x - 170
        text_y = 35
        cv2.putText(imgCurrent, "POSTURE ALERT",(text_x, text_y),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0, 0, 255),1)


    cv2.putText(imgCurrent, statustext, (20,40),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0, 255, 0) if drawingEnabled else (0, 0, 255),2)
    cv2.putText(imgCurrent, "Pen",(20, 80),cv2.FONT_HERSHEY_SIMPLEX,0.8,drawColor,2)
    cv2.putText(imgCurrent, resizeText, (20,120),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0, 255, 0) if voiceResize else (0, 0, 255),2)

    status_text = "POSTURE: ON" if postureEnabled else "POSTURE: OFF"
    color = (0, 255, 0) if postureEnabled else (0, 0, 255)

    cv2.putText(imgCurrent,status_text,(20, height - 20),cv2.FONT_HERSHEY_SIMPLEX,0.6,color,2)

    cv2.imshow("Slides", imgCurrent)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
