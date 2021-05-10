
import re
import pandas as pd
import unidecode

import os

PATH = os.getcwd()
conv = pd.read_csv(PATH + r'/data/measurements.csv').fillna('').values.tolist()

# Get list of measurements
all_units = list()
for c in conv:
    for m in c[1].split(','):
        all_units.append(m.replace('.', '\.').strip())


def recipe_to_df(recipe, fullmatch=False):
    """This function takes a recipe json and returns it as a pandas dataframe
    If fullmatch is True the recipe is only returned when it has matches for all ingredients.
    """

    recipe_id = recipe['recipe_id']
    nomatch = recipe['nomatch']

    if fullmatch:
        if nomatch == 0:
            ing_df = pd.DataFrame()
            for i in recipe['ingredients']:
                df = pd.DataFrame(list(i.items())).set_index(0).transpose()
                ing_df = ing_df.append(df)

            part_df = ing_df[['ingredient_clean', 'co2kg']]
            ing_grouped = ing_df.groupby(['ingredient_clean'])[["co2", "weight"]].sum().reset_index()

            merged = pd.merge(ing_grouped,
                              part_df,
                              on='ingredient_clean',
                              how='inner')
        else:
            merged = pd.DataFrame()
    else:
        ing_df = pd.DataFrame()
        for i in recipe['ingredients']:
            df = pd.DataFrame(list(i.items())).set_index(0).transpose()
            ing_df = ing_df.append(df)

        part_df = ing_df[['ingredient_clean', 'co2kg']]
        ing_grouped = ing_df.groupby(['ingredient_clean'])[["co2", "weight"]].sum().reset_index()

        merged = pd.merge(ing_grouped,
                          part_df,
                          on='ingredient_clean',
                          how='inner')

    sum_co2 = merged[(merged['co2'] > 0)]['co2'].sum()
    sum_weights = merged[(merged['weight'] > 0)]['weight'].sum()

    merged['co2_share'] = merged.co2 / sum_co2
    merged['weight_share'] = merged.weight / sum_weights

    merged.insert(0, 'recipe_id', recipe_id)
    merged['noco2'] = merged.apply(lambda row: row['co2kg'] is None, axis=1)

    merged = merged.drop_duplicates(subset='ingredient_clean')

    return merged


def get_minutes(element):
    """This function determines time in minutes from input string."""
    if element is None:
        return 0

    # Return minutes if string already is an integer
    try:
        return int(element)
    except Exception:
        pass

    if isinstance(element, str):
        time_text = element
    else:
        time_text = element.get_text()
    if time_text.startswith('P') and 'T' in time_text:
        time_text = time_text.split('T', 2)[1]
    if '-' in time_text:
        # Sometimes formats are like this: '12-15 minutes'
        time_text = time_text.split('-', 2)[1]
    if 'h' in time_text:
        time_text = time_text.replace('h', 'hours') + 'minutes'

    TIME_REGEX = re.compile((r'(\D*(?P<hours>\d+)\s*(hours|hrs|hr|h|óra|ora|stunde))?'
                             r'(\D*(?P<minutes>\d+)\s*(minutes|mins|min|m|perc))?'),
                            re.IGNORECASE, )

    matched = TIME_REGEX.search(time_text)

    minutes = int(matched.groupdict().get('minutes') or 0)
    minutes += 60 * int(matched.groupdict().get('hours') or 0)

    return minutes


def find_words(text, search):
    """This function determines if individual words from string are in the target text."""
    search = clean_text(search)
    text = clean_text(text)

    search_split = set(search.split())

    return len(search_split & set(text.split())) == len(search_split)


def clean_text(text):
    """This function represents unicode caracters in ASCII characters and cleans input string."""
    text = unidecode.unidecode(text).lower().replace('-', ' ').strip()
    text = re.sub(r'[^a-zA-Z\s]+', '', text)
    text = re.sub(r'\b\S\b', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def fraction_replace(text):
    """This function transforms (unicode) fractions into decimals."""
    fraction_dict = {
        '½': '.5',
        '⅓': '.33',
        '⅔': '.67',
        '¼': '.25',
        '¾': '.75',
        '⅕': '.2',
        '⅛': '.125',
        '⅞': '.875',
        '1/2': '.5',
        '1/3': '.33',
        '2/3': '.67',
        '1/4': '.25',
        '3/4': '.75',
        '1/5': '.2',
        '1/8': '.125',
        '7/8': '.875'
    }
    for key in fraction_dict:
        text = text.replace(key, fraction_dict[key])
    return text


class Quantity:

    def __init__(self, string):

        if string is None:
            string = 'NaN'

        string = fraction_replace(string)
        self.orig_string = string
        self.all_units = '|'.join(all_units)

        # finds numbers in and right in before parentheses '2 (100 g) cans'
        par_reg = r'(\d*\.?\,?\d+)+\s?\(\s?(\d*\.?\,?\d+)+'
        # finds two following numbers 
        num_reg = r'(\d*\.?\,?\d+)\s+(\d*\.?\,?\d+)'

        par_pairs = re.finditer(par_reg, string)
        num_pairs = re.finditer(num_reg, string)

        # replace e.g. 1 0.25 kg with 1.25 kg
        for n in num_pairs:
            sums = str(float(n[1].replace(',', '.')) + float(n[2].replace(',', '.')))
            string = string.replace(n[0], sums)

        # replace e.g. '2 (100 g) cans' with 200 g
        for n in par_pairs:
            sums = str(float(n[1].replace(',', '.')) * float(n[2].replace(',', '.')))
            string = string.replace(n[0], sums)
            string = string.replace(')', '')

        pattern = (r'(?P<count>(\d*\.?\,?\d+))?\s*'
                   r'((?:^|(?<=\d|\s))(?P<unit>%s)\b)?'
                   )

        # regex for quantity
        UNIT_REGEX = re.compile(pattern % self.all_units, re.IGNORECASE)
        matches = re.finditer(UNIT_REGEX, string)

        unit = None
        count = None
        for match in matches:
            if match.group('count') is not None and match.group('unit') is not None:
                count = match.group('count')
                unit = match.group('unit')
                break
            elif match.group('unit') is not None:
                count = match.group('count')
                unit = match.group('unit')
                break
            elif match.group('count') is not None and count is None:
                count = match.group('count')
                unit = match.group('unit')

        try:
            count = float(count.replace(',', '.'))
        except AttributeError:
            pass

        self.count = count
        self.unit = unit
        self.string = string

    def ing(self):
        """This function cleans up the input ingredient by removing units, numbers, 
        single characters and special characters from ingredient.
        """
        pattern2 = (r'(\d*\.?\,?\d+)*'
                    r'((?<=\d|\s)(%s)\b)*'
                    r'(\b\S{1}\b)*'
                    )
        # clean ingredient
        ingre = re.sub(pattern2 % self.all_units, '', self.string, flags=re.IGNORECASE)  # remove units
        ingre = re.sub(r'[$&+:;=?@#|<>.^/\(\)-]', ' ', ingre)  # remove special characters
        ingre = re.sub(r'\s+', ' ', ingre).strip()  # extra whitespace

        return ingre

    def qty_ing(self):
        """Use this function to determine the quantity if the input string is an ingredient."""
        unit = self.unit
        count = self.count

        if unit and count is not None:
            qty = str(count) + ' ' + str(unit)
        elif unit is not None:
            qty = unit
        elif count is not None:
            qty = str(count)
        else:
            qty = None

        return qty

    def qty_qty(self):
        """Use this function to determine the quantity if the input string is a quantity."""
        unit = self.unit
        count = self.count

        if unit and count is not None:
            qty = str(count) + ' ' + str(unit)
        elif unit is not None:
            qty = unit
        elif count is not None:
            # if no unit was found check if qty is only a number meaning 
            # the quantity is a piece count of the ingredient
            string = re.search(r'[a-zA-Z].+', self.orig_string)
            if string is None:
                unit = 'piece'
                qty = str(count) + ' ' + str(unit)
            else:
                qty = None
        else:
            qty = None

        return qty
