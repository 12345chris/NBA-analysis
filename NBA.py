from datetime import datetime as dtime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyecharts.charts as pye
from pyecharts import options as opts
from pyecharts.globals import ThemeType

# Read data
data = pd.read_excel(r'player.xlsx')

# Drop unnecessary columns
new_data = data.drop(['link', 'en_height', 'en_weight'], axis=1)

# Count rows in Excel
def count_excel_rows(file_path):
    df = pd.read_excel(file_path)
    num_rows = df.shape[0]
    return num_rows

file_path = "player.xlsx"
num_rows = count_excel_rows(file_path)
print("Total number of rows in Excel:", num_rows)

# Check duplicates
print("Number of duplicate entries:", new_data.duplicated().sum())

# Check missing values
print("Missing values:\n", new_data.isnull().sum())

# Fill missing values
new_data['number'].fillna(0, inplace=True)
print("Missing values after filling:\n", new_data.isnull().sum())

# Data cleaning (remove units)
new_data['zh_weight'] = new_data['zh_weight'].str.replace('kg', '').astype(float)
new_data['salary'] = new_data['salary'].str.replace('ten thousand USD', '').astype(float)
new_data['zh_height'] = new_data['zh_height'].str.replace('m', '').astype(float) * 100
new_data['position'] = new_data['position'].replace({'G-F': 'F-G', 'C-F': 'F-C'})

# Drop rows with missing salary
new_data = new_data.dropna(subset=['salary'])

# Convert data types
new_data = new_data.astype({'number': 'int', 'zh_height': 'int', 'zh_weight': 'int', 'salary': 'float'})
new_data['birthday'] = pd.to_datetime(new_data['birthday'], format='%Y/%m/%d')

# Boxplot
new_data.boxplot(column=['number', 'zh_height', 'zh_weight', 'salary'])
plt.savefig("boxplot.png")
plt.close()

# Group by team and rank total salary
team_df = new_data.groupby('team', as_index=False)['salary'].sum().sort_values(by='salary', ascending=False)
bar = (
    pye.Bar(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND))
    .add_xaxis(team_df['team'].tolist())
    .add_yaxis('Salary (10K USD)', team_df['salary'].tolist())
    .set_global_opts(
        title_opts=opts.TitleOpts(title='Team - Total Salary'),
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=80))
    )
)
bar.render("team_salary_bar.html")

# Rank by descending salary
player_df = new_data.sort_values(by='salary', ascending=False)

# Divide players into salary bins
salary_bin = np.linspace(0, max(player_df['salary']), 10, endpoint=True)
salary_cut = pd.cut(player_df['salary'], salary_bin)
print('Player salary distribution by interval:')
print(salary_cut.value_counts(sort=False))

hist = (
    pye.Bar(init_opts=opts.InitOpts(theme=ThemeType.VINTAGE))
    .add_xaxis([str(interval) for interval in salary_bin])
    .add_yaxis("Player Count", salary_cut.value_counts(sort=False).tolist(), category_gap=0)
    .set_global_opts(title_opts=opts.TitleOpts(title="Player Salary Distribution"))
)
hist.render("salary_distribution_bar.html")

# Top 20 salaries
bar = (
    pye.Bar(init_opts=opts.InitOpts(theme=ThemeType.CHALK))
    .add_xaxis(player_df['name'][0:20].tolist())
    .add_yaxis('Salary (10K USD)', player_df['salary'][0:20].tolist())
    .set_global_opts(
        title_opts=opts.TitleOpts(title='Top 20 Salaries'),
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45))
    )
)
bar.render("top_20_salary_bar.html")

# Bottom 20 salaries
bar = (
    pye.Bar(init_opts=opts.InitOpts(theme=ThemeType.DARK))
    .add_xaxis(player_df['name'][-20:].tolist())
    .add_yaxis('Salary (10K USD)', player_df['salary'][-20:].tolist())
    .set_global_opts(
        title_opts=opts.TitleOpts(title='Bottom 20 Salaries'),
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-30), is_inverse=True)
    )
)
bar.render("bottom_20_salary_bar.html")

# Average salary by position
position_salary_df = player_df.groupby('position', as_index=False)['salary'].mean()
position_salary_df['salary'] = position_salary_df['salary'].astype(int)
pie = (
    pye.Pie(init_opts=opts.InitOpts(theme=ThemeType.WESTEROS))
    .add('Position: Avg Salary', [list(z) for z in zip(position_salary_df['position'], position_salary_df['salary'])],
         radius=[50, 120], center=["35%", "50%"])
    .set_global_opts(
        title_opts=opts.TitleOpts(title="Avg Salary by Position (10K USD)"),
        legend_opts=opts.LegendOpts(pos_left="35%", pos_top="5%")
    )
    .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
)
pie.render("position_salary_pie.html")

# Height & weight by position
position_df = new_data.groupby('position', as_index=False)['zh_height'].mean()
position_df2 = new_data.groupby('position', as_index=False)['zh_weight'].mean()
position_body_df = pd.merge(position_df, position_df2, on='position')
position_body_df = position_body_df.astype({'zh_height': 'int', 'zh_weight': 'int'})
print('Average Height/Weight by Position:')
print(position_body_df)

# Player number distribution
number_df = new_data.groupby('number', as_index=False).count()
hist = (
    pye.Bar(init_opts=opts.InitOpts(theme=ThemeType.MACARONS))
    .add_xaxis(number_df['number'].tolist())
    .add_yaxis("Player Count", number_df['name'].tolist(), category_gap=0)
    .set_global_opts(title_opts=opts.TitleOpts(title="Player Number Distribution"))
)
hist.render("player_number_bar.html")

# Position-number player count
position_df2 = new_data.groupby('position', as_index=False).count()
pos_num_lis = []
number_position_df = new_data.groupby(['position', 'number'], as_index=False).count()
number_position_df = number_position_df[~(number_position_df['name'] < 3)]

for x, y in zip(number_position_df['position'], number_position_df['number']):
    pos_num_lis.append(x + '/' + str(y))

# Nested donut chart
pie = (
    pye.Pie(init_opts=opts.InitOpts(theme=ThemeType.WALDEN))
    .add('Position/Count', [list(z) for z in zip(position_df2['position'], position_df2['name'])],
         radius=[0, '30%'], center=["35%", "50%"],
         label_opts=opts.LabelOpts(position="inner"))
    .add('Number/Count', [list(z) for z in zip(pos_num_lis, number_position_df['name'])],
         radius=["40%", "55%"], center=["35%", "50%"],
         label_opts=opts.LabelOpts(position="outside", formatter="{b}: {c}"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="Player-Number-Position Distribution"),
        legend_opts=opts.LegendOpts(orient='vertical', pos_right="5%")
    )
)
pie.render("player_number_position_pie.html")

# Calculate player age
nowdate = dtime.today()
player_df['age'] = (nowdate - player_df['birthday']) / pd.Timedelta('365 days')
player_df['age'] = player_df['age'].astype(int)

# Avg salary by age
age_df = player_df.groupby('age', as_index=False)['salary'].mean()
age_df['salary'] = age_df['salary'].astype(int)

# Age vs avg salary line chart
line = (
    pye.Line(init_opts=opts.InitOpts(theme=ThemeType.WALDEN))
    .add_xaxis(age_df['age'].astype(str).tolist())
    .add_yaxis('Salary (10K USD)', age_df['salary'].tolist())
    .set_global_opts(
        title_opts=opts.TitleOpts(title="Age - Avg Salary (10K USD)"),
        xaxis_opts=opts.AxisOpts(type_="category"),
        yaxis_opts=opts.AxisOpts(interval=100, min_="dataMin", max_="dataMax")
    )
)
line.render("age_salary_line.html")

# Calculate BMI
new_data['bmi'] = round(new_data['zh_weight'] / (new_data['zh_height'] / 100) ** 2, 2)
print('Player BMI Overview:')
print(new_data['bmi'].describe())

# Avg BMI by position
bmi_df = new_data.groupby('position', as_index=False)['bmi'].mean()
bmi_df = bmi_df.sort_values(by='bmi', ascending=False)
print('\nAverage BMI by Position:')
print(bmi_df)

# Bar chart for BMI by position
bar = (
    pye.Bar(init_opts=opts.InitOpts(theme=ThemeType.CHALK))
    .add_xaxis(bmi_df['position'].tolist())
    .add_yaxis('BMI Index', bmi_df['bmi'].round(2).tolist())
    .set_global_opts(
        title_opts=opts.TitleOpts(title='Avg BMI by Position'),
        yaxis_opts=opts.AxisOpts(interval=0.2, min_="dataMin", max_="dataMax")
    )
)
bar.render("position_bmi_bar.html")

# BMI distribution
bmi_bin = np.linspace(new_data['bmi'].min(), new_data['bmi'].max(), 10, endpoint=True)
bmi_cut = pd.cut(new_data['bmi'], bmi_bin)

hist = (
    pye.Bar(init_opts=opts.InitOpts(theme=ThemeType.VINTAGE))
    .add_xaxis([f"[{b.left:.2f}, {b.right:.2f})" for b in bmi_cut.categories])
    .add_yaxis("Player Count", bmi_cut.value_counts().sort_index().tolist(), category_gap=0)
    .set_global_opts(title_opts=opts.TitleOpts(title="BMI Distribution of Players"))
)
hist.render("bmi_distribution_bar.html")
