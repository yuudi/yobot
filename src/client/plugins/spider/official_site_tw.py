from urllib.parse import urljoin

from .base_spider import Base_spider, Item


class Spider_ostw(Base_spider):
    def __init__(self):
        super().__init__()
        self.url = "http://www.princessconnect.so-net.tw/news/"
        self.type = "html"
        self.name = "台服官网"

    def get_items(self, soup):
        return [
            Item(idx=dd.a["href"],
                 content="{}\n{}".format(dd.text, urljoin(self.url, dd.a["href"])))
            for dd in soup.find_all("dd")
        ]
