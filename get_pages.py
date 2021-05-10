
import requests
from bs4 import BeautifulSoup
import json
import xmltodict

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
}


def get_pages_allrecipes():
    base_URL = 'https://www.allrecipes.com/sitemaps/recipe/'

    pages_allrecipes = []
    for i in range(1, 5):

        URL = base_URL + str(i) + '/sitemap.xml'
        page = requests.get(URL, headers=HEADERS)
        sitemap_dict = xmltodict.parse(page.text)

        for r in sitemap_dict["urlset"]["url"]:
            pages_allrecipes.append(r["loc"])

    with open('pages_allrecipes.json', 'w') as outfile:
        json.dump(pages_allrecipes, outfile)


def get_pages_chefkoch():
    counter = 0
    pages_chefkoch = []
    while counter < 120000:
        print(counter)

        URL = 'https://www.chefkoch.de/rs/s{}/Rezepte.html'.format(counter)

        page = requests.get(URL, headers=HEADERS)
        soup = BeautifulSoup(page.content, 'lxml')

        recipe = soup.findAll('a', {'class': 'ds-mb ds-mb-row ds-card rsel-recipe bi-recipe-item'})

        for i in recipe:
            x = i['href']
            pages_chefkoch.append(x)

        counter = counter + 30

    with open('pages_chefkoch6.json', 'w') as outfile:
        json.dump(pages_chefkoch, outfile)


def get_pages_epicurious():
    counter = 1
    pages_epicurious = []
    while counter < 2400:

        page_URL = 'https://www.epicurious.com/search?content=recipe&page={}'.format(counter)
        base_URL = 'https://www.epicurious.com'

        page = requests.get(page_URL, headers=HEADERS)
        soup = BeautifulSoup(page.content, 'lxml')

        recipe = soup.findAll('div', {'class': 'recipe-panel'})

        for r in recipe:
            x = r.find('a')['href']
            recipe_URL = base_URL + x
            pages_epicurious.append(recipe_URL)
        counter = counter + 1

    with open('pages_epicurious.json', 'w') as outfile:
        json.dump(pages_epicurious, outfile)


def get_pages_fooby():
    URL = 'https://fooby.ch/sitemap.xml'

    page = requests.get(URL, headers=HEADERS)
    sitemap_dict = xmltodict.parse(page.text)

    all_url = [r["loc"] for r in sitemap_dict["urlset"]["url"]]

    url_filter = []

    for i in range(1000, 10000):
        url_filter.append('rezepte/' + str(i))

    recipe_url = [ele for ele in all_url for x in url_filter if x in ele]

    with open('pages_fooby.json', 'w') as outfile:
        json.dump(recipe_url, outfile)


def get_pages_cucchiaio():
    counter = 1
    pages_cucchiaio = []
    while counter < 700:

        page_URL = 'https://www.cucchiaio.it/ricette/pag_{}/'.format(counter)
        base_URL = 'https://www.cucchiaio.it'

        page = requests.get(page_URL, headers=HEADERS)
        soup = BeautifulSoup(page.content, 'lxml')

        recipes = soup.findAll('div', {'class': 'box-articoli-hp'})

        for r in recipes:
            x = r.find('a')['href']
            recipe_URL = base_URL + x
            pages_cucchiaio.append(recipe_URL)

        counter = counter + 1

    with open('pages_cucchiaio.json', 'w') as outfile:
        json.dump(pages_cucchiaio, outfile)


def get_pages_tasty():
    URL = 'https://tasty.co/sitemaps/tasty/sitemap.xml'

    page = requests.get(URL, headers=HEADERS)
    sitemap_dict = xmltodict.parse(page.text)

    all_url = [r["loc"] for r in sitemap_dict["urlset"]["url"]]

    recipe_url = []
    for url in all_url:
        if 'tasty.co/recipe/' in url:
            recipe_url.append(url)

    with open('pages_tasty.json', 'w') as outfile:
        json.dump(recipe_url, outfile)


def get_pages_giallozafferano():
    counter = 1
    pages_giallozafferano = []
    while counter < 370:

        page_URL = 'https://www.giallozafferano.it/ricette-cat/page{}/'.format(counter)

        page = requests.get(page_URL, headers=HEADERS)
        soup = BeautifulSoup(page.content, 'lxml')

        recipes = soup.findAll('h2', {'class': 'gz-title'})

        for r in recipes:
            recipe_URL = r.find('a')['href']
            pages_giallozafferano.append(recipe_URL)

        counter = counter + 1

    with open('pages_giallozafferano.json', 'w') as outfile:
        json.dump(pages_giallozafferano, outfile)
