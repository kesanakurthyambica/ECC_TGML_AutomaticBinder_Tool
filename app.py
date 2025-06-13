from flask import Flask, request, render_template, send_file
import os
import pandas as pd
import xml.etree.ElementTree as ET

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def update_binds(xml_file, excel_file, sheet_name):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    df = pd.read_excel(excel_file, sheet_name=sheet_name)

    label_to_bind = {}
    for _, row in df.iterrows():
        nomenclature = str(row.get("Nomenclature", "")).strip()
        for col in ["First Label", "Second Label", "Third Label"]:
            label = str(row.get(col, "")).strip()
            if label:
                label_to_bind[label] = nomenclature

    in_group = False
    current_text = None
    inside_target_text = False

    for elem in root.iter():
        if elem.tag == "Group":
            in_group = True
        elif elem.tag == "Text" and in_group:
            current_text = elem.attrib.get("Name", "").strip()
            inside_target_text = current_text in label_to_bind
        elif elem.tag == "Bind" and in_group and inside_target_text:
            new_bind = label_to_bind.get(current_text)
            elem.set("Name", new_bind)

    output_path = os.path.join(PROCESSED_FOLDER, os.path.basename(xml_file))
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    return output_path

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        tgml = request.files['tgml_file']
        excel = request.files['excel_file']
        sheet_name = request.form['sheet_name']

        tgml_path = os.path.join(UPLOAD_FOLDER, tgml.filename)
        excel_path = os.path.join(UPLOAD_FOLDER, excel.filename)
        tgml.save(tgml_path)
        excel.save(excel_path)

        try:
            processed_file = update_binds(tgml_path, excel_path, sheet_name)
            return send_file(processed_file, as_attachment=True)
        except Exception as e:
            return f"<h3>Error: {str(e)}</h3>"

    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)