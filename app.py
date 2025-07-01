from flask import Flask, render_template_string, request, send_file
from PIL import Image
import os
import io
import zipfile

app = Flask(__name__)

MAX_SIZE_MB = 4.5
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

# HTML as string (no templates folder needed)
html_page = """<!DOCTYPE html>
<html>
<head>
    <title>Advanced Image Resizer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin-top: 100px;
            background-color: #f7f7f7;
        }
        .container {
            background: white;
            padding: 40px;
            margin: auto;
            width: 400px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 10px;
        }
        input[type="file"], input[type="number"], select {
            padding: 8px;
            width: 90%;
            margin: 5px 0;
        }
        button {
            padding: 10px 20px;
            background-color: #007bfc;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
    </style>
</head>
<body>
<div class="container">
    <h1>Image Resizer Tool</h1>
    <form method="POST" enctype="multipart/form-data">
        <label>Select images (multiple):</label><br>
        <input type="file" name="images" multiple required><br><br>

        <label>Custom Width:</label><br>
        <input type="number" name="width" value="250" required><br><br>

        <label>Custom Height:</label><br>
        <input type="number" name="height" value="250" required><br><br>

        <label>Output Format:</label><br>
        <select name="format">
            <option value="jpg">JPG</option>
            <option value="png">PNG</option>
        </select><br><br>

        <button type="submit">Resize & Download ZIP</button>
    </form>
</div>
</body>
</html>"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        width = int(request.form["width"])
        height = int(request.form["height"])
        format_option = request.form["format"].upper()
        files = request.files.getlist("images")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zipf:
            for file in files:
                if file.filename.endswith((".jpg", ".jpeg", ".png")):
                    file.seek(0, os.SEEK_END)
                    size = file.tell()
                    file.seek(0)

                    if size > MAX_SIZE_BYTES:
                        return f"File '{file.filename}' is too large! Limit: 4.5MB"

                    img = Image.open(file)
                    img = img.resize((width, height))

                    output_io = io.BytesIO()
                    save_name = os.path.splitext(file.filename)[0] + "." + format_option.lower()
                    img.save(output_io, format=format_option)
                    output_io.seek(0)

                    zipf.writestr(save_name, output_io.read())

        zip_buffer.seek(0)
        return send_file(zip_buffer, as_attachment=True, download_name="resized_images.zip", mimetype='application/zip')

    return render_template_string(html_page)

if __name__ == "__main__":
    app.run(debug=True)
