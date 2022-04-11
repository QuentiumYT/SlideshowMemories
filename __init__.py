import threading, os, time

from slide import SlideShow
from web import WebApp

class Services:
    def __init__(self):
        self.webapp = None
        self.slideshow = None

        self.configs = {}

    def start_web(self):
        # Debug is not possible in a thread, that's why it should always be false
        self.webapp = WebApp("0.0.0.0", 5502, False)
        self.webapp.init()
        self.webapp.load_routes()
        self.webapp.run()

    def start_slide(self):
        self.slideshow = SlideShow(directory="pictures/")
        self.slideshow.start_slideshow()
        self.slideshow.set_delay(3)
        self.slideshow.mainloop()

    def load_configs(self):
        self.configs = {
            "directory": self.slideshow.directory,
            "image_count": len(self.slideshow.image_list),
            "current_image": self.slideshow.current_image.filename.split(os.sep)[-1],
            "delay": self.slideshow.delay,
        }
        self.webapp.configs = self.configs.copy()
        # Run sync configs in a tkinter event loop
        services.sync_configs(fetch_delay=2000)

    def sync_configs(self, fetch_delay: int = 2000):
        self.webapp.configs["current_image"] = self.slideshow.current_image.filename.split(os.sep)[-1]
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

    # Once the thread is initialized, load configs from the slideshow
    time.sleep(1)
    services.load_configs()
