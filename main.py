import json
import time
import cv2
import sys
import os
import requests
from yanshee import Yanshee

ROBOT_IP = "10.0.3.234"
robot = Yanshee(ROBOT_IP)

CENTER_X, CENTER_Y = 320, 240
THRESHOLD = 40
current_pan, current_tilt = 90, 90

def stop_all_visions():
    print("Nettoyage des ressources...")
    endpoints = [
        ("/visions", "PUT", {"type": "stream", "operation": "stop"}),
        ("/visions", "PUT", {"type": "tracking", "operation": "stop", "option": "face"}),
        ("/visions/streams", "DELETE", {})
    ]
    for url, method, data in endpoints:
        try:
            if method == "PUT":
                requests.put(f"http://{ROBOT_IP}:9090/v1{url}", json=data, timeout=1)
            else:
                requests.delete(f"http://{ROBOT_IP}:9090/v1{url}", timeout=1)
        except: continue
    time.sleep(1)

def setup_tracking():
    stop_all_visions()
    payload = {"type": "tracking", "operation": "start", "option": "face", "timestamp": int(time.time() * 1000)}
    try:
        res = robot._put("/visions", payload)
        return res.get('code') in [0, 200] or res.get('msg') == 'success'
    except: return False

def setup_stream():
    stop_all_visions()
    try:
        robot._post("/visions/streams", {"resolution": "640x480"})
        time.sleep(2)
        return True
    except: return False

def update_servos(x, y):
    global current_pan, current_tilt
    if x > (CENTER_X + THRESHOLD): current_pan -= 6
    elif x < (CENTER_X - THRESHOLD): current_pan += 6
    if y > (CENTER_Y + THRESHOLD): current_tilt += 4
    elif y < (CENTER_Y - THRESHOLD): current_tilt -= 4
    current_pan = max(10, min(170, current_pan))
    current_tilt = max(60, min(120, current_tilt))
    robot.set_servos({"NeckLR": current_pan, "NeckUD": current_tilt}, speed=15)

def run_vision_system(mode="tracking"):
    global current_pan, current_tilt
    face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml") if mode == "stream" else None
    last_heartbeat = time.time()
    
    while True:
        cap = cv2.VideoCapture(f"http://{ROBOT_IP}:8000")
        if not cap.isOpened():
            time.sleep(1)
            continue
            
        print(f"\n--- Flux {mode} connecté (Appuyez sur 'q' pour quitter) ---")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("\nFlux interrompu. Tentative de reconnexion...")
                break 
            
            if time.time() - last_heartbeat > 30:
                try:
                    if mode == "tracking":
                        robot._put("/visions", {"type": "tracking", "operation": "start", "option": "face", "timestamp": int(time.time() * 1000)})
                    last_heartbeat = time.time()
                except: pass

            if mode == "tracking":
                result = robot.get_face_tracking()
                faces = result.get('data', {}).get('face', []) if isinstance(result, dict) else []
                if faces:
                    f = faces[0]
                    fx, fy = int(f.get('x', CENTER_X)), int(f.get('y', CENTER_Y))
                    fw, fh = int(f.get('width', 0)), int(f.get('height', 0))
                    cv2.rectangle(frame, (fx, fy), (fx+fw, fy+fh), (0, 255, 0), 2)
                    update_servos(fx + (fw // 2), fy + (fh // 2))

            elif mode == "stream" and face_cascade:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
                for (x, y, w, h) in faces:
                    update_servos(x + (w // 2), y + (h // 2))
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    break

            cv2.imshow("Yanshee Live", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return

        cap.release()
        time.sleep(1)

if __name__ == "__main__":
    try:
        while True:
            print("\n1. Tracking Natif (IA Robot)")
            print("2. Stream + OpenCV (IA PC)")
            print("3. Quitter")
            choix = input("Choix : ")
            
            if choix == "1":
                if setup_tracking(): run_vision_system("tracking")
            elif choix == "2":
                if setup_stream(): run_vision_system("stream")
            elif choix == "3":
                robot.say("Goodbye!")
                stop_all_visions()
                sys.exit()
    except KeyboardInterrupt:
        stop_all_visions()
        sys.exit()