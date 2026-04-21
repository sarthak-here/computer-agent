"""
Phase 10: UI Element Detection
Detects buttons, input fields, and interactive elements using OpenCV.
Falls back to YOLO (ultralytics) if a trained model is present.
"""
from __future__ import annotations
import numpy as np
from PIL import Image


def detect_ui_elements(img: Image.Image) -> list[dict]:
    """
    Detect interactive UI elements in a screenshot.
    Returns list of dicts: {type, x, y, w, h, cx, cy}
    """
    try:
        return _detect_yolo(img)
    except Exception:
        pass
    try:
        return _detect_opencv(img)
    except ImportError:
        return []


def _detect_opencv(img: Image.Image) -> list[dict]:
    import cv2

    arr = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    elements = []
    min_area = 400
    max_area = img.width * img.height * 0.3

    for contour in contours:
        area = cv2.contourArea(contour)
        if not (min_area < area < max_area):
            continue
        x, y, w, h = cv2.boundingRect(contour)
        aspect = w / h if h > 0 else 0
        if 0.3 < aspect < 8 and 15 < h < 60:
            etype = "button" if aspect > 1.5 else "input"
        elif aspect > 8:
            etype = "toolbar"
        else:
            etype = "panel"
        elements.append({"type": etype, "x": x, "y": y, "w": w, "h": h,
                          "cx": x + w // 2, "cy": y + h // 2})

    elements.sort(key=lambda e: (e["y"] // 50, e["x"]))
    return elements[:30]


def _detect_yolo(img: Image.Image) -> list[dict]:
    import os
    from ultralytics import YOLO

    model_path = os.path.join(os.path.dirname(__file__), "models", "yolo_ui.pt")
    if not os.path.exists(model_path):
        raise FileNotFoundError("YOLO UI model not found at models/yolo_ui.pt")

    model = YOLO(model_path)
    results = model(img, verbose=False)
    elements = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            elements.append({
                "type": model.names[cls],
                "x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1,
                "cx": (x1 + x2) // 2, "cy": (y1 + y2) // 2,
                "conf": float(box.conf[0]),
            })
    return elements


def annotate_image(img: Image.Image, elements: list[dict]) -> Image.Image:
    """Draw bounding boxes on the image for visualization."""
    try:
        import cv2
        arr = np.array(img.convert("RGB"))
        colors = {"button": (0, 255, 0), "input": (255, 165, 0),
                  "toolbar": (0, 0, 255), "panel": (128, 128, 128)}
        for el in elements:
            color = colors.get(el["type"], (255, 0, 0))
            cv2.rectangle(arr, (el["x"], el["y"]),
                          (el["x"] + el["w"], el["y"] + el["h"]), color, 2)
            cv2.putText(arr, el["type"], (el["x"], el["y"] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        return Image.fromarray(arr)
    except ImportError:
        return img


def elements_to_context(elements: list[dict]) -> str:
    """Format detected elements as LLM-readable context."""
    if not elements:
        return ""
    lines = ["\nDetected UI elements (prefer these coordinates for clicks):"]
    for i, el in enumerate(elements[:20]):
        lines.append(
            f"  [{i+1}] {el['type']} at ({el['cx']}, {el['cy']}) size {el['w']}x{el['h']}"
        )
    return "\n".join(lines)
