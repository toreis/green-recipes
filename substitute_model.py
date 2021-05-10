
import json
import os
from collections import Counter
import numpy as np
import pandas as pd
import gensim

from utilities import clean_text

PATH = os.getcwd()

# Fetch all relevant data
reference_list = pd.read_csv(PATH + r'/data/reference_list_en.csv') \
    [['en_key', 'co2', 'attribute', 'classification']].drop_duplicates()
df = pd.read_csv('recipes_full.csv')

# Group recipes by recipe id
grouped = df.groupby('recipe_id')

# Get the ingredient with the highest emissions for each recipe
idx = df.groupby(['recipe_id'])['co2'].transform(max) == df['co2']
max_co2 = df[idx]
max_co2_ing = max_co2['ingredient_clean'].value_counts().reset_index()


# In[1]:

# Get a list of all ingredients grouped by recipes
ingredients = list()
for name, group in grouped:
    print(name)
    
    ing_r = list()
    for ing in group['ingredient_clean']:
        ing = clean_text(str(ing))
        if len(ing) > 0:
            ing_r.append(ing)

    # Only keep recipes with more than 2 ingredients
    if len(ing_r) > 2:
        ingredients.append(ing_r)
        
# In[2]:

# Maximum number of ingredients in a recipe
max_ing = max(map(len, ingredients))

# Count number of occurrences of each ingredient
ing_counts = Counter()
for i, ingredient in enumerate(ingredients):
    for token in ingredient:
        ing_counts[token] += 1

common = ing_counts.most_common(100)
common_df = pd.DataFrame(common, columns=['ingredient', 'count'])

# Ststistics: percentiles of occurrences
print(np.percentile(list(ing_counts.values()), [25., 50., 75., 99.]))

# In[3]:

# Initialize and train the CBOW Word2Vec model
model = gensim.models.Word2Vec(ingredients, # Recipes as sentences
                               vector_size=100,
                               min_count=50, # Ignores ingredients with less occurrences
                               window=max_ing, # Maximum number of ingredients in a recipe
                               workers=8,
                               epochs=50) # Number of iterations over the corpus

print(model.wv.most_similar('beef'))

model.save('ing_similarity.model')

# In[4]:

# Compile substitute dictionary including information on CO2 emission and attributes
substitutes = dict()
for ingredient in ing_counts.keys():
    try:
        sub = model.wv.most_similar(ingredient)
        sub_df = pd.DataFrame(sub, columns=['candidate', 'score'])

        # Only keep substitutes if similarity is higher than threshold
        sub_df = sub_df.loc[sub_df['score'] > 0.5]
    except KeyError:
        sub_df = pd.DataFrame()
    if len(sub_df.index) > 0:
        candidates_co2 = pd.merge(left=sub_df,
                                  right=reference_list,
                                  left_on='candidate',
                                  right_on='en_key',
                                  how='inner').drop('en_key', axis=1)
        candidates_co2 = [tuple(r) for r in candidates_co2.to_numpy()]
        substitutes[ingredient] = candidates_co2

# In[5]:

# Save substitute dictionary
with open('substitutes.json', 'w') as f:
    json.dump(substitutes, f)
