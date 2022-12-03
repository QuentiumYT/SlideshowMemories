import os, dotenv, glob
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_assets import Bundle, Environment

class WebApp:
    def __init__(self, host: str, port: int, debug: bool):
        self.host = host
        self.port = port
        self.debug = debug
        self.configs = {}

        self.watch_folder = lambda f: list(glob.iglob(f + "**", recursive=True))

    def init(self):
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET")
        self.app.secret_key = os.environ.get("FLASK_SECRET")

        self.session = session

        bundles = {
            "scss": Bundle(
                "../scss/style.scss",
                filters="libsass",
                depends=("../scss/*.scss"),
                output="../css/style.css"
            ),

            "cssmin": Bundle(
                "../css/style.css",
                filters="cssmin",
                output="css/style.css"
            ),

            "jsmin": Bundle(
                "../js/main.js",
                filters="jsmin",
                output="js/main.js"
            ),
        }

        assets = Environment(self.app)
        assets.register(bundles)
        bundles["scss"].build(force=True)
        bundles["cssmin"].build(force=True)
        bundles["jsmin"].build(force=True)

    def load_routes(self):
        @self.app.errorhandler(404)
        def not_found(error):
            self.session["error"] = str(error)
            return redirect(url_for("home"))

        @self.app.route("/download/<path:filename>")
        def download_file(filename, download: bool = False):
            if request.args.get("download"):
                download = True
            return send_from_directory("pictures/", filename, as_attachment=download)

        @self.app.route("/", methods=["GET", "POST"])
        @self.app.route("/home", methods=["GET", "POST"])
        def home():
            if request.method == "POST":
                self.configs["delay"] = int(request.form.get("delay"))

                return redirect(url_for("home"))

            return render_template("home.jinja2",
                                   configs=self.configs)

    def run(self):
        self.app.run(host=self.host,
                     port=self.port,
                     debug=self.debug,
                     # Reload if SCSS was compiled
                     extra_files=self.watch_folder("scss/") + self.watch_folder("js/"))



if __name__ == "__main__":
    dotenv.load_dotenv()

    webapp = WebApp("0.0.0.0", 5502, True)
    webapp.init()
    webapp.load_routes()
    webapp.run()
