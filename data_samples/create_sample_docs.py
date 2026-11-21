"""
Synthetic Demo Document Generator
Creates realistic visual mock identity cards with bold watermark:
"DEMO / SIMULATION USE ONLY - NOT A REAL GOVERNMENT DOCUMENT"
"""

import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

def create_demo_id_card(
    full_name: str,
    id_number: str,
    dob: str,
    country: str,
    filename: str,
    tamper: bool = False
):
    width, height = 800, 500
    # Clean modern background
    img = Image.new("RGB", (width, height), color=(245, 248, 252))
    draw = ImageDraw.Draw(img)

    # Card header background
    draw.rectangle([0, 0, width, 90], fill=(24, 43, 73))
    
    # Gold decorative accent line
    draw.rectangle([0, 90, width, 98], fill=(212, 175, 55))

    # Watermark background pattern
    for y in range(120, height, 70):
        draw.text((30, y), "DEMO ONLY • SIMULATION • NOT REAL ID", fill=(225, 230, 238))

    # Header text
    draw.text((30, 20), "DEMO REPUBLIC OF CYBERIA", fill=(255, 255, 255))
    draw.text((30, 50), "SYNTHETIC IDENTITY VERIFICATION CARD", fill=(180, 205, 237))

    # Simulated Photo Box
    draw.rectangle([40, 130, 220, 360], fill=(210, 220, 235), outline=(24, 43, 73), width=2)
    draw.text((80, 230), "[ PHOTO ]", fill=(100, 120, 150))

    # Card Fields
    fields = [
        ("FULL NAME", full_name.upper()),
        ("NATIONAL ID NO", id_number),
        ("DATE OF BIRTH", dob),
        ("ISSUING STATE", country.upper()),
        ("STATUS", "DEMO CITIZEN - SIMULATION ONLY")
    ]

    y_pos = 135
    for label, val in fields:
        draw.text((260, y_pos), label, fill=(110, 120, 140))
        draw.text((260, y_pos + 22), val, fill=(15, 25, 45))
        y_pos += 60

    # Bottom footer notice
    draw.rectangle([0, height - 50, width, height], fill=(230, 235, 245))
    draw.text((30, height - 35), "EDUCATIONAL USE ONLY • SYNTHETIC DOCUMENT FOR INTERNSHIP AI TESTING", fill=(80, 95, 120))

    # Convert to OpenCV image format for optional tampering simulation
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    if tamper:
        # Simulate digital noise, compression artifacts, and spliced patch
        noise = np.random.normal(0, 18, cv_img.shape).astype(np.uint8)
        cv_img = cv2.add(cv_img, noise)
        # Add blur patch over the ID region
        patch = cv_img[240:310, 250:550]
        blurred_patch = cv2.GaussianBlur(patch, (21, 21), 0)
        cv_img[240:310, 250:550] = blurred_patch

    # Save
    out_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(out_dir, filename)
    cv2.imwrite(file_path, cv_img)
    print(f"Generated demo card: {file_path}")
    return file_path

if __name__ == "__main__":
    # 1. Matching valid pass sample
    create_demo_id_card(
        full_name="Johnathan Doe",
        id_number="SIM-9821-4471",
        dob="1990-05-14",
        country="Cyberia",
        filename="sample_id_john_doe_pass.png",
        tamper=False
    )

    # 2. Mismatched sample (Jane Smith data)
    create_demo_id_card(
        full_name="Jane Eleanor Smith",
        id_number="SIM-4422-9901",
        dob="1995-08-22",
        country="Cyberia",
        filename="sample_id_jane_smith_mismatch.png",
        tamper=False
    )

    # 3. Tampered sample
    create_demo_id_card(
        full_name="Robert Vance",
        id_number="SIM-7733-1122",
        dob="1982-12-01",
        country="Cyberia",
        filename="sample_id_robert_tampered.png",
        tamper=True
    )
