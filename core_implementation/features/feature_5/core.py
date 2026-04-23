import os
import cv2
import numpy as np
import pytesseract
import mss
import json

from utils.providers import call_llm

# --- CONFIGURATION ---
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD", r'C:\Program Files\Tesseract-OCR\tesseract.exe')

# --- CORE FUNCTIONS ---

def capture_screen():
    with mss.mss() as sct:
        # Monitor 1 capture
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img_np = np.array(screenshot)
        
        # Convert to Grayscale
        gray_image = cv2.cvtColor(img_np, cv2.COLOR_BGRA2GRAY)
        
        return gray_image

def extract_text_with_coords(image):
    try:
        if image is None: return None, None

        # Simple Threshold (Black & White) - Best for Text
        _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)
        full_text = " ".join([word for word in data['text'] if word.strip() != ""])
        
        return full_text, data
    except Exception as e:
        print(f"Vision Error: {e}")
        return None, None

def get_ai_answer(context_text):
    """Solve a quiz question using the shared LLM fallback chain."""
    prompt = f"""
Quiz Solver. 
TEXT: "{context_text}"
FORMAT (Strict JSON): {{"correct_option_text": "Answer Text", "confidence": "High"}}
"""
    try:
        result = call_llm(prompt=prompt, system="You are an expert quiz solver. Return only valid JSON.", ttl=30)
        if result.startswith("⚠️"):
            return {"error": result}
        clean_text = result.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except json.JSONDecodeError:
        return {"error": f"Could not parse AI response: {result[:200]}"}
    except Exception as e:
        return {"error": str(e)}

def find_coordinates_of_text(target_text, ocr_data):
    if not target_text: return None
    target_words = target_text.split()
    if not target_words: return None
    
    # Clean logic
    search_word = target_words[0].lower().strip().replace(".", "").replace(")", "").replace('"', "").replace("'", "")
    
    n_boxes = len(ocr_data['text'])
    for i in range(n_boxes):
        detected_word = ocr_data['text'][i].lower().strip().replace(".", "").replace(")", "").replace('"', "").replace("'", "")
        
        if search_word in detected_word and len(detected_word) > 1:
            x, y, w, h = (ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i])
            return (x + w // 2, y + h // 2)
            
    return None