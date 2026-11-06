# BMO Robot — ESP32-C3 Mini to SG90 Servo Wiring Guide

---

## 1. Pin Mapping (ESP32-C3 Mini)

Verify the silkscreen labels on your exact ESP32-C3 Mini / SuperMini board before wiring.

| Servo Function | ESP32-C3 Pin (`#define`) | SG90 Wire Color | Safe Angle Clamp |
|---|---|---|---|
| **Left Arm** | `GPIO0` (`LEFT_ARM`) | Orange / Yellow (Signal) | `0°` to `150°` (Rest: `30°`) |
| **Right Arm** | `GPIO1` (`RIGHT_ARM`) | Orange / Yellow (Signal) | `0°` to `150°` (Rest: `30°`) |
| **Neck Pan** *(optional)* | `GPIO3` (`NECK_PAN`) | Orange / Yellow (Signal) | `45°` to `135°` (Rest: `90°`) |
| **Neck Tilt** *(optional)* | `GPIO4` (`NECK_TILT`) | Orange / Yellow (Signal) | `45°` to `135°` (Rest: `90°`) |

> **CRITICAL — Avoid Strapping Pins (`GPIO2`, `GPIO8`, `GPIO9`):**
> On the ESP32-C3, `GPIO2`, `GPIO8`, and `GPIO9` are hardware strapping pins that control bootloader / flash mode at reset. Connecting servo signal lines or pull-loads to `GPIO2`, `GPIO8`, or `GPIO9` can prevent the board from booting or flashing. Keep them free.

---

## 2. Power & Ground Wiring

SG90 servos require **4.8 V – 6.0 V** power (`V+`) and can draw **500 mA – 700 mA each** on startup or stall, while the ESP32-C3 uses **3.3 V logic** on its GPIO pins. Good news: SG90 servos reliably read a **3.3 V PWM signal** even when powered from a **5 V supply**.

```text
  [External 5V 2A-3A Supply]
        |              |
       +5V            GND
        |              |
        +---[470uF]----+------------------------------+
        |   Capacitor  |                              |
        |              | (COMMON GROUND IS MANDATORY) |
        |              +---------------+              |
        |                              |              |
        |                         [ESP32-C3]          |
        |                            GND              |
        |                            GPIO0 ---------> Left Arm SG90  (Signal - Orange)
        |                            GPIO1 ---------> Right Arm SG90 (Signal - Orange)
        |                            GPIO3 ---------> Neck Pan SG90  (Signal - Orange)
        |                            GPIO4 ---------> Neck Tilt SG90 (Signal - Orange)
        |                                             |
        +-------------------------------------------> All 4 SG90 Red Wires (V+ / 5V)
                                                      All 4 SG90 Brown Wires (GND)
```

### Key Power Rules
1. **Common Ground**: Always connect the **GND** of your external 5 V servo power supply to the **GND** pin of the ESP32-C3 Mini. Without a shared ground, the 3.3 V PWM signal has no reference and the servos will jitter wildly.
2. **Never use the ESP32-C3 `3V3` pin for servo power**: The onboard 3.3 V regulator cannot supply servo motor current and will brown out or damage the board.
3. **Decoupling Capacitor**: Place a **470 µF to 1000 µF (10 V or 16 V)** electrolytic capacitor across the `+5V` and `GND` rails on the servo power bus (observe polarity: negative stripe to `GND`).
4. **Soft Boot Attach**: The firmware (`esp32_c3_servos.ino`) attaches the 4 servos one at a time with a 180 ms stagger at startup to minimize inrush current.

---

## 3. Calibration Before Mounting Servo Horns

Before screwing the plastic servo horns onto BMO's arms or neck:
1. Power on the ESP32-C3 and let it move all servos to their `rest` angles (`LEFT_ARM=30°`, `RIGHT_ARM=30°`, `NECK_PAN=90°`, `NECK_TILT=90°`).
2. Press the plastic horns onto the splines so that:
   - Both arms point comfortably down along BMO's sides at `30°` (so raising to `135°–145°` waves upward without hitting the shell).
   - Neck pan looks straight ahead at `90°` and neck tilt is level at `90°`.
3. Test raw angles gently using `POST http://<ESP32_IP>/servo` before fastening the final M2 screws.
