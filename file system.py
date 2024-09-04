import os
import shutil
import time
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, abort

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
@app.route('/browse/', defaults={'subpath': ''})
@app.route('/browse/<path:subpath>')
def browse_files(subpath=''):
    current_folder = os.path.join(UPLOAD_FOLDER, subpath)
    files = []
    if os.path.exists(current_folder):
        for item in os.listdir(current_folder):
            item_path = os.path.join(current_folder, item)
            files.append({
                "name": item,
                "path": os.path.join(subpath, item),
                "is_dir": os.path.isdir(item_path),
                "size": os.path.getsize(item_path) if not os.path.isdir(item_path) else None,
                "time": time.ctime(os.path.getmtime(item_path))
            })
    files = sorted(files, key=lambda x: (not x['is_dir'], x['name']))
    return render_template('browse.html', files=files, current_folder=subpath)

@app.route('/upload', methods=['POST'])
def handle_file_upload():
    if 'file' not in request.files:
        return "No file uploaded", 400

    for file in request.files.getlist('file'):
        if file.filename == '':
            continue  # 如果没有选择文件，则跳过
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        file.save(file_path)

    return redirect(url_for('browse_files'))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/preview/<path:filename>')
def preview_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return abort(404)
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext in ['.png', '.jpg', '.jpeg', '.gif']:
        return render_template('preview_image.html', filename=filename)
    elif file_ext in ['.txt']:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return render_template('preview_text.html', filename=filename, content=content)
    elif file_ext in ['.pdf']:
        return render_template('preview_pdf.html', filename=filename)
    else:
        return "不支持的文件格式", 400

@app.route('/delete/<path:filename>', methods=['POST'])
def delete_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
        return redirect(url_for('browse_files'))
    else:
        return f"File {filename} not found", 404

@app.route('/rename/<path:filename>', methods=['POST'])
def rename_file(filename):
    new_name = request.form['new_name']
    if not new_name:
        return "New name not provided", 400
    old_file_path = os.path.join(UPLOAD_FOLDER, filename)
    new_file_path = os.path.join(UPLOAD_FOLDER, os.path.dirname(filename), new_name)
    if os.path.exists(old_file_path):
        directory = os.path.dirname(new_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        os.rename(old_file_path, new_file_path)
        return redirect(url_for('browse_files'))
    else:
        return f"File {filename} not found", 404

@app.route('/search', methods=['GET'])
def search_file():
    query = request.args.get('q', '')
    matched_files = []
    for root, dirs, files in os.walk(UPLOAD_FOLDER):
        for f in files:
            if query.lower() in f.lower():
                relative_path = os.path.relpath(root, UPLOAD_FOLDER)
                matched_files.append({
                    "name": f,
                    "path": os.path.join(relative_path, f),
                    "size": os.path.getsize(os.path.join(root, f)),
                    "time": time.ctime(os.path.getmtime(os.path.join(root, f))),
                    "is_dir": False
                })
    return render_template('browse.html', files=matched_files, current_folder='')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
