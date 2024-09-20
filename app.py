import base64
import os
import re
from io import BytesIO
import filetype
from PIL import Image
from biplist import readPlist
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/clockface', methods=['POST'])
def clockface():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    try:
        full_plist = readPlist(request.files['file'])
        plistObjects = full_plist["$objects"][4]
        print(plistObjects)
        try:
            # Just a regular clock2 file
            files = extract_images_from_base64(plistObjects.decode('utf-8'))
        except Exception as e:
            # Clock2 file with different position
            files = extract_images_from_base64(full_plist["$objects"][5].decode('utf-8'))
        return jsonify({'files': files})

    except Exception as e:
        try:
            # Clock2 file with different position
            return jsonify({'files': extract_images_from_base64(full_plist["$objects"][3].decode('utf-8'))})

        except Exception as e:
            try:
                # Clock1 file
                return decodeClock1(full_plist)
            except Exception as e:
                return jsonify({'error': str(e)}), 400

def extract_images_from_base64(base64_data):
    files = []

    for match in re.compile(r'imageData":"(.*?)"').findall(base64_data):
        try:
            files.append(getFileType(base64.b64decode(match),None))
        except Exception as e:
            file_info = {
                'file_type': 'error',
                'content': str(e)
            }
            files.append(file_info)
    return files

def getFileType(file_data,file_name):
    kind = filetype.guess(file_data)
    if file_name:
        file_type = os.path.splitext(file_name)[1][1:]
    elif kind:
        file_type = kind.mime
    else:
        file_type = 'png'

    file_info = {
        'file_type': file_type,
        'content': base64.b64encode(file_data).decode('utf-8')
    }

    if file_type.startswith('image/'):
        buffered = BytesIO()
        Image.open(BytesIO(file_data)).save(buffered, format="PNG")
        file_info['content'] = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return file_info

def decodeClock1(full_plist):
    # Clock1 file
    asset_data_index = full_plist["$objects"].index('assetData')
    files = []
    i = asset_data_index + 1
    end = 0

    while i < len(full_plist["$objects"]):
        try:
            if end > 12:
                break
            if isinstance(full_plist["$objects"][i], dict):
                i += 1
                end += 1
                continue
            if isinstance(full_plist["$objects"][i], str):
                i += 1
                end += 1
                continue

            file_name = None
            if i + 1 < len(full_plist["$objects"]):
                if not isinstance(full_plist["$objects"][i + 1],
                                  dict):
                    file_name = full_plist["$objects"][i + 1]

            files.append(getFileType(full_plist["$objects"][i], file_name))

            i += 2 if file_name else 1

        except Exception as e:
            print(f"An error occurred while processing file at index {i}: {e}")
            break
    return jsonify({'files': files})

if __name__ == '__main__':
    app.run(port=5001, debug=True)