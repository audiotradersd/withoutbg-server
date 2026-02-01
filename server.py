#!/usr/bin/env python3
"""
Simple REST API wrapper for withoutbg background removal.
Run with: python server.py
Requires: pip install withoutbg flask flask-cors requests pillow

Endpoints:
  POST /remove-background
    Body: { "image_url": "https://..." }
    Returns: { "success": true, "image_data": "base64...", "content_type": "image/png" }
"""

import os
import io
import base64
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from withoutbg import WithoutBG

app = Flask(__name__)
CORS(app)

# Initialize model once at startup (loads ~320MB model on first use)
print("Loading withoutbg model (first run downloads ~320MB)...")
model = WithoutBG.opensource()
print("Model loaded!")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "withoutbg-server"})

@app.route('/remove-background', methods=['POST'])
def remove_background():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON body provided"}), 400

        image_url = data.get('image_url')
        image_base64 = data.get('image_data')

        if not image_url and not image_base64:
            return jsonify({"success": False, "error": "image_url or image_data required"}), 400

        # Download image from URL or decode base64
        if image_url:
            print(f"Downloading image from: {image_url[:80]}...")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_bytes = io.BytesIO(response.content)
        else:
            print("Processing base64 image...")
            image_bytes = io.BytesIO(base64.b64decode(image_base64))

        # Remove background
        print("Removing background...")
        result = model.remove_background(image_bytes)

        # Convert to base64 PNG
        output_buffer = io.BytesIO()
        result.save(output_buffer, format='PNG')
        output_buffer.seek(0)

        image_data = base64.b64encode(output_buffer.read()).decode('utf-8')

        print("Background removed successfully!")
        return jsonify({
            "success": True,
            "image_data": image_data,
            "content_type": "image/png"
        })

    except requests.exceptions.RequestException as e:
        print(f"Download error: {e}")
        return jsonify({"success": False, "error": f"Failed to download image: {str(e)}"}), 400
    except Exception as e:
        print(f"Processing error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting withoutbg server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
