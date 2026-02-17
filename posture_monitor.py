import time
import math
import threading
import pyttsx3

class PostureMonitor:
    def __init__(self,persistence=6, cooldown=10):
        self.persistence = persistence
        self.cooldown = cooldown

        self.bad_posture_start = None
        self.last_correction_time = 0

        #tts engine 
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 170)
        self.tts_engine.setProperty('volume', 1.0)

        self.tts_lock = threading.Lock()

        # self.is_speaking = False

        # #torso
        # self.torso_history = []
        # self.history_size = 10

    def update(self, landmarks):
        if landmarks is None:
            self.bad_posture_start = None
            return
        
        nose = landmarks[0]
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        left_hip = landmarks[23]
        right_hip = landmarks[24]

        shoulder_bad = self.check_shoulder(left_shoulder, right_shoulder)
        head_bad = self.check_head(nose, left_shoulder, right_shoulder)
        # torso_bad = self.check_torso(left_shoulder,right_shoulder, left_hip, right_hip)

        posture_bad = shoulder_bad or head_bad 

        cTime = time.time()
        if posture_bad:
            if self.bad_posture_start is None:
                self.bad_posture_start = cTime

            elif (cTime - self.bad_posture_start > self.persistence and cTime - self.last_correction_time > self.cooldown):
                # if torso_bad:
                #     self.speak_async("     Sit straight")
                #     print("Torso")
                if shoulder_bad:
                    self.speak_async("       Keep your shoulders level")
                    print("Shoulder")
                elif head_bad:
                    self.speak_async("      Keep your head centered")
                    print("head")

                self.last_correction_time = cTime
                self.bad_posture_start = None

        else:
            self.bad_posture_start = None

    def check_shoulder(self, left_shoulder, right_shoulder):
        diff = abs(left_shoulder.y - right_shoulder.y)
        return diff > 0.10
    
    def check_head(self, nose, left_shoulder, right_shoulder):
        mid = (left_shoulder.x + right_shoulder.x) / 2
        offset = abs(nose.x - mid)
        return offset > 0.04
    
    # def check_torso(self, left_shoulder,right_shoulder, left_hip, right_hip):
    #     smid_x = (left_shoulder.x + right_shoulder.x) / 2
    #     smid_y = (left_shoulder.y + right_shoulder.y) / 2

    #     hmid_x = (left_hip.x + right_hip.x) / 2
    #     hmid_y = (left_hip.y + right_hip.y) / 2

    #     dx = smid_x - hmid_x
    #     dy = smid_y - hmid_y

    #     angle = abs(math.degrees(math.atan2(dx,dy)))
    #     self.torso_history.append(angle)
    #     if len(self.torso_history) > self.history_size:
    #         self.torso_history.pop(0)

    #         avg_angle = sum(self.torso_history) / len(self.torso_history)

    #         return avg_angle > 18


        
    
    def speak_async(self, message):
        # if self.is_speaking:
        #     return  # prevent overlapping speech

        def speak():
            with self.tts_lock:
                try:
                    self.tts_engine.say(message)
                    self.tts_engine.runAndWait()
                except Exception as e:
                    print("TTS Error", e)

        threading.Thread(target=speak, daemon=True).start()

