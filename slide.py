import hashlib
import os
import random
import tkinter as tk
from datetime import datetime

import dotenv
import requests
from PIL import ExifTags, Image, ImageTk

from db import DBHandler

class SlideShow(tk.Tk):
    def __init__(self, directory: str = "."):
        """
        Main slideshow window without controls and max screen size
        """
        self.directory = directory.replace("/", os.sep).replace("\\", os.sep)

        tk.Tk.__init__(self)

        self.title("Slideshow")

        self.bind("<Escape>", lambda _: self.destroy())
        self.bind("<Control-c>", lambda _: self.destroy())

        self.attributes("-fullscreen", True)

        self.screen_w, self.screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{self.screen_w}x{self.screen_h}+0+0")

        self.resizable(False, False)

        self.update_idletasks()

        self.image_list = []
        self.current_image = None
        self.current_id = 0

        self.canvas = tk.Canvas(self, background="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.get_images()

    def init_db(self, db_name: str):
        self.db_name = db_name

        self.db = DBHandler(self.db_name)

        struct = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL",
            "name": "TEXT NOT NULL",
            "hash": "TEXT UNIQUE NOT NULL",
            "lat": "REAL NOT NULL",
            "lon": "REAL NOT NULL",
            "location": "TEXT",
        }

        self.db.create_table("locations", struct)

    def get_images(self):
        """
        Get all images from the directory and shuffle them
        """
        for root, _, files in os.walk(self.directory):
            for file in files:
                if any(file.lower().endswith(x) for x in [".jpg", ".jpeg", ".png", ".gif"]):
                    img_path = os.path.join(root, file)
                    self.image_list.append(img_path)

        random.shuffle(self.image_list)

    def display_slides(self):
        """
        Select each image of the random list and display them with a delay
        """
        # Default delay between images if not set
        if not hasattr(self, "delay"):
            self.delay = 2

        image = self.image_list[self.current_id]
        # Select next image using its shuffle id (non repeatable until looping is complete)
        self.current_id = (self.current_id + 1) % len(self.image_list)
        self.show_image(image)
        self.after(self.delay * 1000, self.display_slides)

    def set_delay(self, delay: int):
        """
        Set the delay between images
        """
        self.delay = delay

    def parse_image_data(self, image_obj: Image) -> dict:
        """
        Get image data from exif
        """
        # pylint: disable=protected-access
        exif = image_obj._getexif()

        return {ExifTags.TAGS[k]: v for k, v in exif.items() if k in ExifTags.TAGS} if exif else {}

    def get_image_date(self, image_path: str, image_date: str) -> str:
        """
        Parse date using exif data if exists, else use file modification date
        """
        if image_date:
            date = datetime.strptime(image_date, "%Y:%m:%d %H:%M:%S")
        else:
            date = datetime.fromtimestamp(os.stat(image_path).st_mtime)

        return date.strftime("%d/%m/%Y %H:%M:%S")

    def get_image_coords(self, gps_info: dict) -> tuple:
        """
        Get the image coordinates as latitude, longitude and altitude
        """

        coords_data = {ExifTags.GPSTAGS[k]: v for k, v in gps_info.items() if k in ExifTags.GPSTAGS}

        if coords_data:
            # Convert the GPS coordinates stored in the EXIF to degrees in float format
            # pylint: disable=unnecessary-lambda-assignment
            dms_to_decimal = lambda dms: float(dms[0]) + float(dms[1]) / 60 + float(dms[2]) / 3600

            lat = + dms_to_decimal(coords_data.get("GPSLatitude"))
            lon = + dms_to_decimal(coords_data.get("GPSLongitude"))
            alt = round(coords_data.get("GPSAltitude"))

            if coords_data.get("GPSLatitudeRef") != "N":
                lat *= -1
            if coords_data.get("GPSLongitudeRef") != "E":
                lon *= -1

        return lat, lon, alt

    def get_image_location(self, lat: str, lon: str) -> str:
        """
        Get the place at which the image was taken using latitude and longitude
        """
        key = os.environ.get("API_KEY")
        url = f"http://api.positionstack.com/v1/reverse?access_key={key}&query={lat},{lon}&limit=1"
        req = requests.get(url, timeout=5)

        return req.json()["data"][0]["name"] + ", " + req.json()["data"][0]["locality"] if req.ok else ""

    def show_image(self, filepath: str):
        """
        Resize the image to fit the screen without exceeding the original image size / specified size
        """
        self.current_image = Image.open(filepath)

        image_name = filepath.split(os.sep)[-1]
        image_data = self.parse_image_data(self.current_image)
        image_date = self.get_image_date(filepath, image_data.get("DateTimeOriginal", image_data.get("DateTime")))

        if image_data.get("GPSInfo") and isinstance(image_data.get("GPSInfo"), dict):
            image_coords = self.get_image_coords(image_data.get("GPSInfo"))
            image_alt = f"Altitude : {image_coords[2]}m"

            image_hash = hashlib.sha256(self.current_image.tobytes()).hexdigest()
            image_query = self.db.get_row("locations", "hash", image_hash)

            if image_query:
                image_loc = image_query.get("location")
            elif os.environ.get("API_KEY"):
                image_loc = self.get_image_location(image_coords[0], image_coords[1])

                if image_loc:
                    data = {
                        "name": image_name,
                        "hash": image_hash,
                        "lat": image_coords[0],
                        "lon": image_coords[1],
                        "location": image_loc,
                    }

                    self.db.insert_row("locations", data)
                else:
                    image_loc = f"Lat : {image_coords[0]}, Lon : {image_coords[1]}"
            else:
                image_loc = f"Lat : {image_coords[0]}, Lon : {image_coords[1]}"
        else:
            image_coords = (0, 0, 0)
            image_alt = None
            image_loc = "Lieu non défini"

        self.current_image.thumbnail((self.screen_w, self.screen_h), Image.Resampling.LANCZOS)

        self.photo_image = ImageTk.PhotoImage(self.current_image)
        self.canvas.delete("all")
        self.canvas.create_image(self.screen_w / 2, self.screen_h / 2, anchor="center", image=self.photo_image)

        # Image date top left
        self.canvas.create_text(20, 10, text=image_date, fill="white", font=("Ubuntu", 12), anchor="nw")
        # Image location bottom left
        self.canvas.create_text(20, self.screen_h - (30 if image_alt else 10), text=image_loc, fill="white", font=("Ubuntu", 12), anchor="sw")
        self.canvas.create_text(20, self.screen_h - 10, text=image_alt, fill="white", font=("Ubuntu", 12), anchor="sw")
        # Image name bottom right
        self.canvas.create_text(self.screen_w - 20, self.screen_h - 10, text=image_name, fill="white", font=("Ubuntu", 12), anchor="se")



if __name__ == "__main__":
    dotenv.load_dotenv()

    slideshow = SlideShow(directory="pictures/")

    slideshow.init_db("data/slideshow.sqlite")
    slideshow.display_slides()
    slideshow.set_delay(2)

    slideshow.mainloop()
