import cv2
import numpy as np
import tensorflow as tf
import serial
import time
from PIL import ImageFont, ImageDraw, Image

# ================= CẤU HÌNH HỆ THỐNG =================
ARDUINO_PORT = 'COM4'
BAUD_RATE = 9600
MODEL_PATH = 'C:/Users/ACER/Desktop/python/phanloai.h5'
FONT_PATH = "arial.ttf"
FONT_SIZE = 32
CONFIDENCE_THRESHOLD = 0.8

# Màu sắc giao diện
COLOR_PACKAGED = (50, 50, 255)
COLOR_FRESH = (50, 255, 50)
COLOR_UNCERTAIN = (0, 255, 255)
COLOR_BG = (30, 30, 30)
COLOR_TEXT = (240, 240, 240)

# ================= GỬI TÍN HIỆU ARDUINO =================
def send_to_arduino(arduino, signal):
    if arduino and arduino.is_open:
        try:
            arduino.write(f"{signal}\n".encode('ascii'))
            print(f" Đã gửi tín hiệu: {signal}")
        except Exception as e:
            print(f"Lỗi gửi Arduino: {e}")

# ================= KẾT NỐI PHẦN CỨNG =================
def init_arduino():
    try:
        arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print("Đã kết nối Arduino!")
        return arduino
    except Exception as e:
        print(f"Lỗi Arduino: {e}")
        return None

def setup_camera():
    for cam_id in [1, 0]:
        cap = cv2.VideoCapture(cam_id)
        if cap.isOpened():
            print(f" Đang sử dụng camera index {cam_id}")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            return cap
    print("Không tìm thấy camera!")
    return None

# ================= TẢI MÔ HÌNH AI =================
def load_model():
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        return model, ["Hàng đóng gói", "Hàng tươi"], [COLOR_PACKAGED, COLOR_FRESH]
    except Exception as e:
        print(f"Lỗi tải model: {e}")
        return None, None, None

# ================= VẼ GIAO DIỆN =================
def draw_ui(frame, rect, label, color, confidence, font, captured_image=None, show_captured=False):
    x, y, w, h = rect
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], 80), COLOR_BG, -1)
    cv2.rectangle(overlay, (0, frame.shape[0]-60), (frame.shape[1], frame.shape[0]), COLOR_BG, -1)
    frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)

    text = f"KẾT QUẢ: {label} ({confidence*100:.1f}%)" if confidence >= CONFIDENCE_THRESHOLD else "ĐANG PHÂN TÍCH..."

    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    draw.text((20, 20), text, font=font, fill=COLOR_TEXT)
    draw.text((20, frame.shape[0]-40), "HỆ THỐNG PHÂN LOẠI THÔNG MINH", font=font, fill=(200, 200, 200))

    # Hiển thị ảnh đã chụp nếu có
    if show_captured and captured_image is not None:
        thumbnail = cv2.resize(captured_image, (160, 120))
        x_offset = frame.shape[1] - thumbnail.shape[1] - 20
        y_offset = frame.shape[0] - thumbnail.shape[0] - 80
        img_pil.paste(Image.fromarray(cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)), (x_offset, y_offset))
        draw.text((x_offset, y_offset - 30), "Đã chụp!", font=font, fill=(255, 255, 255))

    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# ================= CHƯƠNG TRÌNH CHÍNH =================
def main():
    arduino = init_arduino()
    model, class_names, colors = load_model()
    cap = setup_camera()

    if None in [model, cap]:
        return

    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except:
        font = ImageFont.load_default()
        print(" Sử dụng font mặc định")

    cv2.namedWindow("Phân Loại Hàng Hóa", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Phân Loại Hàng Hóa", 800, 600)

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    rect = (int(frame_width*0.2), int(frame_height*0.2), int(frame_width*0.6), int(frame_height*0.6))

    last_class = None
    captured_image = None
    show_captured_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print(" Lỗi đọc frame từ camera")
            break

        x, y, w, h = rect
        roi = frame[y:y+h, x:x+w]
        img = cv2.resize(roi, (128, 128))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img / 255.0
        img = np.expand_dims(img, axis=0)

        predictions = model.predict(img, verbose=0)
        predicted_class = np.argmax(predictions)
        confidence = np.max(predictions)

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        green_mask = cv2.inRange(hsv, (36, 25, 25), (86, 255, 255))
        if np.sum(green_mask > 0) / (w * h) > 0.3:
            predicted_class = 1
            confidence = max(confidence, 0.95)

        label = class_names[predicted_class] if confidence >= CONFIDENCE_THRESHOLD else "Không chắc chắn"
        color = colors[predicted_class] if confidence >= CONFIDENCE_THRESHOLD else COLOR_UNCERTAIN
        show_captured = time.time() - show_captured_time < 2

        frame = draw_ui(frame, rect, label, color, confidence, font, captured_image, show_captured)
        cv2.imshow("Phân Loại Hàng Hóa", frame)

        key = cv2.waitKey(30)

        if key == 27 or cv2.getWindowProperty("Phân Loại Hàng Hóa", cv2.WND_PROP_VISIBLE) < 1:
            break

        elif key == 32:  # SPACE
            if confidence >= CONFIDENCE_THRESHOLD:
                send_to_arduino(arduino, predicted_class + 1)
                captured_image = roi.copy()
                show_captured_time = time.time()
                print(" Đã chụp ảnh và gửi tín hiệu")
            else:
                print(" Độ tin cậy thấp, không gửi tín hiệu.")

    cap.release()
    cv2.destroyAllWindows()
    if arduino: arduino.close()
    print(" Đã dừng chương trình")

if __name__ == "__main__":
    main()
