import os
import re
import tqdm
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
fontsize=19
matplotlib.rc("font", family = "Arial", weight = "regular",size=fontsize)
matplotlib.rcParams['axes.unicode_minus']=False
def calculate_yearly_frequency(df):
    yearly_freq = df.groupby(['Element', 'Year']).size().reset_index(name='Frequency')
    max_freq = yearly_freq['Frequency'].max()
    yearly_freq['Normalized_Frequency'] = yearly_freq['Frequency'].apply(lambda x: 0.1 + 0.9*(x/max_freq))
    return yearly_freq
def plot_gantt_chart_category_specific(df, start_end_df, yearly_frequency, category, base_color,Title):
    category_df = df[df['Category'] == category].copy()
    category_df = category_df.sort_values(by=category)
    fig, ax = plt.subplots(figsize=(11, 11))
    space = 0.8
    Years={element:int(start_end_df[start_end_df[category] == element]['Start_Date'].values[0]) for element in category_df[category].dropna().unique()}
    elements=dict(sorted(Years.items(), key=lambda item: -item[1]))
    for (idx, element),item_base_color in zip(enumerate(elements.keys()),base_color):
        start_year = int(start_end_df[start_end_df[category] == element]['Start_Date'].values[0])
        end_year = int(start_end_df[start_end_df[category] == element]['End_Date'].values[0])
        for year in range(start_year, end_year + 1):
            if year in yearly_frequency[yearly_frequency[category] == element]['Year'].values:
                normalized_frequency = yearly_frequency.loc[(yearly_frequency[category] == element) & 
                                                            (yearly_frequency['Year'] == year), 'Normalized_Frequency'].values[0]
                color = mcolors.to_rgba(item_base_color, alpha=normalized_frequency)
                ax.add_patch(plt.Rectangle((year, idx - space/2), 1, space, facecolor=color,edgecolor='none'))
        rect = plt.Rectangle((start_year, idx - space/2),
                             end_year - start_year + 1, 
                             space, 
                             fill=False, 
                             edgecolor='black', 
                             linewidth=0.5)
        ax.add_patch(rect)
    ax.set_yticks(range(len(elements)))
    ax.set_yticklabels(elements)
    ax.set_ylim([-0.5, len(elements) - 0.5])
    ax.set_xlim([df['Year'].min() - 0.5, df['Year'].max() + 1.5])
    ax.set_xlabel('Year')
    ax.grid(False)
    plt.setp(ax.get_yticklabels(), rotation=45, verticalalignment='top')
    plt.tight_layout()
    plt.savefig(f'{Title}.svg',transparent=True)
    with open(f'{Title}.svg', 'r') as file:
        content = file.read()
    content = re.sub(r'fill:\s*#FFFFFF', 'fill-opacity:0', content, flags=re.IGNORECASE)
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'fill-opacity:0' in line:
            lines[i] = re.sub(r'fill-opacity:(?!0)[^;]*;', '', line)
    content = '\n'.join(lines)
    content=content.replace('font-family:TimesNewRomanPSMT','font-family:Times New Roman')
    content=content.replace('font-family:TimesNewRomanPS','font-family:Times New Roman')
    content=content.replace('font-family:PMingLiU','font-family:Times New Roman')
    content=content.replace('font-family:ArialMT','font-family:Times New Roman')
    with open(f'{Title}.svg', 'w') as file:
        file.write(content)
def plot_gantt_chart_from_csv(file_path, category, category_color='k',Title=''):
    df = pd.read_csv(file_path)
    df['Category'] = category
    element_start_end = df.groupby(category).agg(Start_Date=('Year', 'min'), End_Date=('Year', 'max')).reset_index()
    yearly_frequency = df.groupby([category, 'Year']).size().reset_index(name='Frequency')
    max_freq = yearly_frequency['Frequency'].max()
    yearly_frequency['Normalized_Frequency'] = yearly_frequency['Frequency'].apply(lambda x: 0.1 + 0.9*(x/max_freq))
    plot_gantt_chart_category_specific(df, element_start_end, yearly_frequency, category, category_color,Title)
for i in tqdm.tqdm(['Type.csv','ActiveSpeciesElements.csv', 'CompositionElements.csv', 'PreparationMethod.csv', 'PromoterElements.csv', 'StructureType.csv', 'SupportMaterial.csv', 'TypeIdentify.csv']):
    plot_gantt_chart_from_csv(i, 'Element' if 'Element' in i else i.replace('.csv',''),
                              [mcolors.to_hex([j/255 for j in i]) for i in [
                                  [112,48,160],[0,112,192],[0,176,80],[192,0,0],[204,153,0],
                                  [112,  48, 160],
                                   [  0, 112, 192],
                                   [  0, 176,  80],
                                   [192,   0,   0],
                                   [204, 153,   0],
                                   [ 94, 104,  99],
                                   [161, 213, 162],
                                   [207,  29,  32],
                                   [ 25,  61,  75],
                                   [ 32, 220,  84],
                                   [151,  40, 226],
                                   [157,  58,  84],
                                   [145, 223,  30],
                                   [224,  98, 216],
                                   [ 96, 181,  82],
                                   [125,  30,  34],
                                   [225, 158,  91],
                                   [ 81,  26, 218],
                                   [ 37, 166, 147],
                                   [ 91, 218, 161],
                                   [ 97,  97, 221],
                                   [ 88,  90,  34],
                                   [225, 221, 135],
                                   [161,  95,  24],
                                   [155, 129,  84],
                                   [ 29,  26, 152],
                                   [ 35, 132,  26],
                                   [209, 162,  26],
                                   [163,  91, 177],
                                   [ 30, 136, 218],
                                   [163,  27, 144],
                                   [127, 224, 226],
                                   [161, 148, 224],
                                   [200, 143, 152],
                                   [ 51, 216,  27],
                                   [ 80,  31,  99],
                                   [ 32, 228, 157],
                                   [221, 228,  44],
                                   [103,  49, 160],
                                   [116, 161,  25],
                                   [223,  31, 207],
                                   [114, 145, 155],
                                   [227, 163, 209],
                                   [ 36,  96, 153],
                                   [227,  92,  37],
                                   [223,  25, 102],
                                   [120, 231,  98],
                                   [ 41,  25,  29],
                                   [215, 223, 219],
                                   [ 38, 222, 227]]],i.replace('.csv',''))
