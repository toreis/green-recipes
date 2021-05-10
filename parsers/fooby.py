
import re
import json
import requests
from bs4 import BeautifulSoup
from utilities import get_minutes


class Fooby:

    def __init__(self, url_path):

        HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        }

        page = requests.get(url_path, headers=HEADERS)
        self.soup = BeautifulSoup(page.content, 'lxml')

        for script in self.soup.find_all('script'):
            script = str(script)

            if re.search(r'var\s+recipeJSON\s+=\s+(.*);', script) is not None:
                json_data = re.search(r'var\s+recipeJSON\s+=\s+(.*);', script)[1]
                break
        self.json = json.loads(json_data)

    @classmethod
    def host(self):
        return 'fooby.ch'

    def language(self):
        try:
            language = self.soup.find('html')['lang']
        except:
            language = ''
        return language

    def title(self):
        try:
            title = self.soup.find('meta', {'property': 'og:title'})['content'].strip()
        except:
            title = ''
        return title

    def ingredients(self):
        try:
            ingredients = self.soup.find_all('div', {'itemprop': 'recipeIngredient'})
        except:
            ingredients = []

        ingredient_list = []
        for ingredient in ingredients:
            b = {}
            b['ingredient'] = ingredient.find('span', class_='recipe-ingredientlist__ingredient-desc').text.strip()
            b['quantity'] = ingredient.find('span', class_='recipe-ingredientlist__ingredient-quantity').text.strip()
            ingredient_list.append(b)
        return ingredient_list

    def instructions(self):
        try:
            instructions = self.soup.find('div', {'itemprop': 'recipeInstructions'}).text
            instructions = re.sub(r'\n+', '\n', instructions).strip()
        except:
            instructions = ''
        return instructions

    def image(self):
        try:
            picture_url = self.soup.find('meta', {'property': 'og:image'})['content']
        except:
            picture_url = ''
        return picture_url

    def total_time(self):
        try:
            preptime = self.soup.find('span', {'itemprop': 'totalTime'})['content']
            minutes = re.search(r'\d+', preptime).group(0)
        except:
            minutes = ''
        return get_minutes(minutes)

    def yields(self):
        try:
            servings = self.soup.find('span', {'id': 'portionValueSpan'})['data-portion-calculator-initial-portions']
            label = self.soup.find('span', {'class': 'portion-calculator__display-label'}).text
        except:
            servings = ''
            label = ''
        return servings + ' ' + label

    def nutrients(self):

        nutrients = {}

        try:
            nutrients['calories'] = self.soup.find('span', {'itemprop': 'calories'}).text
        except Exception:
            pass
        try:
            nutrients['fatContent'] = self.soup.find('span', {'itemprop': 'fatContent'}).text
        except Exception:
            pass
        try:
            nutrients['carbohydrateContent'] = self.soup.find('span', {'itemprop': 'carbohydrateContent'}).text
        except Exception:
            pass
        try:
            nutrients['proteinContent'] = self.soup.find('span', {'itemprop': 'proteinContent'}).text
        except Exception:
            pass

        return nutrients


