from pathlib import Path
import pandas as pd


data_path = Path(__file__).parent / "dft_rawcount_years_cut.xlsx"
df = pd.read_excel(data_path)

# ---- USER INPUT ----
# Use a count_point_id that exists for hour=8 in 2020-2024 (from data analysis)
# valid candidates: 27782, 27796, 56582, 57603, 808667
count_point_id = 7724
target_hour = 12

# ---- Get last 5 years ----
point_data = df[df['count_point_id'] == count_point_id]
max_year = point_data['year'].max()
last_5_years = list(range(max_year - 4, max_year + 1))

# ---- Filter data ----
filtered = df[
    (df['count_point_id'] == count_point_id) &
    (df['hour'] == target_hour) &
    (df['year'].isin(last_5_years))
]

# ---- Compute average ----
no_cars = filtered['cars_and_taxis']
no_buses = filtered['buses_and_coaches'] * 3
no_lgvs = filtered['lgvs'] * 3
no_hgvs_2 = filtered['hgvs_2_rigid_axle'] * 2
no_hgvs_3_or_4 = filtered['hgvs_3_rigid_axle'] * 3 + filtered['hgvs_4_or_more_rigid_axle'] * 3 + filtered['hgvs_3_or_4_articulated_axle'] * 3
no_hgvs_5_or_6 = filtered['hgvs_5_articulated_axle'] * 4 + filtered['hgvs_6_articulated_axle'] * 4

effective_no_cars =  (
    no_cars +
    no_buses +
    no_lgvs +
    no_hgvs_2 +
    no_hgvs_3_or_4 +
    no_hgvs_5_or_6).sum()
avg_cars = effective_no_cars/5

print("latest_year", max_year)
print("last_5_years", last_5_years)
print("filtered rows", filtered.shape[0])

if filtered.empty:
    raise ValueError(
      f"No records for count_point_id={count_point_id}, hour={target_hour}, years={last_5_years}"
    )

if pd.isna(avg_cars):
    raise ValueError("cars_and_taxis all null in filtered rows")

print(f"Average cars at {target_hour}:00 over last 5 years: {avg_cars}")