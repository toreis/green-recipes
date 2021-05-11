# Green Recipes

This work is part of a bigger project with the mission of informing consumers on sustainable food choices.
The tool analyzes recipes and suggests an alternative, more environmentally friendly ingredients for ingredients that are above-average contributors to the recipe's GHG emission. To determine the footprint of a recipe, users can choose to upload a recipe from a txt file, write down the ingredients individually, or use an existing recipe from a website as a starting point. 


## Usage

To get environmently friendly substitutes for ingredients in recipes run `substitute_recommender.py`

To change the recipe set the URL here 
```
    
    # String can be an URL or all ingredients in text form (delimited by ';' or '\n')
    # From user input on the web application
    
    # file = open(r'C:\Users\user\OneDrive\Studium\MastersThesis\example_recipe.txt', 'r', encoding='utf-8')
    # string = file.read()
    string = 'https://fooby.ch/en/recipes/19371/asian-grilled-roast-pork-?startAuto1=0'

```

To the substitution model can be updated by running `substitute_model.py`
To update the CO2 refernce sheet run `data_preprocess.py`

## Requirements

Requirements can be found in Requirements.txt
