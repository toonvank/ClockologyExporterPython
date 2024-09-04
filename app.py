from io import BytesIO
from os import remove, linesep
from PIL import Image

from flask import Flask, request, jsonify, render_template
from biplist import readPlist, writePlist, InvalidPlistException
import base64
import os
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
            try:
                # Find the index of the object containing 'assetData'
                asset_data_index = full_plist["$objects"].index('assetData')

                files = []

                # Loop through the objects starting right after 'assetData'
                i = asset_data_index + 1
                while i < len(full_plist["$objects"]):
                    try:
                        # Skip if the current object is a dictionary (dict)
                        if isinstance(full_plist["$objects"][i], dict):
                            i += 1
                            continue
                        if isinstance(full_plist["$objects"][i], str):
                            i += 1
                            continue

                        # Get the file data
                        file_data = full_plist["$objects"][i]

                        # Check the next item in the list for the file name
                        file_name = None
                        if i + 1 < len(full_plist["$objects"]):
                            if not isinstance(full_plist["$objects"][i + 1],
                                              dict):  # Ensure the next item is not a dict
                                file_name = full_plist["$objects"][i + 1]

                        # Write the file data to a temporary file
                        with open('data_temp.txt', 'wb') as f:
                            f.write(file_data)

                        # Read the binary data
                        with open('data_temp.txt', 'rb') as f:
                            data = f.read()

                        # Base64 encode the binary data directly without decoding to UTF-8
                        data_base64 = base64.b64encode(data).decode('utf-8')

                        # Determine file type, if no name is found set it to 'unknown/unknown'
                        if file_name:
                            file_type = os.path.splitext(file_name)[1][1:]  # Get extension without the dot
                        else:
                            file_type = 'png'

                        # Create the file info dictionary
                        file_info = {
                            'file_type': file_type,
                            'content': data_base64
                        }

                        # Append the file info to the files list
                        files.append(file_info)

                        # Move to the next file data (skip the current file name if present)
                        i += 2 if file_name else 1

                    except Exception as e:
                        # If an error occurs, stop processing further files and break out of the loop
                        print(f"An error occurred while processing file at index {i}: {e}")
                        break

                remove('data_temp.txt')
                remove('data.txt')
                return jsonify({'files': files})

            except Exception as e:
                # If the initial setup fails, return an error message
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
            file_info = getFileType(file_data)
            files.append(file_info)
        except Exception as e:
            # Handle the error and log the detected file type or error message
            file_info = {
                'file_type': 'error',
                'content': str(e)
            }
            files.append(file_info)

    return files

def getFileType(file_data):
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

    return file_info

if __name__ == '__main__':
    app.run(debug=True)