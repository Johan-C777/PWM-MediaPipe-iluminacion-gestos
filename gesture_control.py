import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision as mp_vision
from collections import deque, Counter
import serial
import time
import os

SERIAL_PORT     = "COM3"
BAUD_RATE       = 9600
SEND_DELAY      = 0.15
SMOOTHING_FRAMES = 6

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "hand_landmarker.task")

CMD_30PCT  = b"A" 
CMD_70PCT  = b"B"
CMD_100PCT = b"C" 
CMD_SEQ1   = b"D"
CMD_SEQ2   = b"E"   
C_ACCENT = (255, 180,   0) 
C_NONE   = ( 80,  80,  80)
C_OK     = (  0, 220,  80) 
C_BG     = ( 20,  20,  20) 

GESTURE_INFO = {
    "FIST"       : ("Puno        -> LED Amarillo 30pct", CMD_30PCT,  (  0, 220, 160)),
    "PEACE"      : ("Paz (V)     -> LED Azul     70pct", CMD_70PCT,  (255, 160,   0)),
    "OPEN"       : ("Mano abierta-> LED Rojo    100pct", CMD_100PCT, (  0,  80, 255)),
    "THUMB_DOWN" : ("Pulgar abajo-> Secuencia 1",        CMD_SEQ1,   (200,   0, 200)),
    "THUMB_UP"   : ("Pulgar arriba-> Secuencia 2",       CMD_SEQ2,   (  0, 200, 200)),
}

def fingers_up(landmarks):

    TIPS = [4,  8, 12, 16, 20]
    PIPS = [3,  7, 11, 15, 19]  
    ext = []

    ext.append(landmarks[TIPS[0]].x < landmarks[PIPS[0]].x)

    for i in range(1, 5):
        ext.append(landmarks[TIPS[i]].y < landmarks[PIPS[i]].y)
    return ext 


def thumb_direction(landmarks):
 
    tip       = landmarks[4]
    ip        = landmarks[3]
    wrist     = landmarks[0]
    index_mcp = landmarks[5]
    mid_mcp   = landmarks[9]

    hand_h = abs(wrist.y - mid_mcp.y)
    margin = max(hand_h * 0.12, 0.025)

    tip_above_knuckles = tip.y < (index_mcp.y - margin)

    ip_above_knuckles  = ip.y  < index_mcp.y
    if tip_above_knuckles and ip_above_knuckles:
        return "up"

    tip_below_wrist = tip.y > (wrist.y + margin)
    ip_below_wrist  = ip.y  > wrist.y
    if tip_below_wrist and ip_below_wrist:
        return "down"

    return "neutral"


def classify_gesture(landmarks):

    ext = fingers_up(landmarks)

    if all(ext):
        return "OPEN"
    if ext[1] and ext[2] and not ext[3] and not ext[4]:
        return "PEACE"

    if not ext[1] and not ext[2] and not ext[3] and not ext[4]:
        d = thumb_direction(landmarks)
        if d == "up":
            return "THUMB_UP"
        if d == "down":
            return "THUMB_DOWN"
        return "FIST"

    return None

HAND_CONNECTIONS = [
    (0, 1),(1, 2),(2, 3),(3, 4),
    (0, 5),(5, 6),(6, 7),(7, 8),
    (0, 9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5, 9),(9,13),(13,17),
]

def draw_landmarks(frame, landmarks, img_w, img_h):
    """Dibuja el esqueleto y los puntos de la mano sobre el frame."""
    pts = [(int(lm.x * img_w), int(lm.y * img_h)) for lm in landmarks]
    for (a, b) in HAND_CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], (0, 200, 100), 2)
    for (x, y) in pts:
        cv2.circle(frame, (x, y), 4, (255, 255, 255), -1)
        cv2.circle(frame, (x, y), 4, (0, 150, 80), 1)


def main():

    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Modelo no encontrado: {MODEL_PATH}")
        print("        Descarga hand_landmarker.task y coloca junto al script.")
        return

    ser = None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) 
        print(f"[OK] Puerto serial: {SERIAL_PORT} @ {BAUD_RATE} baud")
    except serial.SerialException as e:
        print(f"[AVISO] Serial no disponible ({e}). Modo solo visualizacion.")

    BaseOptions    = mp.tasks.BaseOptions
    HandLandmarker = mp_vision.HandLandmarker
    HandOptions    = mp_vision.HandLandmarkerOptions
    RunningMode    = mp_vision.RunningMode

    options = HandOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] No se pudo abrir la webcam.")
        if ser:
            ser.close()
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


    gesture_history = deque(maxlen=SMOOTHING_FRAMES)
    stable_gesture  = None
    last_gesture    = None
    last_send       = 0.0
    current_cmd     = None

    print("[INFO] Sistema listo. Muestra un gesto. Presiona 'q' para salir.")

    with HandLandmarker.create_from_options(options) as detector:

        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] No se puede leer frame de la camara.")
                break

            frame = cv2.flip(frame, 1)
            h, w  = frame.shape[:2]

            rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts_ms    = int(time.monotonic() * 1000)
            result   = detector.detect_for_video(mp_image, ts_ms)

            raw_gesture = None
            if result.hand_landmarks:
                lms = result.hand_landmarks[0]
                draw_landmarks(frame, lms, w, h)
                raw_gesture = classify_gesture(lms)

            gesture_history.append(raw_gesture)
            valid = [g for g in gesture_history if g is not None]
            if len(valid) >= SMOOTHING_FRAMES // 2 + 1:
                best, count = Counter(valid).most_common(1)[0]
                stable_gesture = best if count >= SMOOTHING_FRAMES // 2 + 1 else None
            else:
                stable_gesture = None
            gesture = stable_gesture
            now = time.time()
            if gesture and gesture != last_gesture:
                if (now - last_send) >= SEND_DELAY:
                    info = GESTURE_INFO.get(gesture)
                    if info:
                        label, cmd, color = info
                        if ser:
                            try:
                                ser.write(cmd)
                                print(f"[SERIAL] {gesture:12s} -> {cmd}")
                            except serial.SerialException as e:
                                print(f"[ERROR] Serial: {e}")
                        else:
                            print(f"[SIM]    {gesture:12s} -> {cmd}")
                        current_cmd = (label, color)
                        last_send   = now
                last_gesture = gesture

            ov = frame.copy()
            cv2.rectangle(ov, (0, 0), (w, 72), C_BG, -1)
            cv2.addWeighted(ov, 0.65, frame, 0.35, 0, frame)

            cv2.putText(frame, "Actividad 4 - Control por Gestos",
                        (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, C_ACCENT, 2, cv2.LINE_AA)

            if gesture and gesture in GESTURE_INFO:
                lbl, _, col = GESTURE_INFO[gesture]
                cv2.putText(frame, f"Gesto: {lbl}",
                            (10, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2, cv2.LINE_AA)
            else:
                cv2.putText(frame, "Gesto: (ninguno reconocido)",
                            (10, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.6, C_NONE, 1, cv2.LINE_AA)

            if current_cmd:
                lbl, col = current_cmd
                cv2.rectangle(frame, (0, h - 40), (w, h), C_BG, -1)
                cv2.putText(frame, f"Ultimo CMD: {lbl}",
                            (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 2, cv2.LINE_AA)

            st = SERIAL_PORT if ser else "SIN SERIAL"
            sc = C_OK if ser else (0, 100, 255)
            cv2.putText(frame, st, (w - 140, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, sc, 1, cv2.LINE_AA)

            cv2.imshow("Actividad 4 - Gesture Control", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("[INFO] Cerrando...")
                break

    cap.release()
    cv2.destroyAllWindows()
    if ser:
        ser.close()
    print("[INFO] Programa finalizado.")


if __name__ == "__main__":
    main()
