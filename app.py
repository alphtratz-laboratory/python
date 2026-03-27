import os
from flask import Flask, request, render_template_string
from google.cloud import storage  # GCS用ライブラリ

app = Flask(__name__)

# 環境変数から設定を読み込む（Cloud Run環境なら自動でセットされることが多い）
BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME')
LOCAL_UPLOAD_FOLDER = './uploads'

# ローカル用のフォルダ作成
if not BUCKET_NAME and not os.path.exists(LOCAL_UPLOAD_FOLDER):
    os.makedirs(LOCAL_UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template_string('''
        <h1>ファイルアップロード</h1>
        <form method="post" action="/upload" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="アップロード">
        </form>
    ''')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file or file.filename == '':
        return 'ファイルがありません'

    # --- 保存先の分岐 ---
    if BUCKET_NAME:
        # 【本番環境】GCSに保存
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(file.filename)
        blob.upload_from_file(file)
        return f'GCSに保存完了: gs://{BUCKET_NAME}/{file.filename}'
    else:
        # 【開発環境】ローカルフォルダに保存
        path = os.path.join(LOCAL_UPLOAD_FOLDER, file.filename)
        file.save(path)
        return f'ローカルに保存完了: {path}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
