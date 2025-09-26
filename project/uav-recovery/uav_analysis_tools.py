
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pandas.api.types import is_numeric_dtype, is_object_dtype, is_datetime64_any_dtype
from IPython.display import display

# Define the clean_data function (paste the function below after you define it in the jupyter notebook in step 4 of 02_Data_Cleaning.ipynb)

#PASTE YOUR clean_data(df, noise_floor=-120): FUNCTION FROM THE JUPYTER NOTEBOOK HERE
def clean_data(df, noise_floor=-120):
    """
    Cleans the UAV field report DataFrame.

    This function performs the following steps:
    1.  Standardizes missing value placeholders ('?', 'N/A', '') to np.nan.
    2.  Standardizes 'team_callsign' to lowercase, corrects known typos,
        and fills any missing callsigns with 'unknown'.
    3.  For the 'signal_strength' column, converts it to numeric (coercing errors)
        and imputes missing values (NaNs) with the specified noise_floor.
    4.  For all other numeric columns, converts them to numeric (coercing errors)
        and imputes missing values with the column's median.

    Args:
        df (pd.DataFrame): The raw field report DataFrame.
        noise_floor (int or float, optional): The noise floor (in dBm) to use for
            imputing missing signal strength values. Defaults to -120.

    Returns:
        pd.DataFrame: The cleaned DataFrame.
    """
    
    # Create a copy to avoid modifying the original DataFrame
    df_clean = df.copy()   

    ##########################################################
    ##### START STUDENT CODE HERE:

    # 1. Standardize missing values across the entire DataFrame using .replace()  you should covert all instances of  ['?', 'N/A', ''] to np.nan.
    df_clean.replace(['?', 'N/A', ''], np.nan, inplace=True)



    # 2. Handle categorical typos (team_callsign)
    if 'team_callsign' in df_clean.columns:
        
        # Fill missing values, standardize casing and strip whitespace using .fillna(), .str.lower(), and .str.strip()
        # Chain string operations for efficiency and clarity
        df_clean['team_callsign'] = df_clean['team_callsign'].fillna('unknown').str.lower().str.strip()

        # Correct known typos such as 'alfa' to 'alpha' by using a map of {`from`: `to`} and the .replace() method
        typo_map = {'alfa': 'alpha'}
        df_clean['team_callsign'] = df_clean['team_callsign'].replace(typo_map)


    # 3. Special handling for signal_strength imputation
    if 'signal_strength' in df_clean.columns:

        # Convert to numeric, coercing errors (like 'ERR-&^%') to NaN by using pd.to_numeric() and the errors='coerce' parameter
        df_clean['signal_strength'] = pd.to_numeric(df_clean['signal_strength'], errors='coerce')

        # Impute NaN values with the noise_floor by using the dataframe .fillna() method, passing in the noise_floor parameter 
        df_clean['signal_strength'] = df_clean['signal_strength'].fillna(noise_floor)



    # 4. Identify and impute other numeric columns with their median
    # Exclude columns we've already handled or know are non-numeric using the dataframe .columns.drop() method and the errors='ignore' parameter
    numeric_cols = df_clean.columns.drop(['timestamp', 'team_callsign', 'report_id', 'signal_strength'], errors='ignore')

    for col in numeric_cols:
        # Convert to numeric, coercing errors to NaN using the pd.to_numeric() function with the errors='coerce' parameter
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        # Calculate the median of the now-numeric column using the dataframe .median() method
        median_val = df_clean[col].median()
        # Fill any NaNs (original or coerced) with the median using the dataframe .fillna() method with inplace=True
        df_clean[col] = df_clean[col].fillna(median_val)



    ##### END STUDENT CODE HERE
    ##########################################################
    
    return df_clean




def perform_eda(df, target_column='signal_strength'):
    """
    Performs a comprehensive Exploratory Data Analysis (EDA) on the DataFrame.

    This function provides:
    1.  Basic info and descriptive statistics.
    2.  Distribution plots for each feature.
    3.  Plots of each feature against the target variable.
    4.  A correlation heatmap for numeric features.

    Args:
        df (pd.DataFrame): The DataFrame to analyze.
        target_column (str): The name of the target variable column.
    """
    # 1. Print the DataFrame's .info() and .describe() summaries.
    print("DataFrame Info:")
    df.info()
    print("\nDataFrame Description:")
    display(df.describe(include='all'))

    # 2. Separate the feature columns from the target column.
    if target_column not in df.columns:
        print(f"❌ Target column '{target_column}' not found in DataFrame. Skipping target-related plots.")
        features = df.copy()
        target = None
    else:
        features = df.drop(columns=[target_column])
        target = df[target_column]

    # 3. Loop through each feature column:
    for column in features.columns:
        print(f"\n--- EDA for Feature: '{column}' ---")
        col_series = features[column]

        # --- Special Handling for Specific Columns ---
        if column == 'report_id':
            print("Skipping plots for ID column.")
            continue

        # --- General Plotting Logic ---
        plt.figure(figsize=(14, 6))

        # Plot 1: Distribution of the feature
        plt.subplot(1, 2, 1)
        if is_datetime64_any_dtype(col_series):
            hour_counts = col_series.dt.hour.value_counts().sort_index()
            sns.barplot(x=hour_counts.index, y=hour_counts.values, palette='viridis')
            plt.title('Report Counts by Hour of Day')
            plt.xlabel('Hour of Day')
            plt.ylabel('Number of Reports')
        elif is_numeric_dtype(col_series):
            sns.histplot(col_series, bins=30, kde=True)
            plt.title(f'Distribution of {column}')
        elif is_object_dtype(col_series) or pd.api.types.is_categorical_dtype(col_series):
            # For high-cardinality categoricals, plot top 15
            order = col_series.value_counts().index
            sns.countplot(y=col_series, order=order[:15])
            plt.title(f'Top 15 Counts for {column}')

        # Plot 2: Feature vs. Target (if target exists)
        if target is not None:
            plt.subplot(1, 2, 2)
            if is_numeric_dtype(col_series):
                sns.scatterplot(x=col_series, y=target, alpha=0.6)
                plt.title(f'{column} vs. {target_column}')
            elif is_object_dtype(col_series) or pd.api.types.is_categorical_dtype(col_series):
                order = col_series.value_counts().index
                sns.boxplot(x=target, y=col_series, order=order[:15])
                plt.title(f'{target_column} by Top 15 {column}')

        plt.tight_layout()
        plt.show()

    # 4. After the loop, create a correlation heatmap for all numeric columns in the DataFrame.
    print("\n--- Correlation Analysis ---")
    numeric_cols = df.select_dtypes(include=np.number)
    if not numeric_cols.empty:
        plt.figure(figsize=(12, 10))
        sns.heatmap(numeric_cols.corr(), annot=True, fmt=".2f", cmap='coolwarm', linewidths=.5)
        plt.title('Correlation Heatmap of Numeric Features')
        plt.show()
    else:
        print("No numeric columns found for correlation heatmap.")

    # 5. Sorted scatterplot of signal strength
    if 'signal_strength' in df.columns:
        print("\n--- Sorted Signal Strength ---")
        plt.figure(figsize=(10, 4))
        sorted_signal = df['signal_strength'].sort_values().reset_index(drop=True)
        plt.scatter(sorted_signal.index, sorted_signal.values, alpha=0.7)
        plt.title('Sorted Scatterplot of Signal Strength')
        plt.xlabel('Sorted Index')
        plt.ylabel('Signal Strength')
        plt.show()