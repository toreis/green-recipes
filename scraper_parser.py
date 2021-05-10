import re
import time

import requests
from recipe_scrapers import scrape_me

import database_queries
from co2_connect import co2_add
from parsers import AllRecipes, Chefkoch, Fooby, ParseString
from utilities import Quantity


SCRAPERS = {
    AllRecipes.host(): AllRecipes,
    Fooby.host(): Fooby,
    Chefkoch.host(): Chefkoch,
    ParseString.host(): ParseString
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
}


def url_path_to_dict(url_path):
    """Divides an URL into its structure."""
    pattern = (r'^'
               r'((?P<schema>.+?)://)?'
               r'(?P<host>.*?)'
               r'(?P<path>/.*?)?'
               r'(?P<query>[?].*?)?'
               r'$'
               )
    regex = re.compile(pattern)
    matches = regex.match(url_path)
    url_dict = matches.groupdict() if matches is not None else None

    return url_dict


def recipe_scraper(url_path):
    """Selects correct scraper for the given URL or string."""
    try:
        # Check if input string is an URL
        requests.get(url_path, headers=HEADERS)
        is_url = True
    except:
        is_url = False

    if is_url is True:
        # If input string is an URL select correct scraper/parser
        url_path = url_path.replace('://www.', '://')
        host = url_path_to_dict(url_path)['host']
        try:
            return SCRAPERS[host](url_path)
        except KeyError:
            return scrape_me(url_path)
    else:
        # If input string is not an URL select string parser
        x = url_path_to_dict('string_parser')
        soup = url_path
        return SCRAPERS[x['host']](soup)


def recipe_parser(url_path, recipe_id=None):
    """Parses the scraped recipe and saves it in a unified format."""
    try:
        recipe_obj = recipe_scraper(url_path)
    except:
        recipe_obj = scrape_me(url_path, wild_mode=True)

    recipe = {'recipe_id': recipe_id,
              'URL': url_path,
              'title': recipe_obj.title()}
    ingredients = recipe_obj.ingredients()

    ingredients_qty = list()
    for ing in ingredients:
        # If ingredient is not yet split up into quantity and ingredient do so
        if not isinstance(ing, dict):
            quantity_obj = Quantity(ing)
            ing_dict = {'ingredient': quantity_obj.ing(),
                        'quantity': quantity_obj.qty_ing()}
            ingredients_qty.append(ing_dict)
        else:
            ingredients_qty.append(ing)

    # Build recipe dictionary
    recipe['ingredients'] = ingredients_qty
    recipe['instructions'] = recipe_obj.instructions()
    recipe['image'] = recipe_obj.image()
    recipe['totalTime'] = recipe_obj.total_time()
    recipe['recipeYield'] = recipe_obj.yields()
    recipe['nutrients'] = recipe_obj.nutrients()
    recipe['language'] = recipe_obj.language()
    recipe['scraped'] = time.ctime(time.time())

    return recipe


# === For scraping and saving directly to the database ==

def add_urls_to_db(URLs):
    """Adds new URLs to be scraped to the database"""
    for URL in URLs:
        print(URL)
        database_queries.insert_recipe_URL(URL)


def scrape_parse_url(recipe_id):
    """Scrapes and parses recipe of URL in db for specified recipe_id"""
    URL = database_queries.get_URL_by_id(recipe_id)

    if URL is None:
        print('no URL for this id')
    else:
        print(URL)
        recipe = recipe_parser(URL, recipe_id)
        database_queries.update_recipe(recipe, recipe_id)

        print(recipe['recipe_id'], recipe['title'])

        recipe_co2 = co2_add(recipe)
        database_queries.update_recipe_co2(recipe_co2, recipe_id)


def parse_recipe_id(recipe_id):
    """Update CO2 values for selected recipe"""
    recipe = database_queries.get_recipe_by_id(recipe_id)

    if recipe is not None:
        print(recipe['recipe_id'], recipe['title'])

        recipe_co2 = co2_add(recipe)
        database_queries.update_recipe_co2(recipe_co2, recipe_id)
    else:
        scrape_parse_url(recipe_id)
