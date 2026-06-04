import csv
import os
from main_yield import *

def save_to_csv(data, filename='data_good_test.csv'):
    # Check if file exists to determine if we need to write headers
    file_exists = os.path.isfile(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Write headers if file doesn't exist
        if not file_exists:
            writer.writerow(Yield_columns)

        # Write all data rows
        writer.writerows(data)







Final_Result = Output_normalize_PLC_single_workpiece('2025-11-27 11:09:28','2026-09-05 14:10:37'
)

save_to_csv(Final_Result)

print(f"Data has been saved to data.csv ({len(Final_Result)} rows)")