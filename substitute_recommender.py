import pandas as pd

from co2_connect import co2_add
from scraper_parser import recipe_parser
from utilities import recipe_to_df
import database_queries


def list_replacement_candidates_of_recipe(recipe_df, co2_threshold=2):
    """Determines ingredients with high emissions that should be replaced"""

    df = recipe_df

    replacement_candidates = df.loc[df['co2kg'] > co2_threshold].sort_values(
        by=['co2'], ascending=False
    )

    return replacement_candidates[['ingredient_clean', 'co2', 'weight', 'co2kg']]


def list_substitutes_for_ingredient(candidate, substitutes):
    """Finds substitutes for the replacement candidate.
    Candidate is the whole row from the ingredients df, substitutes is substitutes dictionary
    """
    
    ingredient_clean = candidate['ingredient_clean']
    co2kg = candidate['co2kg']

    try:
        substitute_candidates = substitutes[ingredient_clean]
        substitute_candidates_df = pd.DataFrame(
            substitute_candidates,
            columns=['ingredient', 'score', 'co2kg', 'attribute', 'classification'],
        )
        substitute_candidates_df = substitute_candidates_df.loc[
            substitute_candidates_df['co2kg'] < co2kg
        ].round(decimals=3)
    except KeyError:
        substitute_candidates_df = pd.DataFrame()

    return substitute_candidates_df


def compute_footprint_reduction(recipe, ingredient, substitute):
    """Calculate the co2 footprint reduction of the recipe for the chosen substitution"""
    substitute_co2kg = substitute['co2kg']
    substitute_co2 = candidate['weight'] * substitute_co2kg / 1000

    co2_saving = ingredient['co2'] - substitute_co2
    co2_total_orig = recipe['co2_total']
    co2_total_sub = co2_total_orig - co2_saving

    return round(100 - co2_total_sub / co2_total_orig * 100, 2)


if __name__ == '__main__':
    import json
    import sys

    # === Demo recipe URL ===
    
    # String can be an URL or all ingredients in text form (delimited by ';' or '\n')
    # From user input on the web application
    
    # file = open(r'C:\Users\user\OneDrive\Studium\MastersThesis\example_recipe.txt', 'r', encoding='utf-8')
    # string = file.read()
    string = 'https://fooby.ch/en/recipes/19371/asian-grilled-roast-pork-?startAuto1=0'

    recipe = recipe_parser(string)
    recipe_co2 = co2_add(recipe)
    
    # Alternatively load recipe form database to be analyzed
    # recipe_co2 = database_queries.get_recipe_by_id(1, True)

    df = recipe_to_df(recipe_co2).round(decimals=3)

    print('CO2 emissions and weights of ingredients of the parsed recipe:')
    print(df[['ingredient_clean', 'co2', 'weight', 'co2kg']].to_string(index=False))
    print('\n')

    with open('substitutes.json') as data:
        substitute_dict = json.load(data)

    ingredients = list_replacement_candidates_of_recipe(df)
    if ingredients.empty:
        print('No ingredients with high emissions that should be replaced.')
        sys.exit(0)

    candidate = ingredients.iloc[0]
    substitute_candidates_df = list_substitutes_for_ingredient(
        candidate, substitute_dict
    )

    if substitute_candidates_df.size > 0:
        print('Alternatives for {} with lower CO2 emissions:'.format(candidate['ingredient_clean']))
        
        print(substitute_candidates_df.to_string(index=False))

        substitute = None
        while substitute is None:
            choice = input('Choose a substitute for {} (index): '.format(candidate['ingredient_clean']))
            try:
                substitute = substitute_candidates_df.iloc[[choice]].iloc[0]
            except IndexError:
                print('Index not in list')
            except ValueError:
                print('Choose index (number) of substitute')

        co2_saving_percent = compute_footprint_reduction(recipe_co2, candidate, substitute)

        print('\n')
        print('By replacing {} with {} the recipes ecological footprint can be reduced by {} percent!'
              .format(candidate['ingredient_clean'], substitute['ingredient'], co2_saving_percent))

    else:
        print('No substitutes for {} that would lower CO2 emissions.'.format(candidate['ingredient_clean']))



