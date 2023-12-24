from vecernji import Vecernji
import datetime

def main():
    import concurrent.futures
    from time import time

    vecernji = Vecernji()
    print("Starting scraping.")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        print(f"Spawning {executor._max_workers} threads.")
        today = datetime.datetime.today()
        end_day = today - datetime.timedelta(days=1)
        date = today
        while date > end_day:
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
            # TODO: save to database
            date -= datetime.timedelta(days=1)
            print()

if __name__ == '__main__':
    main()
