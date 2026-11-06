/*
 * BMO Robot Body Controller Firmware - ESP32-C3 Mini (3.3V Logic)
 *
 * Features:
 *  - Controls up to 4 SG90 micro servos (Left Arm, Right Arm, Neck Pan, Neck Tilt)
 *    using ESP32Servo (or optional direct LEDC 50 Hz PWM fallback).
 *  - Safe angle clamping: Arms [0..150 deg], Neck Pan & Tilt [45..135 deg].
 *  - Staggered soft-attach at boot to prevent 5V brownout / current spikes.
 *  - Non-blocking `millis()` state machine for gestures:
 *      rest, wave, nod, shake, think, happy, excited
 *    Every gesture automatically returns to `rest` when finished.
 *  - Wi-Fi HTTP Server on port 80:
 *      GET  /         -> JSON status, IP, active gesture, current servo angles
 *      POST /gesture  -> JSON {"name": "wave"} triggers a gesture
 *      POST /servo    -> JSON {"left_arm":90,"right_arm":90,"neck_pan":90,"neck_tilt":90}
 *                        for raw calibration angles
 *  - Experimental USB OTG Serial fallback (115200 baud):
 *      Accepts line commands: `GESTURE <name>`, `SERVO <L> <R> <PAN> <TILT>`, `STATUS`
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

#if __has_include("secrets.h")
  #include "secrets.h"
#else
  #error "Missing secrets.h! Copy firmware/esp32_c3_servos/secrets.h.example to secrets.h and set WIFI_SSID and WIFI_PASSWORD."
#endif

// ============================================================================
// 1. GPIO PIN DEFINITIONS (VERIFY AGAINST YOUR EXACT ESP32-C3 MINI BOARD!)
//    IMPORTANT: Avoid ESP32-C3 strapping pins GPIO2, GPIO8, and GPIO9!
// ============================================================================
#define LEFT_ARM   0
#define RIGHT_ARM  1
#define NECK_PAN   3
#define NECK_TILT  4

// ============================================================================
// 2. SAFE SERVO ANGLE LIMITS & REST POSITIONS
// ============================================================================
#define ARM_MIN_ANGLE   0
#define ARM_MAX_ANGLE   150
#define NECK_MIN_ANGLE  45
#define NECK_MAX_ANGLE  135

#define REST_LEFT_ARM   30
#define REST_RIGHT_ARM  30
#define REST_NECK_PAN   90
#define REST_NECK_TILT  90

#define SERVO_MIN_US    500
#define SERVO_MAX_US    2400

// ============================================================================
// 3. NON-BLOCKING GESTURE KEYFRAME DEFINITIONS
// ============================================================================
struct Keyframe {
  int leftArm;
  int rightArm;
  int neckPan;
  int neckTilt;
  unsigned long durationMs;
};

static const Keyframe SEQ_REST[] = {
  {REST_LEFT_ARM, REST_RIGHT_ARM, REST_NECK_PAN, REST_NECK_TILT, 250}
};

static const Keyframe SEQ_WAVE[] = {
  {REST_LEFT_ARM, 135, 90, 85, 280},
  {REST_LEFT_ARM,  95, 90, 85, 220},
  {REST_LEFT_ARM, 140, 90, 85, 220},
  {REST_LEFT_ARM,  95, 90, 85, 220},
  {REST_LEFT_ARM, 135, 90, 85, 240},
  {REST_LEFT_ARM, REST_RIGHT_ARM, REST_NECK_PAN, REST_NECK_TILT, 300}
};

static const Keyframe SEQ_NOD[] = {
  {REST_LEFT_ARM, REST_RIGHT_ARM, 90,  65, 240},
  {REST_LEFT_ARM, REST_RIGHT_ARM, 90, 110, 240},
  {REST_LEFT_ARM, REST_RIGHT_ARM, 90,  68, 240},
  {REST_LEFT_ARM, REST_RIGHT_ARM, REST_NECK_PAN, REST_NECK_TILT, 260}
};

static const Keyframe SEQ_SHAKE[] = {
  {20, 20,  60, 95, 240},
  {20, 20, 120, 95, 260},
  {20, 20,  65, 95, 260},
  {20, 20, 115, 95, 240},
  {REST_LEFT_ARM, REST_RIGHT_ARM, REST_NECK_PAN, REST_NECK_TILT, 280}
};

static const Keyframe SEQ_THINK[] = {
  {110, REST_RIGHT_ARM, 110, 75, 450},
  {115, REST_RIGHT_ARM, 105, 72, 450},
  {REST_LEFT_ARM, REST_RIGHT_ARM, REST_NECK_PAN, REST_NECK_TILT, 320}
};

static const Keyframe SEQ_HAPPY[] = {
  {120, 120,  80, 80, 260},
  { 60,  60, 100, 85, 240},
  {120, 120,  90, 80, 260},
  {REST_LEFT_ARM, REST_RIGHT_ARM, REST_NECK_PAN, REST_NECK_TILT, 300}
};

static const Keyframe SEQ_EXCITED[] = {
  {145, 145,  75,  70, 200},
  { 70,  70, 105, 100, 180},
  {145, 145,  75,  70, 200},
  { 70,  70, 105, 100, 180},
  {145, 145,  90,  75, 220},
  {REST_LEFT_ARM, REST_RIGHT_ARM, REST_NECK_PAN, REST_NECK_TILT, 300}
};

// ============================================================================
// 4. GLOBAL STATE (SERVOS, WEB SERVER, GESTURE PLAYER)
// ============================================================================
Servo servoLeftArm;
Servo servoRightArm;
Servo servoNeckPan;
Servo servoNeckTilt;

WebServer server(80);

int curLeftArm  = REST_LEFT_ARM;
int curRightArm = REST_RIGHT_ARM;
int curNeckPan  = REST_NECK_PAN;
int curNeckTilt = REST_NECK_TILT;

String activeGestureName = "rest";
const Keyframe* activeSequence = nullptr;
size_t activeSequenceLen = 0;
size_t activeStepIndex = 0;
unsigned long stepStartMillis = 0;

String serialBuffer = "";

// ============================================================================
// 5. HELPER FUNCTIONS: CLAMPING & SERVO WRITING
// ============================================================================
int clampArmAngle(int angle) {
  if (angle < ARM_MIN_ANGLE) return ARM_MIN_ANGLE;
  if (angle > ARM_MAX_ANGLE) return ARM_MAX_ANGLE;
  return angle;
}

int clampNeckAngle(int angle) {
  if (angle < NECK_MIN_ANGLE) return NECK_MIN_ANGLE;
  if (angle > NECK_MAX_ANGLE) return NECK_MAX_ANGLE;
  return angle;
}

void applyServoAngles(int leftArm, int rightArm, int neckPan, int neckTilt) {
  curLeftArm  = clampArmAngle(leftArm);
  curRightArm = clampArmAngle(rightArm);
  curNeckPan  = clampNeckAngle(neckPan);
  curNeckTilt = clampNeckAngle(neckTilt);

  servoLeftArm.write(curLeftArm);
  servoRightArm.write(curRightArm);
  servoNeckPan.write(curNeckPan);
  servoNeckTilt.write(curNeckTilt);
}

// Attach servos one by one at boot to avoid an inrush current spike
void attachServosSlowly() {
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  servoLeftArm.setPeriodHertz(50);
  servoLeftArm.write(REST_LEFT_ARM);
  servoLeftArm.attach(LEFT_ARM, SERVO_MIN_US, SERVO_MAX_US);
  delay(180);

  servoRightArm.setPeriodHertz(50);
  servoRightArm.write(REST_RIGHT_ARM);
  servoRightArm.attach(RIGHT_ARM, SERVO_MIN_US, SERVO_MAX_US);
  delay(180);

  servoNeckPan.setPeriodHertz(50);
  servoNeckPan.write(REST_NECK_PAN);
  servoNeckPan.attach(NECK_PAN, SERVO_MIN_US, SERVO_MAX_US);
  delay(180);

  servoNeckTilt.setPeriodHertz(50);
  servoNeckTilt.write(REST_NECK_TILT);
  servoNeckTilt.attach(NECK_TILT, SERVO_MIN_US, SERVO_MAX_US);
  delay(180);
}

bool startGesture(const String& gestureName) {
  String name = gestureName;
  name.trim();
  name.toLowerCase();

  if (name == "rest") {
    activeSequence = SEQ_REST;
    activeSequenceLen = sizeof(SEQ_REST) / sizeof(Keyframe);
  } else if (name == "wave") {
    activeSequence = SEQ_WAVE;
    activeSequenceLen = sizeof(SEQ_WAVE) / sizeof(Keyframe);
  } else if (name == "nod") {
    activeSequence = SEQ_NOD;
    activeSequenceLen = sizeof(SEQ_NOD) / sizeof(Keyframe);
  } else if (name == "shake") {
    activeSequence = SEQ_SHAKE;
    activeSequenceLen = sizeof(SEQ_SHAKE) / sizeof(Keyframe);
  } else if (name == "think") {
    activeSequence = SEQ_THINK;
    activeSequenceLen = sizeof(SEQ_THINK) / sizeof(Keyframe);
  } else if (name == "happy") {
    activeSequence = SEQ_HAPPY;
    activeSequenceLen = sizeof(SEQ_HAPPY) / sizeof(Keyframe);
  } else if (name == "excited") {
    activeSequence = SEQ_EXCITED;
    activeSequenceLen = sizeof(SEQ_EXCITED) / sizeof(Keyframe);
  } else {
    return false;
  }

  activeGestureName = name;
  activeStepIndex = 0;
  stepStartMillis = millis();

  const Keyframe& first = activeSequence[0];
  applyServoAngles(first.leftArm, first.rightArm, first.neckPan, first.neckTilt);
  return true;
}

void updateGestureStateMachine() {
  if (activeSequence == nullptr || activeSequenceLen == 0) {
    return;
  }

  unsigned long now = millis();
  unsigned long elapsed = now - stepStartMillis;
  if (elapsed < activeSequence[activeStepIndex].durationMs) {
    return;
  }

  activeStepIndex++;
  if (activeStepIndex >= activeSequenceLen) {
    // Sequence complete: always ensure we settle in `rest`
    applyServoAngles(REST_LEFT_ARM, REST_RIGHT_ARM, REST_NECK_PAN, REST_NECK_TILT);
    activeSequence = nullptr;
    activeSequenceLen = 0;
    activeStepIndex = 0;
    activeGestureName = "rest";
    return;
  }

  stepStartMillis = now;
  const Keyframe& step = activeSequence[activeStepIndex];
  applyServoAngles(step.leftArm, step.rightArm, step.neckPan, step.neckTilt);
}

// ============================================================================
// 6. LIGHTWEIGHT JSON PARSING HELPERS (NO EXTERNAL JSON LIBRARY REQUIRED)
// ============================================================================
String extractJsonStringField(const String& body, const String& key) {
  String pattern = "\"" + key + "\"";
  int keyIdx = body.indexOf(pattern);
  if (keyIdx < 0) return "";
  int colonIdx = body.indexOf(':', keyIdx + pattern.length());
  if (colonIdx < 0) return "";
  int firstQuote = body.indexOf('"', colonIdx + 1);
  if (firstQuote < 0) return "";
  int secondQuote = body.indexOf('"', firstQuote + 1);
  if (secondQuote < 0) return "";
  return body.substring(firstQuote + 1, secondQuote);
}

int extractJsonIntField(const String& body, const String& key, int fallbackVal) {
  String pattern = "\"" + key + "\"";
  int keyIdx = body.indexOf(pattern);
  if (keyIdx < 0) return fallbackVal;
  int colonIdx = body.indexOf(':', keyIdx + pattern.length());
  if (colonIdx < 0) return fallbackVal;
  int pos = colonIdx + 1;
  while (pos < (int)body.length() && (body[pos] == ' ' || body[pos] == '\t')) {
    pos++;
  }
  String numStr = "";
  while (pos < (int)body.length() && (isDigit(body[pos]) || body[pos] == '-')) {
    numStr += body[pos];
    pos++;
  }
  if (numStr.length() == 0) return fallbackVal;
  return numStr.toInt();
}

String buildStatusJson() {
  String json = "{";
  json += "\"status\":\"ok\",";
  json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  json += "\"gesture\":\"" + activeGestureName + "\",";
  json += "\"angles\":{";
  json += "\"left_arm\":" + String(curLeftArm) + ",";
  json += "\"right_arm\":" + String(curRightArm) + ",";
  json += "\"neck_pan\":" + String(curNeckPan) + ",";
  json += "\"neck_tilt\":" + String(curNeckTilt);
  json += "}}";
  return json;
}

// ============================================================================
// 7. HTTP ENDPOINT HANDLERS: GET /, POST /gesture, POST /servo
// ============================================================================
void handleGetStatus() {
  server.send(200, "application/json", buildStatusJson());
}

void handlePostGesture() {
  String body = server.arg("plain");
  String gestureName = extractJsonStringField(body, "name");
  if (gestureName.length() == 0 && server.hasArg("name")) {
    gestureName = server.arg("name");
  }

  if (gestureName.length() == 0 || !startGesture(gestureName)) {
    server.send(
      400,
      "application/json",
      "{\"status\":\"error\",\"message\":\"Unknown or missing gesture name. Valid: rest, wave, nod, shake, think, happy, excited\"}"
    );
    return;
  }

  server.send(200, "application/json", buildStatusJson());
}

void handlePostServo() {
  String body = server.arg("plain");
  activeSequence = nullptr;
  activeSequenceLen = 0;
  activeGestureName = "manual";

  int nextLeft  = extractJsonIntField(body, "left_arm", curLeftArm);
  int nextRight = extractJsonIntField(body, "right_arm", curRightArm);
  int nextPan   = extractJsonIntField(body, "neck_pan", curNeckPan);
  int nextTilt  = extractJsonIntField(body, "neck_tilt", curNeckTilt);

  applyServoAngles(nextLeft, nextRight, nextPan, nextTilt);
  server.send(200, "application/json", buildStatusJson());
}

// ============================================================================
// 8. EXPERIMENTAL USB OTG SERIAL COMMAND HANDLER
// ============================================================================
void processSerialCommand(String line) {
  line.trim();
  if (line.length() == 0) return;

  String upper = line;
  upper.toUpperCase();

  if (upper == "STATUS") {
    Serial.println(buildStatusJson());
    return;
  }

  if (upper.startsWith("GESTURE ")) {
    String gName = line.substring(8);
    if (startGesture(gName)) {
      Serial.println("OK GESTURE " + activeGestureName);
    } else {
      Serial.println("ERR UNKNOWN_GESTURE");
    }
    return;
  }

  if (upper.startsWith("SERVO ")) {
    int l = curLeftArm, r = curRightArm, p = curNeckPan, t = curNeckTilt;
    if (sscanf(line.c_str() + 6, "%d %d %d %d", &l, &r, &p, &t) == 4) {
      activeSequence = nullptr;
      activeSequenceLen = 0;
      activeGestureName = "manual";
      applyServoAngles(l, r, p, t);
      Serial.println(buildStatusJson());
    } else {
      Serial.println("ERR USAGE: SERVO <left> <right> <pan> <tilt>");
    }
    return;
  }

  Serial.println("ERR UNKNOWN_COMMAND");
}

void pollSerialFallback() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (serialBuffer.length() > 0) {
        processSerialCommand(serialBuffer);
        serialBuffer = "";
      }
    } else if (serialBuffer.length() < 128) {
      serialBuffer += c;
    }
  }
}

// ============================================================================
// 9. ARDUINO SETUP & MAIN LOOP
// ============================================================================
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n[BMO ESP32-C3] Attaching servos slowly...");
  attachServosSlowly();

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("[BMO ESP32-C3] Connecting to Wi-Fi");

  unsigned long wifiStart = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - wifiStart) < 15000) {
    delay(250);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("[BMO ESP32-C3] Wi-Fi connected! IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("[BMO ESP32-C3] Wi-Fi timeout; serial fallback remains active.");
  }

  server.on("/", HTTP_GET, handleGetStatus);
  server.on("/gesture", HTTP_POST, handlePostGesture);
  server.on("/servo", HTTP_POST, handlePostServo);
  server.begin();
  Serial.println("[BMO ESP32-C3] HTTP server listening on port 80.");
}

void loop() {
  server.handleClient();
  updateGestureStateMachine();
  pollSerialFallback();
}
