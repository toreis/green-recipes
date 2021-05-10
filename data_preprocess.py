
import pandas as pd
import numpy as np
import os


PATH = os.getcwd()


def compile_ref_list(lang):
    """Compiles the CO2 reference list for all languages by adding synonyms and substitutes"""

    # Fetching all relevant data
    ingred_cal = pd.read_excel(PATH + r'\data\ingredients_reference.xlsx', sheet_name=0).apply \
        (lambda x: x.str.strip() if x.dtype == "object" else x)
    plurals = pd.read_excel(PATH + r'\data\ingredients_reference.xlsx', sheet_name=3).apply \
        (lambda x: x.str.strip() if x.dtype == "object" else x)
    synonyms = pd.read_excel(PATH + r'\data\ingredients_reference.xlsx', sheet_name=4).apply \
        (lambda x: x.str.strip() if x.dtype == "object" else x)

    # Add English ingredient description as a key
    ingred_cal.insert(0, "en_key", "")
    ingred_cal.loc[:, "en_key"] = ingred_cal["en"]

    df_lang = ingred_cal[
        ["en_key", lang, "type", "co2", "classification", "attribute", "variety"]
    ]
    df_lang.loc[:, "lower"] = df_lang[lang].str.lower()

    # Add ingredient description of selected language as a key
    df_lang.insert(1, "lang_key", "")
    df_lang.loc[:, "lang_key"] = df_lang[lang]

    plurals_lang = plurals.loc[plurals["language"] == lang]
    plurals_lang.loc[:, "lower"] = plurals_lang["singular"].str.lower()

    # Merge with plurals of ingredients
    df2 = pd.merge(
        df_lang, plurals_lang, left_on="lower", right_on="lower", how="inner"
    )[
        [
            "en_key",
            "lang_key",
            "plural",
            "type",
            "co2",
            "classification",
            "attribute",
            "variety",
        ]
    ]
    df2 = df2.rename(columns={"plural": lang})

    synonyms_lang = synonyms.loc[synonyms["language"] == lang]
    synonyms_lang.loc[:, "lower"] = synonyms_lang["source"].str.lower()

    # Merge with synonyms of ingredients
    df3 = pd.merge(
        df_lang, synonyms_lang, left_on="lower", right_on="lower", how="inner"
    )[
        [
            "en_key",
            "lang_key",
            "target",
            "type",
            "co2",
            "classification",
            "attribute",
            "variety",
        ]
    ]
    df3 = df3.rename(columns={"target": lang})

    # Append all reference lists
    df_lang = df_lang[
        [
            "en_key",
            "lang_key",
            lang,
            "type",
            "co2",
            "classification",
            "attribute",
            "variety",
        ]
    ]
    df_lang = df_lang.append(df2)
    df_lang = df_lang.append(df3)

    df_lang = df_lang.rename(columns={lang: "ref"})
    df_lang = df_lang.reset_index(drop=True)

    return df_lang


languages = ["en", "de", "it"]

# Create a dictionary with reference lists for all languages and save it as a csv
reference_lists = {}
for language in languages:
    try:
        df = compile_ref_list(language)
        reference_lists[language] = df

        name = PATH + r"\data\reference_list_{}.csv".format(language)
        df.to_csv(name, index=False, header=True)
    except:
        pass


def create_density_list():
    """Compiles food density list from the USDA FoodData list"""
    food = pd.read_csv(PATH + r"\FoodData_legacy\food.csv")
    food_portion = pd.read_csv(PATH + r"\FoodData_legacy\food_portion.csv")

    joined_ingredient_list = pd.merge(food_portion, food, on="fdc_id", how="left")

    clean_list = joined_ingredient_list[["description", "gram_weight", "modifier"]]

    clean_list = clean_list[clean_list["modifier"].isin(["cup", "tbsp", "tsp"])]

    clean_list["ingredient"] = (
        clean_list["description"].str.split(",").str[0].str.strip().str.lower()
    )
    clean_list["attribute"] = (
        clean_list["description"].str.split(",").str[1].str.strip().str.lower()
    )
    clean_list = clean_list.fillna("")

    grouped_multiple = clean_list.groupby(["ingredient", "attribute", "modifier"])[
        "gram_weight"
    ].mean()
    grouped_multiple = grouped_multiple.reset_index()

    grouped_multiple["density"] = np.where(
        grouped_multiple["modifier"] == "cup",
        grouped_multiple["gram_weight"] / 240,
        np.where(
            grouped_multiple["modifier"] == "tsp",
            grouped_multiple["gram_weight"] / 4.9,
            np.where(
                grouped_multiple["modifier"] == "tbsp",
                grouped_multiple["gram_weight"] / 14.7,
                grouped_multiple["gram_weight"],
            ),
        ),
    )

    density_list = grouped_multiple.groupby(["ingredient", "attribute"])[
        "density"
    ].mean()
    density_list = density_list.reset_index()

    density_avg = density_list.groupby("ingredient")["density"].mean()
    density_list = density_list.set_index("ingredient")
    density_list["density_avg"] = density_avg
    density_list = density_list.reset_index()

    density_list.insert(0, "ingredient_combined", "")
    density_list["ingredient_combined"] = (
        density_list[["attribute", "ingredient"]].agg(" ".join, axis=1).str.strip()
    )

    return density_list
