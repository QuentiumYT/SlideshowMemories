import os, random
import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime

class SlideShow(tk.Tk):
    def __init__(self):
        """
        Main slideshow window without controls and max screen size
        """
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

        self.get_images(directory=directory)

    def get_images(self, directory="."):
        """
        Get image directory from command line or use current directory
        """
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(x) for x in [".jpg", ".jpeg", ".png", ".gif"]):
                    img_path = os.path.join(root, file)
                    self.image_list.append(img_path)

        random.shuffle(self.image_list)

    def start_slideshow(self, delay=4):
        """
        Select an image from the list and display it with a delay
        """
        image = self.image_list[self.current_id]
        self.current_id = (self.current_id + 1) % len(self.image_list)
        self.show_image(image)
        self.after(delay * 1000, self.start_slideshow)

    def parse_image(self, image_path):
        """
        Parse common dates (YMD format) or retrieve exif data
        * Full 20210215_112455 or 20210101-114941-87
        """
        image = image_path.split(os.sep)[-1]
        raw_date = image.split(".")[0]

        if len(image.split("-")) >= 2 or len(image.split("_")) >= 2:
            parsed_date = "_".join(raw_date.split("-")[:2])
            date = datetime.strptime(parsed_date, "%Y%m%d_%H%M%S")
        else:
            date = datetime.fromtimestamp(os.stat(image_path).st_mtime)

        return date.strftime("%d/%m/%Y %H:%M:%S")

    def show_image(self, file):
        """
        Resize the image to fit the screen without exceeding the original image size / specified size
        """
        image = Image.open(file)

        filename = file.split(os.sep)[-1]
        filedate = self.parse_image(file)

        image.thumbnail((self.screen_w, self.screen_h), Image.ANTIALIAS)

        self.current_image = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(self.screen_w / 2, self.screen_h / 2, anchor="center", image=self.current_image)
        # Image name top left
        self.canvas.create_text(20, 10, text=filename, fill="white", font=("Ubuntu", 12), anchor="nw")
        # Image date bottom left
        self.canvas.create_text(20, self.screen_h - 10, text=filedate, fill="white", font=("Ubuntu", 12), anchor="sw")



if __name__ == "__main__":
    # Select current directory
    directory = "."

    slideShow = SlideShow()
    slideShow.start_slideshow()
    slideShow.mainloop()
