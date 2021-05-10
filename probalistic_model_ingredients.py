"""
Adapted from:
https://flothesof.github.io/probabilistic-ingredients.html
"""

import pandas as pd
import re
from collections import Counter
import itertools
from collections import defaultdict
from utilities import clean_text
import json
import os

PATH = os.getcwd()

filler_list = pd.read_csv(PATH + r'/data/filler_strings.csv')['de'].values.tolist()
filler_reg = re.compile(r'\b(%s)\S?\b' % '|'.join(filler_list), re.IGNORECASE)

with open('all_ingredients.json') as f:
    all_ingredients_text1 = json.load(f)

# In[1]:

# Clean ingredients and remove filler strings
all_ingredients_text = []
for i in all_ingredients_text1:
    clean_ing = re.sub(filler_reg, '', i)
    clean_ing = clean_text(clean_ing)
    all_ingredients_text.append(clean_ing)

splitter = re.compile('[,. ]+')
all_words = []
for ingredient in all_ingredients_text:
    all_words += re.split(splitter, ingredient)


def to_ingredient(text):
    """Transforms text into an ingredient."""
    return frozenset(re.split(re.compile('[,. ]+'), text))


all_ingredients = [to_ingredient(text) for text in all_ingredients_text]


def candidates(ingredient):
    """Returns a list of candidate ingredients obtained from the original ingredient by keeping at least one of them."""
    n = len(ingredient)
    possible = []
    for ing in range(1, n + 1):
        possible += [frozenset(combi) for combi in itertools.combinations(ingredient, ing)]
    return possible


c = Counter(all_ingredients)

probability = defaultdict(lambda: 1, c.most_common())


# In[2]:

def candidates_increasing_distance(ingredient, vocabulary):
    """Returns candidate ingredients obtained from the original ingredient by substraction, largest number of
    ingredients first."""
    n = len(ingredient)
    for ing in range(n - 1, 1, -1):
        possible = [frozenset(combi) for combi in itertools.combinations(ingredient, ing)
                    if frozenset(combi) in vocabulary]
        if len(possible) > 0:
            return possible
    return [ingredient]


vocabulary = dict(c.most_common())


def best_replacement_increasing_distance(ingredient, vocabulary):
    """Computes best replacement ingredient for a given input."""
    return max(candidates_increasing_distance(ingredient, vocabulary), key=lambda w: vocabulary[w])


df1 = pd.DataFrame([(text,
                     ''.join(best_replacement_increasing_distance(to_ingredient(text), vocabulary)))
                    for text in sorted(set(all_ingredients_text), key=len, reverse=True)],
                   columns=['original ingredient', 'improved ingredient'])


def improve_ingredients(ingredient_list):
    """Improves the list of ingredients given as input."""
    better_ingredients = []
    for ingredient in ingredient_list:
        cleaned_ingredient = clean_text(ingredient)
        if vocabulary[to_ingredient(cleaned_ingredient)] <= 100:
            better_ingredients.append(''.join(best_replacement_increasing_distance(
                to_ingredient(cleaned_ingredient), vocabulary)))
        else:
            better_ingredients.append(cleaned_ingredient)
    return better_ingredients


better_ingredients_text = improve_ingredients(all_ingredients_text)

d = {'original': all_ingredients_text1, 'better': better_ingredients_text}

df = pd.DataFrame(d)

# In[2]:

count = Counter(better_ingredients_text)
ingredients_df = pd.DataFrame.from_dict(count, orient='index').reset_index().sort_values(0, ascending=False)

head = ingredients_df.head(1000)
# ingredients_df.to_csv('ingredients.csv', index = False, header=True)
