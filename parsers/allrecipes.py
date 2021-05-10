
import re
import json
import requests
from bs4 import BeautifulSoup
from utilities import get_minutes


class AllRecipes():

    def __init__(self, url_path):
        HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        }

        page = requests.get(url_path, headers=HEADERS)
        self.soup = BeautifulSoup(page.content, 'lxml')

        json_ld = self.soup.find('script', {'type': 'application/ld+json'}).contents
        json_ld = json.loads(''.join(json_ld))

        for json_data in json_ld:
            if json_data['@type'] == 'Recipe':
                break
        self.json = json_data

    @classmethod
    def host(self):
        return 'allrecipes.com'

    def title(self):
        return self.soup.find('meta', {'property': 'og:title'})['content']

    def total_time(self):
        try:
            minutes = self.json['totalTime']
        except:
            minutes = ''
        return get_minutes(minutes)

    def ingredients(self):
        try:
            ingredients = self.soup.find_all('li', {'class': 'ingredients-item'})
        except:
            ingredients = []

        ingredient_list = []
        for ingredient in ingredients:
            b = {}
            try:
                ing = ingredient.find('input')['data-ingredient']
                quantity = ingredient.find('input')['data-quantity'] + ' ' + ingredient.find('input')['data-unit']
                qty = quantity.strip().replace('\u2009', ' ')
            except Exception:
                continue
            b['ingredient'] = ing
            b['quantity'] = qty
            ingredient_list.append(b)
        return ingredient_list

    def instructions(self):
        try:
            instruction_steps = [step['text'] for step in self.json['recipeInstructions']]
            instructions = '\n'.join(instruction_steps)
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
            language = ''
        return language

    def yields(self):
        try:
            servings = re.search(r'(^[\d.]+)(.*)', self.json['recipeYield']).group(1).strip()
            label = re.search(r'(^[\d.]+)(.*)', self.json['recipeYield']).group(2).strip()
        except:
            servings = ''
            label = ''
        return servings + ' ' + label


