#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

const int ledPinGreen = 13;
const int ledPinRed = 12;
const int buzzerPin = 6;

void setup() {
  pinMode(ledPinGreen, OUTPUT);
  pinMode(ledPinRed, OUTPUT);
  pinMode(buzzerPin, OUTPUT);

  Serial.begin(9600);
  while (!Serial);

  lcd.init();
  lcd.backlight();
  lcd.print("Arduino san sang");
  delay(2000);
  lcd.clear();
}

void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    data.trim(); // loại bỏ khoảng trắng và ký tự xuống dòng

    Serial.print("Nhan duoc: ");
    Serial.println(data);

    lcd.clear();
    digitalWrite(ledPinGreen, LOW);
    digitalWrite(ledPinRed, LOW);
    noTone(buzzerPin); // đảm bảo tắt buzzer trước

    if (data == "1") {
      lcd.print("Hang tuoi");

      delay(5000);  // Delay 5 giây trước khi xử lý

      digitalWrite(ledPinGreen, HIGH);
      tone(buzzerPin, 1000);
      delay(1000);
      noTone(buzzerPin);

      Serial.println("Bat den xanh - Hang tuoi");
    } else if (data == "2") {
      lcd.print("Hang dong goi");

      delay(5000);  // Delay 5 giây trước khi xử lý

      for (int i = 0; i < 3; i++) {
        digitalWrite(ledPinRed, HIGH);
        tone(buzzerPin, 1000);
        delay(300);
        digitalWrite(ledPinRed, LOW);
        noTone(buzzerPin);
        delay(300);
      }

      Serial.println("Nhay den do - Hang dong goi");
    } else {
      lcd.print("Du lieu sai");
      Serial.println("Du lieu khong hop le");
    }
  }
}
