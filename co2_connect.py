
import re
from fuzzywuzzy import fuzz
import pandas as pd
import numpy as np
from utilities import Quantity
from utilities import clean_text, find_words
import os

# Fetch all relevant data
PATH = os.getcwd()

attributes = pd.read_csv(PATH + r'/data/attributes.csv').fillna('')

weights = pd.read_csv(PATH + r'/data/weights.csv').fillna('')
conv = pd.read_csv(PATH + r'/data/measurements.csv').fillna('').values.tolist()
density_list = pd.read_csv(PATH + r'/data/food_densities.csv').fillna('').values.tolist()

filler_lists = {'en': pd.read_csv(PATH + r'/data/filler_strings.csv')['en'].values.tolist(),
                'de': pd.read_csv(PATH + r'/data/filler_strings.csv')['de'].values.tolist(),
                'it': pd.read_csv(PATH + r'/data/filler_strings.csv')['it'].values.tolist()}

reference_lists = {'en': pd.read_csv(PATH + r'/data/reference_list_en.csv'),
                   'de': pd.read_csv(PATH + r'/data/reference_list_de.csv'),
                   'it': pd.read_csv(PATH + r'/data/reference_list_it.csv')}

# === CO2 add function ===

def co2_add(recipe_json):
    """Matches ingredients from the recipe with CO2 values and calculates the recipes ecological footprint"""

# Create a copy of the recipe json
    recipe_co2 = recipe_json.copy()

    # Supported languages with their corresponding codes
    languages = {'en': 0,
                 'de': 1,
                 'it': 2
                 }
    
    try:
        lang = recipe_co2['language'].lower()
    except KeyError:
        # If language is not specified in recipe prompt users to enter language
        lang = input('Please specify the recipes language {}: '.format([*languages])).lower()
        recipe_co2['language'] = lang

    # Split if language includes designation for counties or regions e.g. en-us
    lang = lang.split('-')[0]

    lang_code = None
    while lang_code is None:
        try:
            lang_code = languages[lang]
        except KeyError:
            # If language is not supported prompt users to enter supported language
            print('language "' + lang + '" not supported')
            lang = input('Please specify the recipes language {}: '.format([*languages])).lower()
            recipe_co2['language'] = lang

    # Select reference list for specified language
    full_list = reference_lists[lang]

    # Get list of filler strings
    filler_list = filler_lists[lang]
    filler_reg = re.compile(r'\b(%s)\S?\b' % '|'.join(filler_list), re.IGNORECASE)
    
    # Initialize values
    nomatchcount = 0
    noquantitycount = 0
    co2_values = list()
    ingweights = list()

    # === Parse all ingredients in the recipe ===
    for r in recipe_co2['ingredients']:

        qty = r['quantity']
        ing = r['ingredient']

        ing_orig = ing

        # Initialize warnings
        warnings = {}
        nomatch = False
        noco2 = False
        avg = False
        sim = False
        nodensity = False

        # Check if attribute is specified in the ingredient entry
        ing_attributes = list()
        for index, row in attributes.iterrows():
            if row[lang] in ing:
                ing_attributes.append(row['en'])

        # Remove filler strings from ingredient and quantity
        try:
            ing = re.sub(filler_reg, '', ing).strip()
        except TypeError:
            pass
        try:
            qty = re.sub(filler_reg, '', qty)
            qty = re.sub(r'clove\D*', '', qty).strip()
        except TypeError:
            pass

        quantity_object_qty = Quantity(qty)
        
        # === Determine quantity of ingredient ===
        
        # Get unit, count and quantity from the Quantity class
        unit = quantity_object_qty.unit
        count = quantity_object_qty.count
        qty = quantity_object_qty.qty_qty()

        # If quantity could not be determined look if quantity is specified in ingredients and set qty accordingly
        if qty is None:
            quantity_object_ing = Quantity(ing)
            unit = quantity_object_ing.unit
            count = quantity_object_ing.count

            if unit is not None:
                qty = quantity_object_ing.qty_ing()

        # Final cleanup of ing by removing digits
        ing = re.sub(r'[0-9]', '', ing).strip()
        
        # === Match ingredient with entry in reference list ===
        
        # Calculate the Levenshtein Distance for all ingredient pairs and sort them
        full_list['score'] = full_list.apply(lambda row: (fuzz.partial_ratio(row['ref'], ing) * 0.5 +
                                                          fuzz.token_sort_ratio(row['ref'], ing) * 0.5), axis=1)

        final_df = full_list.sort_values(by=['score'], ascending=False)

        co2_calc = list()
        for scr in range(10):

            if find_words(ing_orig, final_df.iloc[scr].ref):

                # If the ingredients attribute matches the attribute in the refence list choose that match
                if final_df.iloc[scr]['attribute'] in ing_attributes:
                    match = final_df.iloc[scr]
                    break

                match = final_df.iloc[scr]
                if not pd.isna(final_df.iloc[scr].co2):
                    co2_calc.append(final_df.iloc[scr].co2)

                # Check if the next best match is the same (to take average co2 value for 
                # ingredients with different attributes in reference list)
                if match.ref == final_df.iloc[scr + 1].ref:
                    continue
                else:
                    # If multiple indendical matches and no attribute is specified take average co2
                    if len(co2_calc) > 1:
                        match.co2 = sum(co2_calc) / len(co2_calc)
                        avg = True
                    break

        else:
            nomatch_data = {'en_key': 'nomatch',
                            'ref': ing,
                            'lang_key': ing,
                            'type': np.nan,
                            'co2': 'NaN',
                            'classification': np.nan,
                            'attribute': np.nan,
                            'variety': np.nan,
                            'score': np.nan}
            match = pd.Series(nomatch_data)

            nomatchcount = nomatchcount + 1
            nomatch = True
            noco2 = True

       # If similarity of match is below threshold add warning
        if float(match.score) < 80:
            sim = True
        
        # If no match was found add warning
        if pd.isna(match.co2):
            noco2 = True
            match.co2 = None

        # === Calculate the weight in grams from qunatity specification ===
        ingre = match.en_key
        co2kg = match.co2
        ingweight = None

        if qty is None:
            ingweight = None

        # Piece count: Try to determine weight if quantity is a piece count
        if qty is not None and 'piece' in qty:
            try:
                weight = weights.loc[weights['en'] == ingre]['weight'].values[0]
                ingweight = round(weight * count, 5)
            except IndexError:
                # If weight of piece is not in list search for weight in ingredient and multiply with piece count
                # assuming that the weight specification is for each piece and not the total of all pieces
                quantity_object_ing = Quantity(ing_orig)
                unit2 = quantity_object_ing.unit
                count2 = quantity_object_ing.count
                if unit2 and count2 is not None:
                    count = count * count2
                    unit = unit2
                    qty = str(count) + ' ' + unit
                else:
                    ingweight = None

        # Measurement: Look up weight of measurement
        if unit is not None:
            for c in conv:
                for m in c[1].split(','):
                    if unit.lower() == m.strip().lower() and c[2] != '':
                        if count is None:
                            # For 'a little' etc set count to 1
                            count = 1
                        density = None
                        # Check if ingredient is in density list if volume measurement
                        if c[3] == 'volume':
                            for d in density_list:
                                if ingre == d[0]:
                                    # Check if attribute is specified.
                                    # If not take the average of all densities
                                    if d[1] in ing_attributes:
                                        density = d[2]
                                    else:
                                        density = d[3]
                            # Standard density of one if density for ingredient is not in list
                            if density is None:
                                density = 1
                                if nomatch is False:
                                    nodensity = True
                            # Calculate the weight in grams of volume measure with the determined density
                            ingweight = round(c[2] * float(density) * count, 5)
                            break

                        else:
                            # Calculate the weight in grams if mass measure
                            ingweight = round(float(c[2]) * count, 5)
                            break

        # Add weight to list for total weight calculation
        if ingweight is not None:
            ingweights.append(ingweight)
        
        # === Calculate CO2 value for given ingredient weight ===
        if ingweight is not None and noco2 is False:
            onegram = float(co2kg) / 1000
            co2 = round(onegram * float(ingweight), 5)

            co2_values.append(co2)

        # If weight in grams cannot determined add measure to missing quantity list and set co2 to none
        elif ingweight is None:
            co2 = None
            noquantitycount = noquantitycount + 1

        # Quantity in grams determined but no match
        else:
            co2 = None
        
        if co2kg == 'NaN':
            co2kg = None
            
        # === Update ingredient dictionary ===
        
        # Replace ingre in dictionary with cleaned up ingredient if no match
        if ingre == 'nomatch':
            # Split ingredient at certain words, ',' and '('
            ing_split = re.sub(r'\b(or|oder|o)\b|([()])', ',', ing)
            ing_split = ing_split.split(',')

            ingre = clean_text(ing_split[0])
            match.lang_key = ing_split[0].strip()

        # Update warnings for ingredient
        warnings['nomatch'] = nomatch
        warnings['sim'] = sim
        warnings['avg'] = avg
        warnings['nodensity'] = nodensity

        # Add new entries to the ingredient dictionary
        r['ingredient_clean'] = ingre
        r['ingredient_clean_lang'] = match.lang_key
        r['weight'] = ingweight
        r['co2kg'] = co2kg
        r['quantity_clean'] = qty
        r['co2'] = co2

        r['attributes'] = ing_attributes
        r['warnings'] = warnings
        
        
    # === Update recipe dictionary ===
    
    # Calculate co2 and weight totals
    co2_total = round(sum(co2_values), 5)
    weight_total = round(sum(ingweights), 5)

    # Add new entries to the recipe dictionary
    recipe_co2['co2_total'] = co2_total
    recipe_co2['weight_total'] = weight_total
    recipe_co2['noquantity'] = noquantitycount
    recipe_co2['nomatch'] = nomatchcount

    return recipe_co2


