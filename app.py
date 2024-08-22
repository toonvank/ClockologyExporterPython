from io import BytesIO
from os import remove, linesep
from PIL import Image

from flask import Flask, request, jsonify, render_template
from biplist import readPlist, writePlist, InvalidPlistException
import base64
import json
import io

import re

from importlib_metadata import files
from typing_extensions import dataclass_transform

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/clockface', methods=['POST'])
def clockface():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    file.save('file.plist')

    try:
        with open('file.plist', 'rb') as f:
            full_plist = readPlist(f)

        remove('file.plist')

        with open('data.txt', 'wb') as f:
            object = full_plist["$objects"][30]
            f.write(full_plist["$objects"][4])

        try:
            with open('data.txt', 'rb') as f:
                data = f.read()
                data = data.decode('utf-8')
                images = extract_images_from_base64(data)
        except Exception as e:
            data = full_plist["$objects"][5]
            data = data.decode('utf-8')
            images = extract_images_from_base64(data)

        image_strings = []
        for img in images:
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            image_strings.append(img_str)

        remove('data.txt')

        return jsonify({'images': image_strings})
    except Exception as e:
        return jsonify({'error': str(e)}), 400



def extract_images_from_base64(base64_data):
    # Define a pattern to match base64 image data
    image_pattern = re.compile(r'imageData":"(.*?)"')

    # Find all matches of the pattern in the base64 data
    matches = image_pattern.findall(base64_data)

    images = []
    for match in matches:
        # Decode the base64 data
        img_data = base64.b64decode(match)
        try:
            # Load image from bytes
            img = Image.open(BytesIO(img_data))
            images.append(img)
        except Exception as e:
            continue

    return images

if __name__ == '__main__':
    app.run(debug=True)