import os, random
import tkinter as tk
from PIL import Image, ImageTk, ExifTags
from datetime import datetime

class SlideShow(tk.Tk):
    def __init__(self, directory: str = "."):
        """
        Main slideshow window without controls and max screen size
        """
        self.directory = directory.replace("/", os.sep).replace("\\", os.sep)

        tk.Tk.__init__(self)

        self.attributes("-fullscreen", True)

        self.overrideredirect(True)

        self.screen_w, self.screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("{}x{}+{}+{}".format(self.screen_w, self.screen_h, 0, 0))

        self.image_list = []
        self.current_image = None
        self.current_id = 0

        self.canvas = tk.Canvas(self, background="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.get_images()

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

    def start_slideshow(self, delay: int = 4):
        """
        Select an image from the list and display it with a delay
        """
        image = self.image_list[self.current_id]
        # Select next image using its shuffle id (non repeatable until looping is complete)
        self.current_id = (self.current_id + 1) % len(self.image_list)
        self.show_image(image)
        self.after(delay * 1000, self.start_slideshow)

    def parse_image_data(self, image_obj: Image) -> dict:
        """
        Get image data from exif
        """
        exif = image_obj._getexif()

        if not exif:
            return {}

        return {ExifTags.TAGS[k]: v for k, v in exif.items() if k in ExifTags.TAGS}

    def get_image_date(self, image_path: str, image_date: str) -> str:
        """
        Parse date using exif data if exists, else use file modification date
        """

        if image_date:
            date = datetime.strptime(image_date, "%Y:%m:%d %H:%M:%S")
        else:
            date = datetime.fromtimestamp(os.stat(image_path).st_mtime)

        return date.strftime("%d/%m/%Y %H:%M:%S")

    def show_image(self, filepath: str):
        """
        Resize the image to fit the screen without exceeding the original image size / specified size
        """
        image = Image.open(filepath)

        filename = filepath.split(os.sep)[-1]
        filedata = self.parse_image_data(image)
        filedate = self.get_image_date(filepath, filedata.get("DateTimeOriginal", filedata.get("DateTime")))

        image.thumbnail((self.screen_w, self.screen_h), Image.Resampling.LANCZOS)

        self.current_image = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(self.screen_w / 2, self.screen_h / 2, anchor="center", image=self.current_image)
        # Image name top left
        self.canvas.create_text(20, 10, text=filename, fill="white", font=("Ubuntu", 12), anchor="nw")
        # Image date bottom left
        self.canvas.create_text(20, self.screen_h - 10, text=filedate, fill="white", font=("Ubuntu", 12), anchor="sw")



if __name__ == "__main__":
    slideShow = SlideShow(directory=".")
    slideShow.start_slideshow(delay=2)
    slideShow.mainloop()
