from io import BytesIO
from os import remove, linesep
from PIL import Image

from flask import Flask, request, jsonify, render_template
from biplist import readPlist, writePlist, InvalidPlistException
import base64
import json
import io

import re
import filetype

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
            f.write(full_plist["$objects"][4])

        try:
            with open('data.txt', 'rb') as f:
                data = f.read()
                data = data.decode('utf-8')
                files = extract_images_from_base64(data)
        except Exception as e:
            data = full_plist["$objects"][5]
            data = data.decode('utf-8')
            files = extract_images_from_base64(data)

        remove('data.txt')

        return jsonify({'files': files})
    except Exception as e:
        try:
            with open('data.txt', 'wb') as f:
                f.write(full_plist["$objects"][3])
            with open('data.txt', 'rb') as f:
                data = f.read()
                data = data.decode('utf-8')
                files = extract_images_from_base64(data)
            return jsonify({'files': files})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

def extract_images_from_base64(base64_data):
    # Define a pattern to match base64 image data
    image_pattern = re.compile(r'imageData":"(.*?)"')

    # Find all matches of the pattern in the base64 data
    matches = image_pattern.findall(base64_data)

    files = []
    for match in matches:
        # Decode the base64 data
        file_data = base64.b64decode(match)
        try:
            # Determine the file type using filetype library
            kind = filetype.guess(file_data)
            if kind:
                file_type = kind.mime
            else:
                file_type = 'unknown/unknown'

            # Prepare the response object
            file_info = {
                'file_type': file_type,
                'content': base64.b64encode(file_data).decode('utf-8')
            }

            # If the file is an image, convert it and include it in the response
            if file_type.startswith('image/'):
                img = Image.open(BytesIO(file_data))
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                file_info['content'] = img_str

            files.append(file_info)
        except Exception as e:
            # Handle the error and log the detected file type or error message
            file_info = {
                'file_type': 'error',
                'content': str(e)
            }
            files.append(file_info)

    return files


if __name__ == '__main__':
    app.run(debug=True)