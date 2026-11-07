# BMO Robot — Mechanical Dimensions Reference for Blender CAD

Use these reference measurements and printing tolerances when modeling BMO's teal PLA shell in **Blender**. Always verify your physical phone and servos with calipers before slicing the final print.

---

## 1. Samsung Galaxy A07 (Vertical / Portrait Mount)

| Feature | Nominal Dimension | Recommended CAD Slot / Cutout (with PLA Tolerance) | Notes |
|---|---:|---:|---|
| **Phone Height** | `167.3 mm` | `169.0 mm` internal slot height | Leave extra room at the bottom for the right-angle USB-C charging cable (`+18 mm` channel) |
| **Phone Width** | `77.3 mm` | `78.8 mm` (`+0.75 mm` per side) | Allows smooth vertical slide-in without scratching the phone frame |
| **Phone Thickness** | `8.0 mm` (`~9.6 mm` at camera bump) | `10.5 mm` channel depth | Add a stepped recess on the back wall of the phone cradle to clear the rear camera bump |
| **Front Bezel Window (Screen Cutout)** | `152.0 × 68.0 mm` active display | `148.0 × 66.0 mm` rounded rectangle (`R = 8 mm`) | Overlaps the phone's black bezel by ~1–2 mm on all sides to hold the phone securely behind the front wall |
| **Bottom USB-C, 3.5 mm Mic Jack & Speaker Channel** | Bottom edge ports | `36.0 × 14.0 mm` bottom slot + front acoustic vents | Leave clearance for the external microphone plug/adapter alongside the USB-C charging cable, plus a forward sound channel for the speaker |
| **External Microphone Clip / Front Port** | Top or front bezel | `Ø 8.0 – 10.0 mm` pass-through hole | Allows routing the external mic capsule to the front of BMO's shell for clear voice pickup |

---

## 2. Exterior ZMO Proportions & 3D Printing Tips

- **Classic BMO Box Proportions**: Approximately **Width : Height : Depth = 1 : 1.45 : 0.72**
  - Suggested outer shell size around the Galaxy A07: **`116 mm (W) × 195 mm (H) × 90 mm (D)`**.
- **Wall Thickness**: **`2.4 mm` to `3.0 mm`** (6–7 perimeters with a 0.4 mm nozzle) so the arm servo mounts don't flex during `wave` or `excited` gestures.
- **Split for Printing**:
  - **Front Bezel + Main Body**: Print face-down on a textured or smooth PEI bed for a clean front surface with zero supports on the screen cutout.
  - **Removable Back Door**: Attach with 4× M3 screws or 6×3 mm neodymium magnets so you can slide the Galaxy A07 in/out easily.
