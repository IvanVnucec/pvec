import datetime
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass

@dataclass
class Comment:
    author: str
    content: str
    date: datetime.datetime
    reactions: list['Comment'] = None

    def __str__(self) -> str:
        return f"{self.author} ({self.date.strftime('%H:%M %d.%m.%Y.')}): '{self.content[:10]}'"

class Vecernji:
    def __init__(self):
        self.base_url = "https://www.vecernji.hr"
        self.session = requests.Session()

    def _http_get(self, url:str) -> requests.Response:
        response = self.session.get(url)
        response.raise_for_status()
        return response

    def get_articles_url(self, date:datetime.datetime) -> list[str]:
        page = 1
        articles = []
        while True:
            url = f"{self.base_url}/najnovije-vijesti/{date.strftime('%Y-%m-%d')}?page={page}"
            response = self._http_get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            card_items = soup.find_all("div", class_="card-group__item")
            articles += [f"{self.base_url}{item.find('a', class_='card__link')['href']}" for item in card_items]
            last_page = soup.find("div", class_="author__pagination").find_all("a")[-1]["href"] == "#"
            if last_page:
                break
            page += 1
        articles_to_parse = int(soup.find("div", class_="article-stats__number").text)
        assert len(articles) == articles_to_parse
        return articles

    def get_comment_reactions(self, comment_id:int) -> list[Comment]:
        reactions = []
        url = f"{self.base_url}/forum/snippet-post/{comment_id}"
        response = self._http_get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        comment_boxes = soup.find("div", class_="comment-replies").find_all("div", class_="comment-box")
        for box in comment_boxes:
            # TODO: see if this code is in a get_comments function also
            author = str(box.find("div", class_="comment-card__author-name").text).strip()
            date = datetime.datetime.strptime(str(box.find("div", class_="comment-card__report-time").text).strip(), "%H:%M %d.%m.%Y.")
            content = str(box.find("div", class_="comment-card__text").p.text).strip()
            reactions.append(Comment(author, content, date))
        return reactions

    def get_comments(self, article_url:str) -> list[Comment]:
        page = 1
        comments:list[Comment] = []
        while True:
            url = f"{article_url}/komentari?order=-created_date&page={page}"
            try:
                response = self._http_get(url)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    return None
                else:
                    raise
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.find("div", class_="component__content").find_all("div", class_="card-group__item")
            for item in items:
                author = str(item.find("div", class_="comment-card__author-name").text).strip()
                date = datetime.datetime.strptime(str(item.find("div", class_="comment-card__time").text).strip(), "%H:%M %d.%m.%Y.")
                content = str(item.find("div", class_="comment-card__text").p.text).strip()
                reactions_exists = item.find("div", class_="comment-replies")
                if reactions_exists:
                    comment_id = int(item.find("div", class_="comment-card")["id"].replace("position_", ""))
                    reactions = self.get_comment_reactions(comment_id)
                else:
                    reactions = []
                comments.append(Comment(author, content, date, reactions))
            pagination = soup.find("div", class_="author__pagination")
            last_page = pagination == None or pagination.find_all("a")[-1]["href"] == "#"
            if last_page:
                break
            page += 1
        return comments

def main():
    import concurrent.futures
    from time import time

    vecernji = Vecernji()
    print("Starting scraping.")
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    print(f"Spawning {executor._max_workers} threads.")
    date = datetime.datetime.today()
    while date > datetime.datetime(2000, 1, 1):
        print(f"Scraping for articles published {date.strftime('%d.%m.%Y')}.")
        articles = vecernji.get_articles_url(date=date)
        print(f"Done. Found {len(articles)} article(s).")
        print(f"Scraping comments from every article.")
        tick = time()
        for i,(article,comments) in enumerate(zip(articles, executor.map(vecernji.get_comments, articles)), start=1):
            url = article.lstrip('https://')
            print(f"  {i:3}. {url}: {len(comments) if comments is not None else 'None'}")
        tock = time()
        dt = tock - tick
        aps = len(articles) / dt
        print(f"Done. Scraped {len(articles)} article(s) in {dt:.2f} seconds ({aps:.2f} articles/sec).")
        date -= datetime.timedelta(days=1)
        print()

if __name__ == '__main__':
    main()
