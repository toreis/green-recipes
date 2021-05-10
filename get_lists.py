
from utilities import recipe_to_df
import sql_queries
import pandas as pd
import json


def get_recipe_list(id_range):
    """Get a list of all recipes for selected recipe_id range"""
    appended_recipes = list()
    for r in id_range:
        try:
            print(r)
            recipe = sql_queries.get_recipe_by_id(r, True)
            df = recipe_to_df(recipe, True)
            appended_recipes.append(df)
        except:
            pass
    appended_recipes = pd.concat(appended_recipes)
    appended_recipes.to_csv('recipes_full.csv', index=False, header=True)


def get_ingredient_list(id_range):
    """Get a list of all ingredients for selected recipe_id range"""
    appended_ingredients = list()
    for r in id_range:
        try:
            print(r)
            recipe = sql_queries.get_recipe_by_id(r, True)
            for i in recipe['ingredients']:
                appended_ingredients.append(i['ingredient'])
        except:
            pass

    with open('all_ingredients.json', 'w') as f:
        json.dump(appended_ingredients, f)
