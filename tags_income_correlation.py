import os
import pandas as pd
from mappings import tracks_to_drop, gema_to_apl, keywords_no_colon

pd.set_option('display.max_columns', 200)
pd.set_option('display.width', 1000)

#################################################### PREPROCESSING #####################################################

#################################
### GEMA INCOME PER APL TRACK ###
#################################

# Folder with statements in CSV format
folder_path = 'C:/Users/jakub/PycharmProjects/tags_income_correlation/statements'

# Target columns
target_columns = [
    'Betrag gebucht',
    'Werkfassungstitel',
    'Komponist(en)',
    'Name, Vorname Unterkonto'
]

all_dfs = []

for file_name in os.listdir(folder_path):
    if file_name.endswith('.csv'):
        file_path = os.path.join(folder_path, file_name)
        try:
            df = pd.read_csv(file_path, sep=';', decimal=',', encoding='utf-8', low_memory=False)

            # Ensure all target columns are present
            for col in target_columns:
                if col not in df.columns:
                    df[col] = pd.NA

            # Select and reorder columns
            df = df[target_columns]

            all_dfs.append(df)
        except Exception as e:
            print(f'Error reading {file_name}: {e}')

# Combine all data
gema = pd.concat(all_dfs, ignore_index=True)

# Renaming columns
gema = gema.rename(columns={
    'Betrag gebucht': 'income',
    'Werkfassungstitel': 'track_title',
    'Komponist(en)': 'composer(s)',
    'Name, Vorname Unterkonto': 'publisher_name'
})

# Publishers names to upper case
gema['publisher_name'] = gema['publisher_name'].str.upper().str.strip()

# Dictionary to rename our publishers' names
rename_dict_publishers = {
    'APL': 'APL PUBLISHING',
    'APL PUBLISHING APS': 'APL PUBLISHING',
    'APL PUBLISHING GMBH': 'APL PUBLISHING',
    'TAI YANG SHEN': 'SWIMMING POOL MUSIC',
    'TASTY DANISH': 'SWIMMING POOL MUSIC',
    'TRY A DANISH': 'SWIMMING POOL MUSIC'
}

gema['publisher_name'] = gema['publisher_name'].replace(rename_dict_publishers)

# We will keep only our labels info
gema_APL = gema.loc[gema['publisher_name'].isin(['APL DECADES',
                                                 'APL FRONTRUNNERS',
                                                 'APL LIFESTYLE',
                                                 'APL ORGANIC',
                                                 'APL PUBLISHING',
                                                 'APL VOCALS',
                                                 'CPH-NYC PUBLISHING APS',
                                                 'SWIMMING POOL MUSIC'
                                                 ])]

# Ensure Betrag gebucht is numeric
gema_APL['income'] = pd.to_numeric(gema_APL['income'], errors='coerce')

# Adding helper column for mapping duplicated track titles with Cadenza metadata
gema_APL['helper_column'] = (gema_APL['track_title'].astype(str)
                          + '_'
                          + gema_APL['composer(s)'].astype(str)
                          + '_'
                          + gema_APL['publisher_name']
                            )

# Drop tracks that are not ours or no longer represented (TRACKS_TO_DROP)
gema_APL = gema_APL[~gema_APL['helper_column'].isin(tracks_to_drop)]

# Mapping duplicated titles and different naming of the same tracks
gema_APL['gema_to_apl'] = gema_APL['helper_column'].map(gema_to_apl)
gema_APL['track_title'] = gema_APL['gema_to_apl'].fillna(gema_APL['track_title'])

# gema_APL.to_csv('gema_APL.csv', index=False)

# Group and sum income per track title
grouped_income_APL = (gema_APL.groupby('track_title', as_index=False)['income']
                  .sum()
                  .sort_values(by='income', ascending=False)
                  )

###############################################
### COMBINING AND CLEANING CADENZA METADATA ###
###############################################

# Folder with metadata in CSV format
folder_path_met = "C:/Users/jakub/PycharmProjects/tags_income_correlation/cadenza_metadata"

# Target columns
target_columns_met = [
    'ALBUM: Release Date',
    'TRACK: Title',
    'TRACK: Is Main',
    'WRITER:1: Last Name',
    'PUBLISHER:1: Name',
    'CATEGORY: Genre',
    'CATEGORY: Instrumentation',
    'CATEGORY: Mood',
    'CATEGORY: Period',
    'CATEGORY: Tempo',
    'CATEGORY: Type',
    'CATEGORY: Usage',
    'CATEGORY: Location'
]

all_dfs_met = []

for file_name_met in os.listdir(folder_path_met):
    if file_name_met.endswith('.csv'):
        file_path_met = os.path.join(folder_path_met, file_name_met)
        try:
            df_met = pd.read_csv(file_path_met, sep=',', encoding='utf-8', low_memory=False)

            # Ensure all target columns are present
            for col_met in target_columns_met:
                if col_met not in df_met.columns:
                    df_met[col_met] = pd.NA

            # Select and reorder columns
            df_met = df_met[target_columns_met]

            all_dfs_met.append(df_met)
        except Exception as e:
            print(f'Error reading {file_name_met}: {e}')

# Combine all data
metadata = pd.concat(all_dfs_met, ignore_index=True)

# Filtering out alternate versions
metadata = metadata.loc[metadata["TRACK: Is Main"] == "Y"]
metadata = metadata.drop("TRACK: Is Main", axis=1)

# Renaming columns
metadata = metadata.rename(columns={
    'ALBUM: Release Date': 'release_date',
    'TRACK: Title': 'track_title',
    'WRITER:1: Last Name': 'writer_last_name',
    'PUBLISHER:1: Name': 'publisher_name'
})

metadata['track_title'] = metadata['track_title'].str.upper()
metadata['writer_last_name'] = metadata['writer_last_name'].str.upper()
metadata['publisher_name'] = metadata['publisher_name'].str.upper()
metadata['release_date'] = pd.to_datetime(metadata['release_date'])

# Adjusting titles registered in GEMA without apostrophes and/or parentheses, and also those registered differently
# metadata['track_title'] = metadata['track_title'].replace(apl_to_gema)

# Rename the publishers
metadata['publisher_name'] = metadata['publisher_name'].replace(rename_dict_publishers)

missing_publishers = {
    'SHINE BRIGHTER': 'APL PUBLISHING',
    'PURE ELATION': 'APL PUBLISHING',
    'EVERGREEN POSSIBILITIES': 'APL PUBLISHING',
    'SPARK OF JOY': 'APL PUBLISHING',
    'SUNBURST OF LOVE': 'APL PUBLISHING',
    'COOL ROQUE': 'SWIMMING POOL MUSIC'
}

metadata['publisher_name'] = metadata['publisher_name'].fillna(metadata['track_title'].map(missing_publishers))

missing_composers = {
    '1000': 'ZEKAJA',
    'CRASH': 'ZEKAJA',
    'INHALE EXHALE': 'ZEKAJA',
    'NOSTALGIA': 'ZEKAJA',
    'NUMB': 'ZEKAJA',
    'O.D.': 'ZEKAJA',
    'SPRING CPH': 'ZEKAJA',
    'SUB CPH': 'ZEKAJA',
    'THE DRIVE': 'ZEKAJA',
    'THE GOT AWAY': 'ZEKAJA',
    'ZETUP': 'ZEKAJA'
}

metadata['writer_last_name'] = metadata['writer_last_name'].fillna(metadata['track_title'].map(missing_composers))

# Merging tags into one list for each track
tag_cols = [
    'CATEGORY: Genre',
    'CATEGORY: Instrumentation',
    'CATEGORY: Mood',
    'CATEGORY: Period',
    'CATEGORY: Tempo',
    'CATEGORY: Type',
    'CATEGORY: Usage',
    'CATEGORY: Location'
]

def merge_tags(row):
    tags = []
    for col_t in tag_cols:
        if pd.notnull(row[col_t]):
            tags.extend([t.strip() for t in row[col_t].split(';')])
    return tags

metadata['all_tags'] = metadata.apply(merge_tags, axis=1)
metadata = metadata.drop(tag_cols, axis=1)

# Deconstructing keywords with colons
def clean_keywords(tag_list):
    # Check if tag_list is actually a list and not NaN/None
    if isinstance(tag_list, list):
        # 1. Map tags using the dictionary (falling back to original if not found)
        # 2. Use set() to remove duplicates (e.g., if 'Rock:Post Rock' and 'Post Rock' both exist)
        cleaned = {keywords_no_colon.get(tag, tag) for tag in tag_list}
        return list(cleaned)
    return tag_list

metadata['all_tags'] = metadata['all_tags'].apply(clean_keywords)

# Adding helper column for matching with GEMA statements
metadata['helper_column'] = (metadata['track_title'].astype(str)
                          + '_'
                          + metadata['writer_last_name'].astype(str)
                          + '_'
                          + metadata['publisher_name']
                            )

metadata = metadata.drop_duplicates('helper_column')

# Renaming duplicated track titles with values from helper column
mask = metadata['track_title'].duplicated(keep=False)
metadata.loc[mask, 'track_title'] = metadata.loc[mask, 'helper_column']

# metadata.to_csv('metadata.csv', index=False)

##########################################
### MAPPING INCOME WITH TAGS AND DATES ###
##########################################

helper_dict = metadata.set_index('helper_column')['all_tags'].to_dict()
title_dict = metadata.set_index('track_title')['all_tags'].to_dict()

helper_dict_date = metadata.set_index('helper_column')['release_date'].to_dict()
title_dict_date = metadata.set_index('track_title')['release_date'].to_dict()

# Mapping tags and dates with helper_column first, then with track_title column
grouped_income_APL['all_tags'] = (grouped_income_APL['track_title'].map(helper_dict).fillna(grouped_income_APL['track_title'].map(title_dict)))
grouped_income_APL['release_date'] = (grouped_income_APL['track_title'].map(helper_dict_date).fillna(grouped_income_APL['track_title'].map(title_dict_date)))

# Calculating tracks lifetime up to the given date
# In case of errors in dates, the minimum value is set to 0 days
reference_date = pd.to_datetime('2026-03-31')
grouped_income_APL['track_age_days'] = (reference_date - grouped_income_APL['release_date']).dt.days
grouped_income_APL['track_age_days'] = grouped_income_APL['track_age_days'].clip(lower=0)

grouped_income_APL = grouped_income_APL.dropna(subset=['all_tags'])

# grouped_income_APL.to_csv('grouped_income_APL.csv', index=False)

################################################### MODEL TRAINING #####################################################

###############
### IMPORTS ###
###############

import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer
from scipy.stats import pointbiserialr
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LassoCV
from sklearn.linear_model import ElasticNetCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

#############################
### MULTI LABEL BINARIZER ###
#############################

mlb = MultiLabelBinarizer()

# Transform the 'all_tags' list into a binary matrix
tag_matrix = mlb.fit_transform(grouped_income_APL['all_tags'])

# Create a new DataFrame from this matrix with tag names as columns
tags_df = pd.DataFrame(tag_matrix, columns=mlb.classes_, index=grouped_income_APL.index)

# Remove tags with tempos
tags_to_remove = [
    'Alternating Tempo', 'Arrhythmic', 'Fast', 'Medium', 'Medium-Fast', 'Medium-Slow', 'Rubato', 'Slow',
    'Very-Fast', 'Very-Slow'
]

tags_df = tags_df.drop(columns=tags_to_remove, errors='ignore')

# Concatenating the track_age_days column
analysis_df = pd.concat([grouped_income_APL[['income', 'track_age_days']], tags_df], axis=1)

###########################
### FEATURE ENGINEERING ###
###########################

# Adding number of tags
analysis_df['tag_count'] = tags_df.sum(axis=1)

##############################
### FILTERING OUT OUTLIERS ###
##############################

lower_threshold = 1
upper_threshold = analysis_df['income'].quantile(0.99)

print(f"Analysis range: from {lower_threshold:.2f} to {upper_threshold:.2f} Euro")

df_clean = analysis_df[
    (analysis_df['income'] >= lower_threshold) &
    (analysis_df['income'] <= upper_threshold)
].copy()

removed_low = len(analysis_df[analysis_df['income'] < lower_threshold])
removed_high = len(analysis_df[analysis_df['income'] > upper_threshold])

print(f"Removed {removed_low} tracks below 1 Euro threshold ('dust').")
print(f"Removed {removed_high} tracks over 99th percentile (outliers).")
print(f"{len(df_clean)} tracks left for analysis.")

#########################################################
### THE FREQUENCY FILTER & POINT-BISERIAL CORRELATION ###
#########################################################

# Get the sum of each tag column to see how often they appear
tag_counts = df_clean.drop(columns='income').sum()

# Filter for tags that appear at least 50 times and in less than 70% of tracks (not too common)
upper_threshold = len(df_clean) * 0.7
normal_tags = tag_counts[(tag_counts > 50) & (tag_counts < upper_threshold)].index

# Run correlation only on common tags
filtered_correlations = df_clean[['income'] + list(normal_tags)].corr()['income'].drop('income').sort_values(ascending=False)

print('TOP POSITIVE EARNERS:\n', filtered_correlations.head(20))
print('\nTOP NEGATIVE EARNERS:\n', filtered_correlations.tail(20))

##########################
### MEAN INCOME BY TAG ###
##########################

mean_income_by_tag = {}

for tag in normal_tags:
    mean_income_by_tag[tag] = df_clean[df_clean[tag] == 1]['income'].mean()

mean_income_by_tag = pd.Series(mean_income_by_tag).sort_values(ascending=False)

print('\nMEAN INCOME BY TAG:\n', mean_income_by_tag.head(20))

######################################
### TOP TAG STATISTICAL VALIDATION ###
######################################

# p_keyword = 'News'
#
# # Check a specific tag
# tag_column = df_clean[p_keyword]
# income_column = df_clean['income']
#
# correlation, p_value = pointbiserialr(tag_column, income_column)

# print(f'\nCorrelation for the keyword {p_keyword}: {correlation:.4f}')
# print(f'P-value: {p_value:.10f}\n')

################################################
### COMPARING WITH SPEARMAN RANK CORRELATION ###
################################################

# Define the columns to analyze (income + your filtered normal_tags)
cols_to_analyze = ['income'] + list(normal_tags)

# Calculate Pearson Correlation (Point-Biserial)
pearson_corrs = df_clean[cols_to_analyze].corr(method='pearson')['income'].drop('income').sort_values(ascending=False)

# Calculate Spearman Correlation (Rank-based)
spearman_corrs = df_clean[cols_to_analyze].corr(method='spearman')['income'].drop('income').sort_values(ascending=False)

# Create a comparison DataFrame
comparison_df = pd.DataFrame({
    'Pearson': pearson_corrs,
    'Spearman': spearman_corrs,
    'Frequency': tag_counts[normal_tags]  # Adding frequency for context
})

# Add a 'Difference' column to see which tags shift the most
comparison_df['Diff'] = comparison_df['Spearman'] - comparison_df['Pearson']

# Show the top results sorted by Spearman
# print('CORRELATION COMPARISON (Sorted by Spearman):')
# print(comparison_df.sort_values(by='Spearman', ascending=False).head(20))

###########################################################
### LASSO REGRESSION WITH COLUMN TRANSFORMER & PIPELINE ###
###########################################################

# Zachowanie wcześniejszego frequency filter
X = df_clean[list(normal_tags) + ['track_age_days']]
y = df_clean['income']

# Train-test split (opcjonalny, ale zalecany)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Log transform
y_train_log = np.log1p(y_train)
y_test_log = np.log1p(y_test)

# Column Transformer Preprocessor
binary_cols = list(normal_tags)
numeric_cols = ['track_age_days']

preprocessor = ColumnTransformer([
    ('num', StandardScaler(), numeric_cols),
    ('bin', 'passthrough', binary_cols)
])

# Pipeline łączy kroki: najpierw skalowanie, potem Lasso
lasso_pipeline = Pipeline([
    ('prep', preprocessor),
    ('lasso', LassoCV(cv=5, random_state=42, max_iter=10000))
])

# Trenowanie
# Ważne: Przekazujemy surowe X_train, pipeline sam zajmie się skalowaniem
lasso_pipeline.fit(X_train, y_train_log)

# Wyciąganie wyników - KLUCZOWY MOMENT
# Pobieramy nazwy cech w kolejności, w jakiej ułożył je preprocesor
feature_names = numeric_cols + binary_cols
lasso_model = lasso_pipeline.named_steps['lasso']
coefficients = pd.Series(lasso_model.coef_, index=feature_names)

# Usuwamy wiek tracków do wykresu tagów
important_tags = coefficients.drop('track_age_days', errors='ignore')
important_tags = important_tags[important_tags != 0].sort_values(ascending=False)

print('\nTOP POSITIVE TAGS (Lasso Pipeline):')
print(important_tags.head(15))

# Ocena modelu
# Pipeline automatycznie zeskaluje X_test przed predykcją!
y_pred = lasso_pipeline.predict(X_test)

#########################################################
### ELASTIC NET CV WITH COLUMN TRANSFORMER & PIPELINE ###
#########################################################

# Using previous frequency filter for tags
X_en = df_clean[list(normal_tags) + ['track_age_days']]

y_en = df_clean['income']

# Train-test split
X_en_train, X_en_test, y_en_train, y_en_test = train_test_split(
    X_en, y_en, test_size=0.2, random_state=42
)

# Log transform for Y, because income distribution is highly skewed
y_en_train_log = np.log1p(y_en_train)
y_en_test_log = np.log1p(y_en_test)

binary_cols = list(normal_tags)
numeric_cols = ['track_age_days']

# Column Transformer Preprocessor - scaling the track_age_days only
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), numeric_cols),
    ('bin', 'passthrough', binary_cols)
])

# Pipeline with Column Transformer
en_pipeline = Pipeline([
    ('prep', preprocessor),
    ('elasticnet', ElasticNetCV(
        l1_ratio=[.1, .5, .7, .9, .95, .99, 1],
        cv=5,
        random_state=42,
        max_iter=10000
    ))
])

# Trenowanie
# Ważne: Przekazujemy surowe X_train, pipeline sam zajmie się skalowaniem
en_pipeline.fit(X_en_train, y_en_train_log)

# Wyciąganie wyników
# Pobieramy nazwy cech w kolejności, w jakiej ułożył je preprocesor
feature_names = numeric_cols + binary_cols
en_model = en_pipeline.named_steps['elasticnet']
coefficients_en = pd.Series(en_model.coef_, index=feature_names)

# Usuwamy wiek tracków do wykresu tagów
important_tags_en = coefficients_en.drop('track_age_days', errors='ignore')
important_tags_en = important_tags_en[important_tags_en != 0].sort_values(ascending=False)

print('\nTOP POSITIVE TAGS (Elastic Net Pipeline):')
print(important_tags_en.head(15))

# Ocena modelu
# Pipeline automatycznie zeskaluje X_en_test przed predykcją!
y_en_pred = en_pipeline.predict(X_en_test)

print(f'Best L1 Ratio: {en_model.l1_ratio_}') # 1.0 means it behaved like Lasso

######################################################
### MAE & MSE FOR ELASTIC NET CV + DUMMY REGRESSOR ###
######################################################

# Pobierz predykcje (są w skali logarytmicznej)
y_en_pred_log = en_pipeline.predict(X_en_test)

# Odwróć logarytm, aby wrócić do oryginalnych wartości przychodu
y_en_pred_original = np.expm1(y_en_pred_log)
y_en_test_original = np.expm1(y_en_test_log) # to jest to samo co df_clean['income'] dla testu

# Oblicz metryki
mae_en = mean_absolute_error(y_en_test_original, y_en_pred_original)
mse_en = mean_squared_error(y_en_test_original, y_en_pred_original)
rmse_en = np.sqrt(mse_en) # Pierwiastek z MSE - łatwiejszy do interpretacji

print(f'--- ELASTIC NET (Skala oryginalna) ---')
print(f'MAE: {mae_en:.2f}')
print(f'MSE: {mse_en:.2f}')
print(f'RMSE: {rmse_en:.2f}')

from sklearn.dummy import DummyRegressor

# Stwórz model Dummy (zawsze przewiduje średnią z y_train_log)
dummy_mean = DummyRegressor(strategy='mean')
dummy_mean.fit(X_en_train, y_en_train_log)

# Przewidywanie (w skali logarytmicznej)
y_dummy_log = dummy_mean.predict(X_en_test)

# Powrót do skali oryginalnej (Euro)
y_dummy_original = np.expm1(y_dummy_log)
y_en_test_original = np.expm1(y_en_test_log) # Twoje prawdziwe dane testowe w Euro

# Oblicz MAE
mae_dummy = mean_absolute_error(y_en_test_original, y_dummy_original)
mae_model = mean_absolute_error(y_en_test_original, y_en_pred_original) # Twoje MAE z Elastic Net

print(f"MAE Modelu naiwnego (Średnia): {mae_dummy:.2f} EUR")
print(f"MAE Twojego modelu Elastic Net: {mae_model:.2f} EUR")

# Procentowa poprawa
improvement = (mae_dummy - mae_model) / mae_dummy * 100
print(f"\nTwój model jest lepszy od zgadywania średniej o: {improvement:.2f}%")

#############################
### BUSINESS IMPACT TABLE ###
#############################

# Pobieramy współczynniki z obu modeli (pobrane wcześniej z pipeline'ów)
# Usuwamy wiek utworu, aby skupić się tylko na tagach
df_lasso = pd.Series(lasso_pipeline.named_steps['lasso'].coef_, index=feature_names).drop('track_age_days', errors='ignore')
df_en = pd.Series(en_pipeline.named_steps['elasticnet'].coef_, index=feature_names).drop('track_age_days', errors='ignore')

# Tworzymy wspólną tabelę
comparison_table = pd.DataFrame({
    'Lasso_Coef': df_lasso,
    'EN_Coef': df_en
})

# Filtrujemy - zostawiamy tylko te tagi, które chociaż w jednym modelu nie są zerem
comparison_table = comparison_table[(comparison_table['Lasso_Coef'] != 0) | (comparison_table['EN_Coef'] != 0)]

# Obliczamy Realny Wpływ Procentowy dla obu modeli
comparison_table['Lasso_Impact_%'] = (np.exp(comparison_table['Lasso_Coef']) - 1) * 100
comparison_table['EN_Impact_%'] = (np.exp(comparison_table['EN_Coef']) - 1) * 100

# Dodajemy liczebność (Frequency) dla kontekstu biznesowego
comparison_table['Frequency'] = tag_counts[comparison_table.index]

# Sortujemy według średniego wpływu
comparison_table['Mean_Impact'] = (comparison_table['Lasso_Impact_%'] + comparison_table['EN_Impact_%']) / 2
comparison_table = comparison_table.sort_values(by='Mean_Impact', ascending=False)

# # Wyświetlamy Top 20 wyników
# print("PORÓWNANIE WPŁYWU BIZNESOWEGO (LASSO VS ELASTIC NET):")
# cols_to_show = ['Lasso_Impact_%', 'EN_Impact_%', 'Frequency']
# print(comparison_table[cols_to_show].head(20).to_string(formatters={
#     'Lasso_Impact_%': '{:,.2f}%'.format,
#     'EN_Impact_%': '{:,.2f}%'.format
# }))

# comparison_table.to_csv('business_impact_table.csv')

###############################
### RANDOM FOREST REGRESSOR ###
###############################

X_forest = df_clean[list(normal_tags) + ['track_age_days']]
y_forest = df_clean['income']

# Log transform dla dochodu (nadal zalecany, by wyrównać rozkład)
y_forest_log = np.log1p(y_forest)

X_forest_train, X_forest_test, y_forest_train, y_forest_test = train_test_split(
    X_forest, y_forest_log, test_size=0.2, random_state=42)

rf = RandomForestRegressor(n_estimators=100, max_depth=None, min_samples_leaf=5, random_state=42, n_jobs=-1)

rf.fit(X_forest_train, y_forest_train)

y_forest_pred = rf.predict(X_forest_test)

# Feature Importance
# To odpowiednik 'coefficients' z Lasso, ale pokazuje realny wpływ na decyzje modelu
importances = pd.Series(rf.feature_importances_, index=X_forest.columns)
important_features = importances.sort_values(ascending=False)

print('\nTOP 20 NAJWAŻNIEJSZYCH TAGÓW (RF):')
print(important_features.head(20))

print(f'\nWspółczynnik R^2 (Lasso Pipeline): {r2_score(y_test_log, y_pred):.4f}')
print(f'\nWspółczynnik R^2 (Elastic Net Pipeline): {r2_score(y_en_test_log, y_en_pred):.4f}')
print(f'\nWspółczynnik R^2 (Random Forest): {r2_score(y_forest_test, y_forest_pred):.4f}')

######################
### VISUALIZATIONS ###
######################

import matplotlib.pyplot as plt
import seaborn as sns

fig, axs = plt.subplots(1, 2, figsize=(10, 5))

# Subplot 1: Pearson Correlations
top_corr = filtered_correlations.head(10)
bottom_corr = filtered_correlations.tail(10)
plot_data = pd.concat([top_corr, bottom_corr]).sort_values()

axs[0].barh(y=plot_data.index, width=plot_data.values, color='skyblue')

axs[0].set_title('Pearson Correlations')
axs[0].axvline(0, color='black', linewidth=1)
axs[0].grid(axis='x', linestyle='--', alpha=0.3)

# # Subplot 2: Spearman Correlations
# top_corr_sp = spearman_corrs.head(10)
# bottom_corr_sp = spearman_corrs.tail(10)
# plot_data_sp = pd.concat([top_corr_sp, bottom_corr_sp]).sort_values()
#
# axs[0].barh(y=plot_data_sp.index, width=plot_data_sp.values, color='orange')
#
# axs[0].set_title('Spearman Correlations')
# axs[0].axvline(0, color='black', linewidth=1)
# axs[0].grid(axis='x', linestyle='--', alpha=0.3)

# # Subplot 3: Lasso Regression
#
# # Usuwamy track_age_days TYLKO z wyników do wykresu
# # Używamy .drop(..., errors='ignore'), aby kod się nie wywalił, jeśli go tam nie ma
# plot_tags = important_tags.drop(labels=['track_age_days'], errors='ignore')
#
# # Prepare the data (Top 10 positive and Top 10 negative)
# top_pos = plot_tags.head(10)
# top_neg = plot_tags.tail(10)
# plot_data = pd.concat([top_pos, top_neg])
#
# sns.barplot(x=plot_data.values, y=plot_data.index, hue=plot_data.index, palette='viridis', legend=False, ax=axs[1,0])
#
# axs[1,0].set_title('Lasso Regression')
# axs[1,0].set_ylabel(None)
# axs[1,0].axvline(0, color='black', linewidth=1.5, alpha=0.7)
# axs[1,0].grid(axis='x', linestyle='--', alpha=0.4)

# Subplot 4: Elastic Net

# Usuwamy track_age_days TYLKO z wyników do wykresu
# Używamy .drop(..., errors='ignore'), aby kod się nie wywalił, jeśli go tam nie ma
plot_tags_en = important_tags_en.drop(labels=['track_age_days'], errors='ignore')

# Prepare the data (Top 10 positive and Top 10 negative)
top_pos_en = plot_tags_en.head(10)
top_neg_en = plot_tags_en.tail(10)
plot_data_en = pd.concat([top_pos_en, top_neg_en])

sns.barplot(x=plot_data_en.values, y=plot_data_en.index, hue=plot_data_en.index, palette='viridis', legend=False, ax=axs[1])

axs[1].set_title('Elastic Net')
axs[1].set_ylabel(None)
axs[1].axvline(0, color='black', linewidth=1.5, alpha=0.7)
axs[1].grid(axis='x', linestyle='--', alpha=0.4)

plt.tight_layout()
plt.show()
# plt.savefig('Subplots.png')

# Można jeszcze spróbować FEATURE ENGINEERING
# UŻYCIE TOP TAGÓW Z RF DO FEATURE ENGINEERINGU W ELASTIC NET (2 najlepsze modele)
# Można policzyć różnicę średnich jak jest tag (1) vs jak go nie ma (0)
# Może dodać jako feature, z jakiego roku to jest przychód (Nutzungsjahr w statementach GEMY)?

# Cross Validation Score
# SHAP dla Random Forest
# XGBoost
