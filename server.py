#!/usr/bin/env python3
"""
Background removal REST API using rembg.
Run with: python server.py

Endpoints:
  GET  /health
  POST /remove-background
    Body: {
      "image_url": "https://...",      # or "image_data": "base64..."
      "model": "birefnet-general",     # optional, default birefnet-general
      "alpha_matting": true,           # optional, default true
      "alpha_matting_foreground_threshold": 270,  # optional, default 270
      "alpha_matting_background_threshold": 20,   # optional, default 20
      "alpha_matting_erode_size": 10,             # optional, default 10
      "post_process_mask": true        # optional, default true
    }
    Returns: { "success": true, "image_data": "base64...", "content_type": "image/png", "source": "rembg", "model": "..." }
"""

import os
import io
import base64
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from rembg import remove, new_session

app = Flask(__name__)
CORS(app)

# Pre-load default model at startup
DEFAULT_MODEL = "isnet-general-use"
print(f"Loading rembg model '{DEFAULT_MODEL}' (first run downloads model)...")
sessions = {}
sessions[DEFAULT_MODEL] = new_session(DEFAULT_MODEL)
print("Model loaded!")


def get_session(model_name):
    """Get or create a rembg session for the given model."""
    if model_name not in sessions:
        print(f"Loading model '{model_name}'...")
        sessions[model_name] = new_session(model_name)
        print(f"Model '{model_name}' loaded!")
    return sessions[model_name]


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "service": "withoutbg-server",
        "engine": "rembg",
        "default_model": DEFAULT_MODEL,
        "available_models": [
            "isnet-general-use",
            "u2net",
            "u2netp",
            "silueta"
        ]
    })


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

        # Parse optional parameters
        model_name = data.get('model', DEFAULT_MODEL)
        alpha_matting = data.get('alpha_matting', True)
        fg_threshold = data.get('alpha_matting_foreground_threshold', 270)
        bg_threshold = data.get('alpha_matting_background_threshold', 20)
        erode_size = data.get('alpha_matting_erode_size', 10)
        post_process = data.get('post_process_mask', True)

        # Download image from URL or decode base64
        if image_url:
            print(f"Downloading image from: {image_url[:80]}...")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            input_data = response.content
        else:
            print("Processing base64 image...")
            input_data = base64.b64decode(image_base64)

        # Get model session
        session = get_session(model_name)

        # Remove background with rembg
        print(f"Removing background (model={model_name}, alpha_matting={alpha_matting})...")
        result_bytes = remove(
            input_data,
            session=session,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=fg_threshold,
            alpha_matting_background_threshold=bg_threshold,
            alpha_matting_erode_size=erode_size,
            post_process_mask=post_process
        )

        # Encode result as base64
        image_data = base64.b64encode(result_bytes).decode('utf-8')

        print(f"Background removed successfully (model={model_name})!")
        return jsonify({
            "success": True,
            "image_data": image_data,
            "content_type": "image/png",
            "source": "rembg",
            "model": model_name
        })

    except requests.exceptions.RequestException as e:
        print(f"Download error: {e}")
        return jsonify({"success": False, "error": f"Failed to download image: {str(e)}"}), 400
    except Exception as e:
        print(f"Processing error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting rembg server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
