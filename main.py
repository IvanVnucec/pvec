import datetime
import requests
from bs4 import BeautifulSoup

class Vecernji:
    def __init__(self):
        self.base_url = "https://www.vecernji.hr"
        self.session = requests.Session()

    def _http_get(self, url:str) -> BeautifulSoup:
        response = self.session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def get_articles(self, date:datetime.datetime) -> list[str]:
        page = 1
        articles = []
        while True:
            url = f"{self.base_url}/najnovije-vijesti/{date.strftime('%Y-%m-%d')}?page={page}"
            soup = self._http_get(url)
            card_items = soup.find_all("div", class_="card-group__item")
            articles += [f"{self.base_url}{item.find('a', class_='card__link')['href']}" for item in card_items]
            is_last_page = soup.find("div", class_="author__pagination").find_all("a")[-1]["href"] == "#"
            if is_last_page:
                break
            page += 1
        articles_length_scraped = int(soup.find("div", class_="article-stats__number").text)
        assert len(articles) == articles_length_scraped
        return articles

def main():
    vecernji = Vecernji()
    date = datetime.datetime.today()
    while True:
        print(f"Scraping articles for {date.strftime('%Y-%m-%d')}...", end=" ", flush=True)
        articles = vecernji.get_articles(date=date)
        print(f"Found: {len(articles)}")
        date -= datetime.timedelta(days=1)

if __name__ == '__main__':
    main()
