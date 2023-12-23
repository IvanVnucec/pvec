import datetime
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass

@dataclass
class Comment:
    author: str
    content: str
    date: datetime.datetime
    # TODO: add replies

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
            is_last_page = soup.find("div", class_="author__pagination").find_all("a")[-1]["href"] == "#"
            if is_last_page:
                break
            page += 1
        articles_length_scraped = int(soup.find("div", class_="article-stats__number").text)
        assert len(articles) == articles_length_scraped
        return articles

    def get_comments(self, article_url:str) -> list[Comment]:
        article = article_url.rsplit("/")[-1]
        url = f"{self.base_url}/forum/{article}/komentari?order=-created_date"
        try:
            response = self._http_get(url)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            else:
                raise
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find("div", class_="component__content").find_all("div", class_="card-group__item")
        # TODO: also scrape replies
        comments = []
        for item in items:
            comments.append(Comment(
                author=str(item.find("div", class_="comment-card__author-name").text).strip(),
                date=datetime.datetime.strptime(str(item.find("div", class_="comment-card__time").text).strip(), "%H:%M %d.%m.%Y."),
                content=str(item.find("div", class_="comment-card__text").p.text).strip(),
            ))
        return comments

def main():
    vecernji = Vecernji()
    date = datetime.datetime.today()
    while True:
        print(f"Scraping for articles published {date.strftime('%d.%m.%Y')}.")
        articles = vecernji.get_articles_url(date=date)
        print(f"Done. Found {len(articles)} article(s).")
        print("Scraping comments for each article.")
        for i,article in enumerate(articles, start=1):
            print(f"  {i:3}. '{article[:60]}...':", end=" ", flush=True)
            comments = vecernji.get_comments(article)
            print(len(comments) if comments != None else None)
        date -= datetime.timedelta(days=1)
        print()

if __name__ == '__main__':
    main()
