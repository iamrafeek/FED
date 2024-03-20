import random
import jellyfish
import pandas as pd
from rapidfuzz import fuzz
from Levenshtein import distance as levenshtein_distance 

while True:

    # Define the columns of your DataFrame
    columns = ['NAME_1', 'GENDER_1', 'RELATION_DESC', 'NAME_2', 'GENDER_2']

    # Ask the user for the number of rows they want to add
    num_rows = int(input("How many rows do you want to add? "))

    # Initialize an empty list to hold row data
    data = []

    # Loop through the number of rows, asking for input each time
    for _ in range(num_rows):
        row_input = input(f"Enter values for row {_+1}, separated by commas (Format: NAME_1,GENDER_1,RELATION_DESC,NAME_2,GENDER_2): ")
        row_data = row_input.split(",")
        if len(row_data) == len(columns):  # Ensure the row has the correct number of values
            data.append(row_data)
        else:
            print("Invalid number of values entered. Please enter the correct number of values.")
            break  # Exit the loop if the number of values is incorrect


    df = pd.DataFrame(data, columns=columns)



    #Group by the specified columns
    grouped = df.groupby(['NAME_1', 'GENDER_1', 'RELATION_DESC', 'GENDER_2'], as_index=False)

    #function for taking the lengthy name
    def select_most_charactered_name(group):
        return group.loc[group['NAME_2'].str.len().idxmax()]

    
    def filter_records_3(group):
        records_to_keep = []
        already_compared = set()  # To track comparisons and avoid repeats

        for i, row_i in group.iterrows():
            if i in already_compared:
                continue  # Skip if already selected or compared unfavorably

            best_record = row_i  # Assume current record is the best to keep
            for j, row_j in group.iterrows():
                if i == j or j in already_compared:
                    continue  # Avoid self-comparison and re-checking

                similarity_ratio = fuzz.partial_ratio(row_i['NAME_2'], row_j['NAME_2'])
                print("s :", similarity_ratio)
                if similarity_ratio >= 70:
                    lev_distance = levenshtein_distance(row_i['NAME_2'], row_j['NAME_2'])
                    print("l: ", lev_distance)
                    if lev_distance > 3:
                            # Decide which one to keep based on the name length or randomly if lengths are equal
                            if len(row_i['NAME_2']) < len(row_j['NAME_2']):
                                best_record = row_j  # Keep the record with the lengthier NAME_2
                            elif len(row_i['NAME_2']) == len(row_j['NAME_2']):
                                best_record = random.choice([row_i, row_j])  # Randomly choose if lengths are equal
                            already_compared.add(j)  # Mark the compared record as processed
                    else:
                            # Levenshtein distance is greater than 3, so keep both records
                            keep_both = True
                            break  # No need to compare with other records since we're keeping both

            records_to_keep.append(best_record)
            already_compared.add(i)  # Mark the current record as processed

        return pd.DataFrame(records_to_keep)
    

    def filter_records_4(group):
        records_to_keep = []
        already_compared = set()  # To track comparisons and avoid repeats

        for i, row_i in group.iterrows():
            if i in already_compared:
                continue  # Skip if already selected or compared unfavorably

            best_record = row_i  # Assume current record is the best to keep
            for j, row_j in group.iterrows():
                if i == j or j in already_compared:
                    continue  # Avoid self-comparison and re-checking

                similarity_ratio = fuzz.partial_ratio(row_i['NAME_2'], row_j['NAME_2'])
                print("s :", similarity_ratio)
                if similarity_ratio >= 70:
                    lev_distance = levenshtein_distance(row_i['NAME_2'], row_j['NAME_2'])
                    print("l: ", lev_distance)
                    if lev_distance >0:
                            # Decide which one to keep based on the name length or randomly if lengths are equal
                            if len(row_i['NAME_2']) < len(row_j['NAME_2']):
                                best_record = row_j  # Keep the record with the lengthier NAME_2
                            elif len(row_i['NAME_2']) == len(row_j['NAME_2']):
                                best_record = random.choice([row_i, row_j])  # Randomly choose if lengths are equal
                            already_compared.add(j)  # Mark the compared record as processed
                    else:
                            # Levenshtein distance is greater than 3, so keep both records
                            keep_both = True
                            break  # No need to compare with other records since we're keeping both

            records_to_keep.append(best_record)
            already_compared.add(i)  # Mark the current record as processed

        return pd.DataFrame(records_to_keep)
       


    # Apply the filtering function to each group
    result_df = df.groupby(['NAME_1', 'GENDER_1', 'RELATION_DESC', 'GENDER_2'], as_index=False).apply(filter_records_3).reset_index(drop=True)
    print(result_df)
    result_df = result_df.groupby(['NAME_1', 'GENDER_1', 'RELATION_DESC', 'GENDER_2'], as_index=False).apply(filter_records_4).reset_index(drop=True)

    output_df=result_df

    print(output_df)
