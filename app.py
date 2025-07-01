from flask import Flask, render_template_string, request, send_file
from PIL import Image
import io, os, zipfile

app = Flask(__name__)
MAX_SIZE_MB = 4.5
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

html = """<!DOCTYPE html>
<html>
<head>
    <title>Image Resizer Tool</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; background: #f7f7f7; margin: 0; padding: 0; }
        .box { background: white; padding: 30px; max-width: 500px; margin: 40px auto; box-shadow: 0 0 10px #ccc; border-radius: 10px; }
        input, select { margin: 8px 0; width: 100%; padding: 8px; box-sizing: border-box; }
        button { background: #007bfc; color: white; padding: 10px; width: 100%; border: none; border-radius: 5px; margin-top: 10px; }
        .drop-area {
            border: 2px dashed #aaa;
            padding: 20px;
            border-radius: 10px;
            background: #f0f0f0;
            cursor: pointer;
            margin: 10px 0;
        }
        .preview img {
            max-width: 80px;
            margin: 5px;
            border-radius: 5px;
        }
        .history {
            background: #eaf7ea;
            padding: 10px;
            border-radius: 5px;
            margin-top: 15px;
        }
    </style>
</head>
<body>
<div class="box">
    <h2>Resize Your Images</h2>
    <form method="POST" enctype="multipart/form-data" id="resizeForm">
        <div class="drop-area" id="drop-area">📥 Drag & Drop Images or Click to Upload</div>
        <input type="file" id="fileInput" name="images" multiple style="display:none;" required><br>
        <div class="preview" id="preview"></div>
        <input type="number" name="width" placeholder="Width (px)" required value="250"><br>
        <input type="number" name="height" placeholder="Height (px)" required value="250"><br>
        <select name="format">
            <option value="jpg">JPG</option>
            <option value="png">PNG</option>
        </select><br>
        <button type="submit">Resize & Download ZIP</button>
    </form>

    <div class="history">
        <b>Last Resized:</b>
        <ul id="historyList"></ul>
    </div>
</div>

<script>
const dropArea = document.getElementById("drop-area");
const fileInput = document.getElementById("fileInput");
const preview = document.getElementById("preview");
const historyList = document.getElementById("historyList");

dropArea.addEventListener("click", () => fileInput.click());
dropArea.addEventListener("dragover", e => {
    e.preventDefault();
    dropArea.style.background = "#d0e9ff";
});
dropArea.addEventListener("dragleave", () => {
    dropArea.style.background = "#f0f0f0";
});
dropArea.addEventListener("drop", e => {
    e.preventDefault();
    dropArea.style.background = "#f0f0f0";
    fileInput.files = e.dataTransfer.files;
    showPreview(fileInput.files);
});
fileInput.addEventListener("change", () => showPreview(fileInput.files));
function showPreview(files) {
    preview.innerHTML = "";
    for (const file of files) {
        const img = document.createElement("img");
        img.src = URL.createObjectURL(file);
        preview.appendChild(img);
    }
}
document.getElementById("resizeForm").addEventListener("submit", () => {
    const names = Array.from(fileInput.files).map(f => f.name);
    localStorage.setItem("resizedHistory", JSON.stringify(names));
});
window.addEventListener("load", () => {
    const history = JSON.parse(localStorage.getItem("resizedHistory") || "[]");
    historyList.innerHTML = history.map(name => `<li>${name}</li>`).join("");
});
</script>
</body>
</html>"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            width = int(request.form.get("width", 250))
            height = int(request.form.get("height", 250))
            fmt = request.form.get("format", "jpg").upper()
            pillow_fmt = "JPEG" if fmt == "JPG" else fmt

            files = request.files.getlist("images")
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for file in files:
                    file.seek(0, os.SEEK_END)
                    if file.tell() > MAX_SIZE_BYTES:
                        return f"❌ File too large: {file.filename} (limit: 4.5MB)"
                    file.seek(0)

                    img = Image.open(file)
                    if pillow_fmt == "JPEG":
                        img = img.convert("RGB")
                    img = img.resize((width, height))

                    output = io.BytesIO()
                    filename = os.path.splitext(file.filename)[0] + "." + fmt.lower()
                    img.save(output, format=pillow_fmt)
                    output.seek(0)
                    zipf.writestr(filename, output.read())

            zip_buffer.seek(0)
            return send_file(zip_buffer, download_name="resized_images.zip", as_attachment=True)
        except Exception as e:
            return f"Internal Error: {e}"
    return render_template_string(html)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
