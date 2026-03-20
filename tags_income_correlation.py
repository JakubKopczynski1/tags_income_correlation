import os
import pandas as pd
from mappings import duplicated_titles_gema, keywords_no_colon, tracks_titles_rework_gema, tracks_to_drop

pd.set_option('display.max_columns', 200)
pd.set_option('display.width', 1000)

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

# Rename the publishers
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

# Drop tracks that are not our or no longer represented
gema_APL = gema_APL[~gema_APL['helper_column'].isin(tracks_to_drop)]

# Mapping duplicated track titles
gema_APL['mapped_helper'] = gema_APL['helper_column'].map(duplicated_titles_gema)

gema_APL['track_title'] = gema_APL['mapped_helper'].fillna(gema_APL['track_title'])

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
metadata['track_title'] = metadata['track_title'].replace(tracks_titles_rework_gema)

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

# Filling in missing publishers
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

# Filling in missing composers
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

# Apply the function directly to the list column
metadata['all_tags'] = metadata['all_tags'].apply(clean_keywords)

# Adding helper column
metadata['helper_column'] = (metadata['track_title'].astype(str)
                          + '_'
                          + metadata['writer_last_name'].astype(str)
                          + '_'
                          + metadata['publisher_name']
                            )

metadata = metadata.drop_duplicates('helper_column')

mask = metadata['track_title'].duplicated(keep=False)

metadata.loc[mask, 'track_title'] = metadata.loc[mask, 'helper_column']

##########################################
### MAPPING INCOME WITH TAGS AND DATES ###
##########################################

helper_dict = metadata.set_index('helper_column')['all_tags'].to_dict()
title_dict = metadata.set_index('track_title')['all_tags'].to_dict()

helper_dict_date = metadata.set_index('helper_column')['release_date'].to_dict()
title_dict_date = metadata.set_index('track_title')['release_date'].to_dict()

# Mapping tags and dates with helper_column first, the with track_title column
grouped_income_APL['all_tags'] = (grouped_income_APL['track_title'].map(helper_dict).fillna(grouped_income_APL['track_title'].map(title_dict)))
grouped_income_APL['release_date'] = (grouped_income_APL['track_title'].map(helper_dict_date).fillna(grouped_income_APL['track_title'].map(title_dict_date)))

# Obliczamy wiek utworu w dniach względem końca Twojego okresu raportowego (np. koniec 2025)
reference_date = pd.to_datetime('2025-12-31')
grouped_income_APL['track_age_days'] = (reference_date - grouped_income_APL['release_date']).dt.days

# Jeśli masz utwory z przyszłości (błędy w dacie), ustawiamy im minimum 0 dni
grouped_income_APL['track_age_days'] = grouped_income_APL['track_age_days'].clip(lower=0)

grouped_income_APL = grouped_income_APL.dropna(subset=['all_tags'])

# grouped_income_APL.to_csv('grouped_income_APL.csv', index=False)

########################
### ONE-HOT ENCODING ###
########################

from sklearn.preprocessing import MultiLabelBinarizer

# Initialize the binarizer
mlb = MultiLabelBinarizer()

# Transform the 'all_tags' list into a binary matrix
tag_matrix = mlb.fit_transform(grouped_income_APL['all_tags'])

# Create a new DataFrame from this matrix with tag names as columns
tags_df = pd.DataFrame(tag_matrix, columns=mlb.classes_, index=grouped_income_APL.index)

# Remove tags with tempos
tags_to_remove = [
    'Alternating Tempo',
    'Arrhythmic',
    'Fast',
    'Medium',
    'Medium-Fast',
    'Medium-Slow',
    'Rubato',
    'Slow',
    'Very-Fast',
    'Very-Slow'
]

tags_df = tags_df.drop(columns=tags_to_remove, errors='ignore')

# Zmieniamy pd.concat, aby dołączyć wiek utworu obok income
analysis_df = pd.concat([grouped_income_APL[['income', 'track_age_days']], tags_df], axis=1)

##############################
### FILTERING OUT OUTLIERS ###
##############################

# Definiujemy dolny próg (np. $1)
lower_threshold = 1.00

# Obliczamy górny próg (99. percentyl)
upper_threshold = analysis_df['income'].quantile(0.99)

print(f"Zakres analizy: od ${lower_threshold:.2f} do ${upper_threshold:.2f}")

df_clean = analysis_df[
    (analysis_df['income'] >= lower_threshold) &
    (analysis_df['income'] <= upper_threshold)
].copy()

removed_low = len(analysis_df[analysis_df['income'] < lower_threshold])
removed_high = len(analysis_df[analysis_df['income'] > upper_threshold])

print(f"Usunięto {removed_low} utworów poniżej progu $1 (tzw. 'dust').")
print(f"Usunięto {removed_high} utworów powyżej 99. percentyla (outliery).")
print(f"Pozostało do analizy: {len(df_clean)} utworów.")

##############################################
### CALCULATING POINT-BISERIAL CORRELATION ###
##############################################

# Calculate correlation of all columns with 'income'
correlations = df_clean.corr()['income'].sort_values(ascending=False)

# Remove the 'income' correlation with itself
tag_correlations = correlations.drop('income')

############################
### THE FREQUENCY FILTER ###
############################

# Get the sum of each tag column to see how often they appear
tag_counts = df_clean.drop(columns='income').sum()

# Filter for tags that appear at least 50 times and in less than 70% of tracks (not too common)
upper_threshold = len(df_clean) * 0.7

normal_tags = tag_counts[(tag_counts > 50) & (tag_counts < upper_threshold)].index

# Re-run correlation only on common tags
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

from scipy.stats import pointbiserialr

p_keyword = 'Neutral'

# Check a specific tag
tag_column = df_clean[p_keyword]
income_column = df_clean['income']

correlation, p_value = pointbiserialr(tag_column, income_column)

print(f'\nCorrelation for the keyword {p_keyword}: {correlation:.4f}')
print(f'P-value: {p_value:.10f}\n')

#####################
### VISUALIZATION ###
#####################

import matplotlib.pyplot as plt

top = filtered_correlations.head(10)
bottom = filtered_correlations.tail(10)

plot_data = pd.concat([top, bottom])

plt.figure(figsize=(10,8))

plot_data.sort_values().plot(kind='barh')

plt.title('Top and Bottom 10 Correlations between Tags and Income (GEMA 2024-2025)')
plt.xlabel('Correlation with Income')

plt.axvline(0)  # linia zero
plt.tight_layout()

################################################
### COMPARING WITH SPEARMAN RANK CORRELATION ###
################################################

# Define the columns to analyze (income + your filtered normal_tags)
cols_to_analyze = ['income'] + list(normal_tags)

# Calculate Pearson Correlation (Point-Biserial)
pearson_corrs = df_clean[cols_to_analyze].corr(method='pearson')['income'].drop('income')

# Calculate Spearman Correlation (Rank-based)
spearman_corrs = df_clean[cols_to_analyze].corr(method='spearman')['income'].drop('income')

# Create a comparison DataFrame
comparison_df = pd.DataFrame({
    'Pearson': pearson_corrs,
    'Spearman': spearman_corrs,
    'Frequency': tag_counts[normal_tags]  # Adding frequency for context
})

# Add a 'Difference' column to see which tags shift the most
comparison_df['Diff'] = comparison_df['Spearman'] - comparison_df['Pearson']

# Show the top results sorted by Spearman
print('CORRELATION COMPARISON (Sorted by Spearman):')
print(comparison_df.sort_values(by='Spearman', ascending=False).head(20))

########################
### LASSO REGRESSION ###
########################

# Które tagi mają wpływ na income biorąc pod uwagę też inne tagi?

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LassoCV
from sklearn.metrics import r2_score

X = df_clean.drop(columns='income')
y = df_clean['income']

# Train-test split (opcjonalny, ale zalecany)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Log transform
y_train_log = np.log1p(y_train)
y_test_log = np.log1p(y_test)

# Standardyzacja
scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Lasso z cross-validation
lasso = LassoCV(cv=5, random_state=42, n_jobs=-1, max_iter=10000)

lasso.fit(X_train_scaled, y_train_log)

# Wyniki
coefficients = pd.Series(lasso.coef_, index=X.columns)

# Usunięcie zer (usunięcie szumu)
important_tags = coefficients[coefficients != 0].sort_values(ascending=False)

print('\nTOP POSITIVE TAGS LASSO:')
print(important_tags.head(15))

print('\nTOP NEGATIVE TAGS LASSO:')
print(important_tags.tail(15))

# Ocena modelu
y_pred = lasso.predict(X_test_scaled)

print('\nWspółczynnik R^2 (Lasso):', r2_score(y_test_log, y_pred))

###########################
### LASSO VISUALIZATION ###
###########################

import seaborn as sns

# Usuwamy track_age_days TYLKO z wyników do wykresu
# Używamy .drop(..., errors='ignore'), aby kod się nie wywalił, jeśli go tam nie ma
plot_tags = important_tags.drop(labels=['track_age_days'], errors='ignore')

# Prepare the data (Top 10 positive and Top 10 negative)
top_pos = plot_tags.head(10)
top_neg = plot_tags.tail(10)
plot_data = pd.concat([top_pos, top_neg])

fig, ax = plt.subplots(figsize=(15, 8))

sns.barplot(x=plot_data.values, y=plot_data.index, hue=plot_data.index, palette='viridis', legend=False, ax=ax)

ax.set_title('Lasso Regression: Independent Impact of Tags on Income', fontsize=16, pad=20)
ax.set_xlabel('Coefficient Strength', fontsize=12)
ax.set_ylabel(None)
ax.axvline(0, color='black', linewidth=1.5, alpha=0.7)
ax.grid(axis='x', linestyle='--', alpha=0.4)

for i, v in enumerate(plot_data.values):
    if v > 0:
        ax.text(v + 0.002, i, f' {v:.4f}',
                va='center', ha='left', fontsize=10, fontweight='bold')
    else:
        ax.text(v - 0.002, i, f'{v:.4f} ',
                va='center', ha='right', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.show()
# plt.savefig('lasso_important_tags.png')

###############################
### RANDOM FOREST REGRESSOR ###
###############################

from sklearn.ensemble import RandomForestRegressor

X_forest = df_clean.drop(columns='income')
y_forest = df_clean['income']

# Log transform dla dochodu (nadal zalecany, by wyrównać rozkład)
y_forest_log = np.log1p(y_forest)

X_forest_train, X_forest_test, y_forest_train, y_forest_test = train_test_split(
    X_forest, y_forest_log, test_size=0.2, random_state=42)

rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)

rf.fit(X_forest_train, y_forest_train)

y_forest_pred = rf.predict(X_forest_test)
r2 = r2_score(y_forest_test, y_forest_pred)

print(f'\nWspółczynnik R^2 (Random Forest): {r2:.4f}')

# Feature Importance
# To odpowiednik 'coefficients' z Lasso, ale pokazuje realny wpływ na decyzje modelu
importances = pd.Series(rf.feature_importances_, index=X.columns)
important_features = importances.sort_values(ascending=False)

print('\nTOP 15 NAJWAŻNIEJSZYCH TAGÓW (RF):')
print(important_features.head(15))

# ElasticNet?
# Można policzyć różnicę średnich jak jest tag (1) vs jak go nie ma (0)
# Może dodać jako feature, z jakiego roku to jest przychód (Nutzungsjahr w statementach GEMY)?
# Test U Manna-Whitney'a?
# Trzeba jeszcze uzupełnić listę tytułów tracków
