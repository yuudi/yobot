from .base_spider import Base_spider, Item


class Spider_oscn(Base_spider):
    def __init__(self):
        super().__init__()
        self.url = "https://api.biligame.com/news/list?gameExtensionId=267&positionId=2&typeId=&pageNum=1&pageSize=5"
        self.type = "json"
        self.name = "国服官网"

    def get_items(self, content):
        try:
            items = [
                Item(
                    idx=n["id"],
                    content="{}\nhttps://game.bilibili.com/pcr/news.html#detail={}\n{}".format(
                        n["title"], n["id"], n["content"])
                )
                for n in content["data"]
            ]
            items.sort(key=lambda x: x["id"], reverse=True)
        except KeyError:
            print("咨询获取错误：{}，未知的样式".format(self.name))
            return None
        return items
