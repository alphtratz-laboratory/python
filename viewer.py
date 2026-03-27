import os
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic', '.webp'}

def get_archive_list():
    """存在する年月（YYYY-MM）のリストを取得"""
    if not os.path.exists(UPLOAD_FOLDER):
        return []
    # フォルダ名（YYYY-MM-DD）から YYYY-MM 部分だけ抜き出す
    dirs = [d[:7] for d in os.listdir(UPLOAD_FOLDER) if os.path.isdir(os.path.join(UPLOAD_FOLDER, d)) and len(d) >= 7]
    return sorted(list(set(dirs)), reverse=True)

@app.route('/')
@app.route('/archive/<month>')
def index(month=None):
    archive_list = get_archive_list()
    
    # 月が指定されていない場合は最新の月を表示
    if not month and archive_list:
        month = archive_list[0]
    
    data = {}
    if os.path.exists(UPLOAD_FOLDER) and month:
        # 指定された月（YYYY-MM）で始まるフォルダだけ抽出
        all_dirs = [d for d in os.listdir(UPLOAD_FOLDER) if os.path.isdir(os.path.join(UPLOAD_FOLDER, d))]
        target_dirs = sorted([d for d in all_dirs if d.startswith(month)], reverse=True)

        for date in target_dirs:
            files_in_date = []
            path = os.path.join(UPLOAD_FOLDER, date)
            for filename in sorted(os.listdir(path)):
                if filename.startswith('.'): continue
                ext = os.path.splitext(filename)[1].lower()
                files_in_date.append({
                    "name": filename,
                    "is_image": ext in IMAGE_EXTENSIONS
                })
            data[date] = files_in_date

    return render_template('viewer.html', data=data, archive_list=archive_list, current_month=month)

@app.route('/file/<date>/<filename>')
def serve_file(date, filename):
    return send_from_directory(os.path.join(UPLOAD_FOLDER, date), filename)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
