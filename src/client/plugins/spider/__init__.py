from .official_site_tw import Spider_ostw
from .official_site_cn import Spider_oscn


class Spiders:
    def __init__(self):
        self.spiders = {
            "news_tw_official": Spider_ostw(),
            "news_cn_official": Spider_oscn(),
        }

    def sources(self):
        return self.spiders.keys()

    def __getitem__(self, key):
        return self.spiders[key]
