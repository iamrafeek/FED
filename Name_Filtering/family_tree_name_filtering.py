import random
import jellyfish
import pandas as pd
from rapidfuzz import fuzz

#data loadingHI2HDIIODJDJWDJ
df=pd.read_csv('family_tree.csv')

#Group by the specified columns
grouped = df.groupby(['NAME_1', 'GENDER_1', 'RELATION_DESC', 'GENDER_2'], as_index=False)

#These code lines are used to find Count of groups..If we need to find the count change the comment to code:)
# unique_groups_count = len(grouped)
# print(f"Total unique groups: {unique_groups_count}") 



#function for taking the lengthy name
def select_most_charactered_name(group):
    return group.loc[group['NAME_2'].str.len().idxmax()]


#####First step in filtering#####

def filter_records_1(group):
    records_to_keep = []
    already_compared = set()  # To track comparisons and avoid repeats

    for i, row_i in group.iterrows():
        if i in already_compared:
            continue  # Skip if already selected or compared unfavorably

        best_record = row_i  # Assume current record is the best to keep
        for j, row_j in group.iterrows():
            if i == j or j in already_compared:
                continue  # Avoid self-comparison and re-checking

            similarity_ratio = fuzz.token_set_ratio(row_i['NAME_2'], row_j['NAME_2'])

            if similarity_ratio >= 80:
                # If names are similar, decide which one to keep
                if len(row_i['NAME_2']) < len(row_j['NAME_2']):
                    best_record = row_j  # Keep the record with the lengthier NAME_2
                elif len(row_i['NAME_2']) == len(row_j['NAME_2']):
                    best_record = random.choice([row_i, row_j])  # Randomly choose if lengths are equal

                already_compared.add(j)  # Mark the compared record

        records_to_keep.append(best_record)
        already_compared.add(i)  # Mark the current record as processed

    return pd.DataFrame(records_to_keep)

# Apply the filtering function to each group
result_df = df.groupby(['NAME_1', 'GENDER_1', 'RELATION_DESC', 'GENDER_2'], as_index=False).apply(filter_records_1).reset_index(drop=True)

# result_df.shape

corrected_data1=result_df

#####Second step in filtering####

def filter_records_2_with_soundex(group):
    records_to_keep = []
    already_compared = set()  # To track comparisons and avoid repeats

    for i, row_i in group.iterrows():
        if i in already_compared:
            continue  # Skip if already selected or compared unfavorably

        best_record = row_i  # Assume current record is the best to keep
        soundex_i = jellyfish.soundex(row_i['NAME_2'])  # Compute Soundex for NAME_2 of current record

        for j, row_j in group.iterrows():
            if i == j or j in already_compared:
                continue  # Avoid self-comparison and re-checking

            soundex_j = jellyfish.soundex(row_j['NAME_2'])  # Compute Soundex for NAME_2 of the compared record

            if soundex_i == soundex_j:
                # If Soundex codes match, decide which one to keep based on the length of NAME_2
                if len(row_i['NAME_2']) < len(row_j['NAME_2']):
                    best_record = row_j  # Keep the record with the lengthier NAME_2
                elif len(row_i['NAME_2']) > len(row_j['NAME_2']):
                    best_record = row_i  # Keep the current record if it has the lengthier NAME_2
                else:
                    best_record = random.choice([row_i, row_j])  # Randomly choose if lengths are equal

                already_compared.add(j)  # Mark the compared record

        records_to_keep.append(best_record)
        already_compared.add(i)  # Mark the current record as processed

    return pd.DataFrame(records_to_keep)

# Apply the filtering function to each group
result_df = corrected_data1.groupby(['NAME_1', 'GENDER_1', 'RELATION_DESC', 'GENDER_2'], as_index=False).apply(filter_records_2_with_soundex).reset_index(drop=True)

######Third step in filtering######

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

            if similarity_ratio >= 80:
                # If names are similar, decide which one to keep
                if len(row_i['NAME_2']) < len(row_j['NAME_2']):
                    best_record = row_j  # Keep the record with the lengthier NAME_2
                elif len(row_i['NAME_2']) == len(row_j['NAME_2']):
                    best_record = random.choice([row_i, row_j])  # Randomly choose if lengths are equal

                already_compared.add(j)  # Mark the compared record

        records_to_keep.append(best_record)
        already_compared.add(i)  # Mark the current record as processed

    return pd.DataFrame(records_to_keep)

# Apply the filtering function to each group
result_df = result_df.groupby(['NAME_1', 'GENDER_1', 'RELATION_DESC', 'GENDER_2'], as_index=False).apply(filter_records_3).reset_index(drop=True)

result_df.to_csv('result.csv')

output_df=result_df

