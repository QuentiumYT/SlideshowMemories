import os
import threading
import time

from slide import SlideShow
from web import WebApp
from device import DeviceManager

class Services:
    def __init__(self):
        self.webapp = None
        self.slideshow = None
        self.device_manager = None

        self.configs = {}

    def start_web(self):
        # Debug is not possible in a thread, that's why it should always be false
        self.webapp = WebApp("0.0.0.0", 5502, False)
        self.webapp.init_web()
        self.webapp.load_routes()
        self.webapp.run()

    def start_slide(self):
        self.slideshow = SlideShow()
        self.slideshow.init_db("data/slideshow.sqlite")
        self.slideshow.load_images(directory="pictures/")
        self.slideshow.display_slides()
        self.slideshow.set_delay(3)
        self.slideshow.mainloop()

    def start_device(self):
        if not DeviceManager:
            return

        self.device_manager = DeviceManager()
        self.device_manager.get_mountpoints()
        self.device_manager.watch()

    def load_configs(self):
        self.configs = {
            "directories": self.slideshow.directories,
            "image_count": len(self.slideshow.image_list),
            "current_image": self.slideshow.current_image.filename,
            "delay": self.slideshow.delay,
        }
        self.webapp.configs = self.configs.copy()
        # Run sync configs in a tkinter event loop
        self.sync_configs(fetch_delay=2000)

    def sync_configs(self, fetch_delay: int = 2000):
        self.webapp.configs["current_image"] = self.slideshow.current_image.filename
        if self.configs["delay"] != self.webapp.configs["delay"]:
            self.slideshow.set_delay(self.webapp.configs["delay"])
            self.configs["delay"] = self.webapp.configs["delay"]

        self.slideshow.after(fetch_delay, self.sync_configs)



if __name__ == "__main__":
    services = Services()
    slide_thread = threading.Thread(target=services.start_slide)
    slide_thread.start()

    web_thread = threading.Thread(target=services.start_web)
    web_thread.start()

    device_thread = threading.Thread(target=services.start_device)
    device_thread.start()

    # Once the thread is initialized, load configs from the slideshow
    time.sleep(1)
    services.load_configs()

    # Load extra images into the slideshow
    time.sleep(5)
    services.slideshow.load_images("screenshots/")
    services.load_configs()
