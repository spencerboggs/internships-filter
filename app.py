from flask import Flask, render_template, request, redirect, url_for, jsonify
import plotly.graph_objects as go
import requests
import re
import json
import os

app = Flask(__name__)

# "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/refs/heads/dev/README.md"
GITHUB_README_URLS = [
    "https://raw.githubusercontent.com/cvrve/Summer2025-Internships/main/README.md"
]
INTERNSHIP_DATA_FILE = "internships.json"
APPLIED_JOBS_FILE = "data.json"

def check_applied_jobs_file():
    if not os.path.exists(APPLIED_JOBS_FILE):
        with open(APPLIED_JOBS_FILE, "w") as file:
            json.dump([], file)

def check_internships_file():
    if not os.path.exists(INTERNSHIP_DATA_FILE) or os.path.getsize(INTERNSHIP_DATA_FILE) == 0:
        all_table_data = []
        for url in GITHUB_README_URLS:
            table_data = fetch_table_from_readme(url)
            table_data = replace_arrow_with_valid_company(table_data)
            all_table_data.extend(table_data)
        merged_data = merge_internship_data(all_table_data)
        save_internship_data(merged_data)


def load_applied_jobs_data():
    with open(APPLIED_JOBS_FILE, "r") as file:
        return json.load(file)

def save_applied_jobs_data(data):
    with open(APPLIED_JOBS_FILE, "w") as file:
        json.dump(data, file)

def load_internship_data():
    with open(INTERNSHIP_DATA_FILE, "r") as file:
        return json.load(file)

def save_internship_data(data):
    with open(INTERNSHIP_DATA_FILE, "w") as file:
        json.dump(data, file)

def fetch_table_from_readme(url):
    response = requests.get(url)
    if response.status_code == 200:
        readme_content = response.text.splitlines()
        table_start = None
        for i, line in enumerate(readme_content):
            if line.strip().startswith("| Company | Role | Location | Application/Link | Date Posted |"):
                table_start = i
                break
        if table_start is None:
            return []
        rows = []
        for line in readme_content[table_start + 2:]:
            if not line.strip() or not line.startswith("|"):
                break
            columns = [col.strip() for col in line.split("|")[1:-1]]
            if len(columns) == 5:
                rows.append({
                    "Company": columns[0],
                    "Role": columns[1],
                    "Location": columns[2],
                    "Application/Link": columns[3],
                    "Date Posted": columns[4]
                })
        return rows
    else:
        return []

def replace_arrow_with_valid_company(table_data):
    last_valid_company = ""
    for row in table_data:
        if row["Company"] == "\u21b3":
            row["Company"] = last_valid_company
        else:
            last_valid_company = row["Company"]
    return table_data

def merge_internship_data(table_data):
    seen = set()
    unique_data = []
    for row in table_data:
        key = (row["Company"].lower(), row["Role"].lower())
        if key not in seen:
            seen.add(key)
            unique_data.append(row)
    return unique_data

def update_existing_entries():
    app_data = load_applied_jobs_data()
    for entry in app_data:
        if "Interviewed" not in entry:
            entry["Interviewed"] = False
        if "Hired" not in entry:
            entry["Hired"] = False
    save_applied_jobs_data(app_data)

@app.route("/", methods=["GET", "POST"])
def index():
    check_applied_jobs_file()
    check_internships_file()

    table_data = load_internship_data()
    app_data = load_applied_jobs_data()

    for row in table_data:
        row['Applied'] = any(app['Company'] == row['Company'] and app['Role'] == row['Role'] for app in app_data)

    filters = {
        "company": request.form.get("company", "").lower(),
        "role": request.form.get("role", "").lower(),
        "location": request.form.get("location", "").lower()
    }

    def is_negative_filter(filter_value):
        return filter_value.startswith("-")

    if filters["company"]:
        if is_negative_filter(filters["company"]):
            table_data = [row for row in table_data if filters["company"][1:] not in row["Company"].lower()]
        else:
            table_data = [row for row in table_data if filters["company"] in row["Company"].lower()]
    if filters["role"]:
        if is_negative_filter(filters["role"]):
            table_data = [row for row in table_data if filters["role"][1:] not in row["Role"].lower()]
        else:
            table_data = [row for row in table_data if filters["role"] in row["Role"].lower()]
    if filters["location"]:
        if is_negative_filter(filters["location"]):
            table_data = [row for row in table_data if filters["location"][1:] not in row["Location"].lower()]
        else:
            table_data = [row for row in table_data if filters["location"] in row["Location"].lower()]

    table_data = replace_arrow_with_valid_company(table_data)

    table_data = [row for row in table_data if '🔒' not in row["Application/Link"]]

    result_count = str(len(table_data)) + " internships found"
    result_count = result_count if len(table_data) > 1 else str(len(table_data)) + " internship found"

    for row in table_data:
        for key in row:
            if key == "Location":
                row[key] = re.sub(r'(</br\s*/?>)', r'<br>', row[key])
                row[key] = re.sub(r'<(?!br\s*/?)[^<]+?>', '', row[key])
                row[key] = re.sub(r'\*\*.*?\*\*', '', row[key])
            elif key == "Application/Link":
                row[key] = re.sub(r'<a\s+[^>]*href="([^"]*)"[^>]*>.*?<\s*/a>', r'<a href="\1" target="_blank">Apply</a>', row[key])

    if request.method == "POST" and "clear_filters" in request.form:
        return redirect(url_for('index'))

    return render_template("index.html", table_data=table_data, filters=filters, result_count=result_count)

@app.route("/update_status", methods=["POST"])
def update_status():
    check_applied_jobs_file()
    update_existing_entries()
    app_data = load_applied_jobs_data()
    data = request.json
    
    entry = {
        "Company": data["Company"],
        "Role": data["Role"],
        "Application/Link": data["Application/Link"],
        "Location": data["Location"],
        "Date": data["Date"],
        "Interviewed": data.get("Interviewed", False),
        "Hired": data.get("Hired", False)
    }

    if data["Applied"]:
        if not any(app for app in app_data if app["Company"] == data["Company"] and app["Role"] == data["Role"]):
            app_data.append(entry)
    else:
        app_data = [app for app in app_data if not (app["Company"] == data["Company"] and app["Role"] == data["Role"])]
    
    save_applied_jobs_data(app_data)
    return jsonify({"success": True})

@app.route("/saved_jobs")
def saved_jobs():
    check_applied_jobs_file()
    saved_jobs = load_applied_jobs_data()
    saved_jobs = saved_jobs[::-1]
    saved_jobs_length = str(len(saved_jobs)) + " internships"
    saved_jobs_length = saved_jobs_length if len(saved_jobs) > 1 else str(len(saved_jobs)) + " internship"
    return render_template("applied.html", saved_jobs=saved_jobs, saved_jobs_length=saved_jobs_length)

@app.route("/refresh_internships", methods=["GET"])
def refresh_internships():
    try:
        all_table_data = []
        for url in GITHUB_README_URLS:
            table_data = fetch_table_from_readme(url)
            table_data = replace_arrow_with_valid_company(table_data)
            all_table_data.extend(table_data)
        merged_data = merge_internship_data(all_table_data)
        save_internship_data(merged_data)
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error refreshing internships: {e}")
        return jsonify({"success": False})


@app.route("/sankey_diagram")
def sankey_diagram():
    check_applied_jobs_file()
    data = load_applied_jobs_data()

    statuses = ["Applied", "Interviewed", "Not Interviewed", "Hired", "Not Hired"]
    nodes = statuses
    node_indices = {node: i for i, node in enumerate(nodes)}

    total_applied = len(data)
    interviewed = sum(1 for job in data if job.get("Interviewed", False))
    not_interviewed = total_applied - interviewed
    hired_from_interviewed = sum(1 for job in data if job.get("Interviewed", False) and job.get("Hired", False))
    not_hired_from_interviewed = interviewed - hired_from_interviewed
    hired_from_not_interviewed = sum(1 for job in data if not job.get("Interviewed", False) and job.get("Hired", False))
    not_hired_from_not_interviewed = not_interviewed - hired_from_not_interviewed

    links = [
        {"source": node_indices["Applied"], "target": node_indices["Interviewed"], "value": interviewed},
        {"source": node_indices["Applied"], "target": node_indices["Not Interviewed"], "value": not_interviewed},
        
        {"source": node_indices["Interviewed"], "target": node_indices["Hired"], "value": hired_from_interviewed},
        {"source": node_indices["Interviewed"], "target": node_indices["Not Hired"], "value": not_hired_from_interviewed},
        
        {"source": node_indices["Not Interviewed"], "target": node_indices["Hired"], "value": hired_from_not_interviewed},
        {"source": node_indices["Not Interviewed"], "target": node_indices["Not Hired"], "value": not_hired_from_not_interviewed},
    ]

    sankey_fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes
        ),
        link=dict(
            source=[link["source"] for link in links],
            target=[link["target"] for link in links],
            value=[link["value"] for link in links]
        )
    )])

    sankey_fig.update_layout(title_text="Sankey Diagram of Job Applications", font_size=10)
    sankey_html = sankey_fig.to_html(full_html=False)

    saved_jobs_length = f"{len(data)} applications completed"

    return render_template("sankey.html", sankey_html=sankey_html, saved_jobs_length=saved_jobs_length)

@app.route("/update_interview_offer", methods=["POST"])
def update_interview_offer():
    check_applied_jobs_file()
    app_data = load_applied_jobs_data()
    data = request.json

    for app in app_data:
        if app["Company"] == data["Company"] and app["Role"] == data["Role"]:
            app["Interviewed"] = data["Interviewed"]
            app["Hired"] = data["Hired"]
            break

    save_applied_jobs_data(app_data)
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
