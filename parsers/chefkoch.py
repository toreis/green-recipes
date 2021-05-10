
import re
import json
import requests
from bs4 import BeautifulSoup
from utilities import get_minutes


class Chefkoch:

    def __init__(self, url_path):
        HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        }

        page = requests.get(url_path, headers=HEADERS)
        self.soup = BeautifulSoup(page.content, 'lxml')

        json_ld = self.soup.find_all('script', type='application/ld+json')[-1]

        json_ld = str(json_ld).replace('\n', '')
        json_data = re.search(r'\{(.+)\}', json_ld).group(0)
        self.json = json.loads(json_data)

    @classmethod
    def host(self):
        return 'chefkoch.de'

    def title(self):
        try:
            title_div = self.soup.find('div', {'class': 'ds-mb ds-mb-col'})
            title = title_div.find('h1', {'class': ''}).text
        except:
            title = ''
        return title

    def total_time(self):
        try:
            time = self.json['totalTime']
        except:
            time = ''

        return get_minutes(time)

    def ingredients(self):
        try:
            results = self.soup.find('article', class_='recipe-ingredients')
            ingredients = results.find_all('tr')
        except:
            ingredients = []

        ingredient_list = []

        for ingredient in ingredients:
            b = {}
            try:
                ing = ingredient.find('td', class_='td-right').text.strip()
                qty = ingredient.find('td', class_='td-left').text.strip()
                qty = ' '.join(qty.split())
            except Exception:
                continue
            b['ingredient'] = ing
            b['quantity'] = qty
            ingredient_list.append(b)
        return ingredient_list

    def instructions(self):
        try:
            title = self.soup.find('h2', text='Zubereitung')
            instructions = title.findNext('div').text.strip().replace('\n\r', '')
        except:
            instructions = ''
        return instructions

    def image(self):
        try:
            picture_url = self.soup.find('meta', {'property': 'og:image'})['content']
        except:
            picture_url = ''
        return picture_url

    def nutrients(self):

        nutrients = {}
        try:
            nutrients['calories'] = self.json['nutrition']['calories']
        except Exception:
            pass

        try:
            nutrients['fatContent'] = self.json['nutrition']['fatContent']
        except Exception:
            pass

        try:
            nutrients['carbohydrateContent'] = self.json['nutrition']['carbohydrateContent']
        except Exception:
            pass

        try:
            nutrients['proteinContent'] = self.json['nutrition']['proteinContent']
        except Exception:
            pass

        return nutrients

    def language(self):
        try:
            language = self.soup.find('html')['lang']
        except:
            language = 'NaN'
        return language

    def yields(self):
        try:
            counter = self.soup.find('div', {'class': 'recipe-servings ds-box'})
            servings = counter.find('input')['value']
            label = counter.find('input')['name']
        except:
            servings = 'NaN'
            label = 'NaN'
        return servings + ' ' + label

