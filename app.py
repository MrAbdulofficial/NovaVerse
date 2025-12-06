import os
import sqlite3
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash

# ----------------------------------------------------------------------
# NovaVerse - A personal portfolio website built with Flask + SQLite.
# NOTE: Some parts of this project (structure/comments/text) were
# assisted by an AI tool (ChatGPT), but the final code and logic
# were reviewed and customized by me (your name).
# ----------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "change-this-secret-key"  # required for flash messages

DATABASE = "novaverse.db"


def get_db_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they do not exist."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Create projects table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            link TEXT,
            tags TEXT,
            image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Create messages table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    conn.commit()
    conn.close()


@app.route("/")
def index():
    """Home page."""
    return render_template("index.html")


@app.route("/about")
def about():
    """About page."""
    return render_template("about.html")


@app.route("/projects")
def projects():
    """List all projects."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch projects
    cur.execute("SELECT * FROM projects ORDER BY created_at DESC;")
    projects = cur.fetchall()

    # Fetch images for each project
    images_dict = {}
    for project in projects:
        cur.execute("SELECT image FROM project_images WHERE project_id = ?", (project["id"],))
        images = cur.fetchall()
        images_dict[project["id"]] = [img["image"] for img in images]

    conn.close()

    # Pass images to template
    return render_template("projects.html", projects=projects, images=images_dict)



@app.route("/projects/add", methods=["GET", "POST"])
def add_project():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        link = request.form.get("link")
        tags = request.form.get("tags")

        # MULTIPLE IMAGE UPLOAD
        image_files = request.files.getlist("images")
        image_filenames = []

        for image in image_files:
            if image and image.filename != "":
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filenames.append(filename)

        if not title or not description:
            flash("Title and description are required.", "error")
            return redirect(url_for("add_project"))

        conn = get_db_connection()
        cur = conn.cursor()

        # Insert project
        cur.execute(
            """
            INSERT INTO projects (title, description, link, tags)
            VALUES (?, ?, ?, ?);
            """,
            (title, description, link, tags),
        )

        project_id = cur.lastrowid

        # Insert images for this project
        for filename in image_filenames:
            cur.execute(
                "INSERT INTO project_images (project_id, image) VALUES (?, ?);",
                (project_id, filename)
            )

        conn.commit()
        conn.close()

        flash("Project added successfully!", "success")
        return redirect(url_for("projects"))

    return render_template("add_project.html")


app.config['UPLOAD_FOLDER'] = 'static/images/projects'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route("/projects/delete/<int:id>", methods=["POST"])
def delete_project(id):
    """Delete a project by ID."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM projects WHERE id = ?;", (id,))
    conn.commit()
    conn.close()

    flash("Project deleted successfully!", "success")
    return redirect(url_for("projects"))



@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact form (stores message in database)."""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")

        if not name or not email or not message:
            flash("Name, email, and message are required.", "error")
            return redirect(url_for("contact"))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO messages (name, email, subject, message)
            VALUES (?, ?, ?, ?);
            """,
            (name, email, subject, message),
        )
        conn.commit()
        conn.close()

        flash("Thanks for reaching out! I'll get back to you soon.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")

@app.route("/resume")
def resume():
    return render_template("resume.html")

@app.route("/certificates")
def certificates():
    certificates = [
        {
            "title": "CS50x Certificate",
            "issuer": "Harvard / CS50",
            "file": url_for('static', filename='certificates/cs50.png')
        },
        {
            "title": "Web Development Internship",
            "issuer": "TechnoHacks Solutions",
            "file": url_for('static', filename='certificates/webdev.jpg')
        },
        {
            "title": "Introduction to Agile Methodology",
            "issuer": "Infosys Springboard",
            "file": url_for('static', filename='certificates/agile.png')
        }
    ]
    return render_template("certificates.html", certificates=certificates)

if __name__ == "__main__":
    # Initialize DB before first run
    if not os.path.exists(DATABASE):
        init_db()
    else:
        # safe to call anyway
        init_db()

    # Run the Flask development server
    app.run(debug=True)
