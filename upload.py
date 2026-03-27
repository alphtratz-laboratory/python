import os
import hashlib
import traceback
from flask import Flask, render_template, request, jsonify
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 拡張子の定義
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic'}

def calculate_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_file_date(file_path):
    # splitextの結果から[1]（拡張子部分）だけを取り出して小文字化する
    ext = os.path.splitext(file_path)[1].lower()
    
    # 1. 画像ならExifを試す
    if ext in IMAGE_EXTENSIONS:
        try:
            with Image.open(file_path) as image:
                exif_data = image._getexif()
                if exif_data:
                    for tag, value in exif_data.items():
                        if TAGS.get(tag) == 'DateTimeOriginal':
                            # '2024:03:24 12:00:00' -> '2024-03-24'
                            val_str = str(value)
                            date_part = val_str.split(' ')[0]
                            return date_part.replace(':', '-')
        except Exception as e:
            print(f"Exif parse error: {e}")
    
    # 2. 動画、Exifなし、またはエラー時は「ファイルの更新日時」
    try:
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    except:
        return "Unknown"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('photo')
    if not file or file.filename == '':
        return jsonify({"status": "error", "message": "No file"}), 400

    filename = os.path.basename(file.filename)
    temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{filename}")
    
    try:
        file.save(temp_path)
        new_hash = calculate_hash(temp_path)
        date_str = get_file_date(temp_path)
        
        target_dir = os.path.join(UPLOAD_FOLDER, date_str)
        os.makedirs(target_dir, exist_ok=True)
        
        final_path = os.path.join(target_dir, filename)
        
        if os.path.exists(final_path):
            if calculate_hash(final_path) == new_hash:
                os.remove(temp_path)
                return jsonify({"status": "skipped"})
            else:
                name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(os.path.join(target_dir, f"{name}_{counter}{ext}")):
                    counter += 1
                final_path = os.path.join(target_dir, f"{name}_{counter}{ext}")

        os.replace(temp_path, final_path)
        return jsonify({"status": "success"})

    except Exception as e:
        traceback.print_exc()
        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
