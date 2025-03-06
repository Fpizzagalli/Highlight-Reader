import os
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import shutil
from datetime import datetime
import zipfile

app = Flask(__name__)
app.secret_key = "supersecretkey"
UPLOAD_FOLDER = "uploads"
DOWNLOAD_FOLDER = "downloads"
ALLOWED_EXTENSIONS = {"txt"}

# Ensure directories exist
for folder in [UPLOAD_FOLDER, DOWNLOAD_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_clippings(file_path):
    highlights = {}
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read().split("==========")
        for entry in content:
            entry = entry.strip()
            if not entry:
                continue
            lines = entry.splitlines()
            if len(lines) < 4:
                continue
            title_line = lines[0].strip()
            metadata = lines[1].strip()
            highlight = lines[-1].strip()
            title = title_line[:title_line.index("(")].strip() if "(" in title_line else title_line
            if title not in highlights:
                highlights[title] = []
            highlights[title].append({"metadata": metadata, "highlight": highlight})
    return highlights


def save_highlights_to_folder(highlights, output_dir):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    for title, entries in highlights.items():
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
        filename = os.path.join(output_dir, f"{safe_title}.txt")
        with open(filename, "w", encoding="utf-8") as file:
            file.write(f"Book: {title}\n")
            file.write(f"Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            file.write("Highlights:\n")
            file.write("-" * 50 + "\n")
            for entry in entries:
                file.write(f"{entry['metadata']}\n")
                file.write(f"{entry['highlight']}\n")
                file.write("-" * 50 + "\n")
    return output_dir


def create_zip(folder_path, zip_name):
    zip_path = os.path.join(DOWNLOAD_FOLDER, zip_name)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))
    return zip_path


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No file selected")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            highlights = parse_clippings(file_path)
            if not highlights:
                flash("No valid highlights found in the file.")
                os.remove(file_path)
                return redirect(request.url)

            # Store highlights in session or pass directly to template
            os.remove(file_path)  # Clean up uploaded file
            return render_template("results.html", highlights=highlights)
        else:
            flash("Invalid file type. Please upload a .txt file.")
            return redirect(request.url)
    return render_template("index.html")


@app.route("/download_zip", methods=["POST"])
def download_zip():
    highlights = request.form.to_dict(flat=False)  # Reconstruct highlights from form data
    processed_highlights = {}
    for title in highlights:
        if title.startswith("title_"):
            clean_title = title.replace("title_", "")
            processed_highlights[clean_title] = []
            for i in range(len(highlights[f"metadata_{clean_title}"])):
                processed_highlights[clean_title].append({
                    "metadata": highlights[f"metadata_{clean_title}"][i],
                    "highlight": highlights[f"highlight_{clean_title}"][i]
                })

    temp_dir = "temp_highlights"
    save_highlights_to_folder(processed_highlights, temp_dir)
    zip_name = f"kindle_highlights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = create_zip(temp_dir, zip_name)

    shutil.rmtree(temp_dir)
    return send_file(zip_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)