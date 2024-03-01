import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import tqdm
import os
import re
fontsize=19
matplotlib.rc("font", family = "Arial", weight = "regular",size=fontsize)
matplotlib.rcParams['axes.unicode_minus']=False
def outliers_iqr(data):
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 2 * IQR
    upper_bound = Q3 + 2 * IQR
    return ~data.between(lower_bound, upper_bound)
def calculate_linewidths(data, max_linewidth=5, min_linewidth=0.5, scaling_factor=1):
    data = np.nan_to_num(data, nan=0.0)
    data[data == 0] = np.min(data[np.nonzero(data)])
    if np.all(data == 0):
        return np.zeros_like(data)
    log_data = np.log10(data)
    log_range = np.log10(np.max(data)) - np.log10(np.min(data))
    log_normalized_data = scaling_factor * (np.log10(np.max(data)) - log_data)
    linewidths = min_linewidth + (max_linewidth - min_linewidth) * (log_normalized_data - np.min(log_normalized_data)) / (np.max(log_normalized_data) - np.min(log_normalized_data))
    linewidths[data == 0] = 0
    return linewidths
def draw_bubble_plot(filename):
    global data
    data = pd.read_csv(filename)
    factor_x, factor_y = os.path.splitext(filename)[0].split('-')
    data = data.sort_values(by=[factor_x, factor_y],ignore_index=True)
    if np.issubdtype(data['Selectivity'].dtype, np.number):
        selectivity_outliers = outliers_iqr(data['Selectivity'])
    else:
        selectivity_outliers = pd.Series([False]*len(data))
    if np.issubdtype(data['ConversionRate'].dtype, np.number):
        conversion_rate_outliers = outliers_iqr(data['ConversionRate'])
    else:
        conversion_rate_outliers = pd.Series([False]*len(data))
    if np.issubdtype(data['ConvertedStability'].dtype, np.number):
        ConvertedStability_outliers = outliers_iqr(data['ConvertedStability'])
    else:
        ConvertedStability_outliers = pd.Series([False]*len(data))
    if np.issubdtype(data[factor_x].dtype, np.number):
        factor_x_outliers = outliers_iqr(data[factor_x])
    else:
        factor_x_outliers = pd.Series([False]*len(data))
    if np.issubdtype(data[factor_y].dtype, np.number):
        factor_y_outliers = outliers_iqr(data[factor_y])
    else:
        factor_y_outliers = pd.Series([False]*len(data))
    combined_outliers = selectivity_outliers | conversion_rate_outliers | ConvertedStability_outliers | factor_x_outliers | factor_y_outliers 
    global filtered_data
    filtered_data = data[~combined_outliers]
    plt.figure(figsize=(17,17))
    edgecolor='g'
    linewidths=calculate_linewidths(filtered_data['ConvertedStability'], max_linewidth=3, min_linewidth=0.2, scaling_factor=5)
    scatter = plt.scatter(
        filtered_data[factor_x], 
        filtered_data[factor_y], 
        s=filtered_data['ConversionRate']**4/1E4, 
        facecolors='none',
        edgecolors=[(*matplotlib.colors.to_rgb(edgecolor),linewidths[i]/np.max(linewidths)/3) for i in range(len(filtered_data))] ,
        linewidths=linewidths,
        marker="o"
    )
    scatter = plt.scatter(
        filtered_data[factor_x], 
        filtered_data[factor_y], 
        s=filtered_data['ConversionRate']**4/1E4, 
        c=filtered_data['Selectivity'], 
        cmap="Blues",
        alpha=filtered_data['Selectivity']**2/1E5, 
        edgecolors='none',
        linewidths=0,
        marker="o"
    )
    plt.xlabel('\n'.join(re.findall(r'[A-Z][a-z]*', factor_x)),fontsize=fontsize*1.5).set_horizontalalignment('left')
    plt.ylabel(' '.join(re.findall(r'[A-Z][a-z]*', factor_y)),fontsize=fontsize*1.5).set_horizontalalignment('left')
    ax = plt.gca()
    if not np.issubdtype(data[factor_x].dtype, np.number):
        plt.setp(ax.get_xticklabels(), rotation=45, horizontalalignment='center')
        ax.tick_params(axis='x', which='major', pad=0,) 
    if not np.issubdtype(data[factor_y].dtype, np.number):
        plt.setp(ax.get_yticklabels(), rotation=45, verticalalignment='top')
        ax.tick_params(axis='y', which='major', pad=0,) 
    ax.xaxis.set_label_coords(1., -0.025)
    plt.title(f'{factor_x} - {factor_y} for Selectivity, Conversion and Stability',fontdict={'size':fontsize*1.5})
    cbar = plt.colorbar(scatter)
    cbar.set_label('Selectivity')
    sizes = [25, 50, 75]
    conversion_rate_labels = ["25% Conversion", "50% Conversion", "75% Conversion"]
    conversion_rate_legends = [plt.Line2D([0], [0], ls="", marker="o", markersize=np.sqrt(size**4/1e5), markerfacecolor="b",
                                          markeredgecolor='none',markeredgewidth=0,alpha=0.5) for size in sizes]
    stability_sizes = [0.5, 1, 3]
    stability_labels = ["Low Stability", "Medium Stability", "High Stability"]
    converted_stability_legends = [
        plt.Line2D([0], [0], ls="", marker="o", markersize=13,alpha=0.5, 
                   markerfacecolor="none", markeredgecolor=edgecolor, markeredgewidth=lw)
        for lw in stability_sizes
    ]
    all_legends = conversion_rate_legends + converted_stability_legends
    all_labels = conversion_rate_labels + stability_labels
    plt.legend(handles=all_legends, labels=all_labels, title=None,
               loc="best",frameon=False,facecolor='none')
    plt.tight_layout()
    plt.savefig(filename.replace('.csv', '.svg'))
    with open(filename.replace('.csv', '.svg'), 'r') as file:
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
    with open(filename.replace('.csv', '.svg'), 'w') as file:
        file.write(content)
    plt.close()
    print()
AllInfluencingFactor=['Type',  'StructureType', 'SupportMaterial', 'PreparationMethod',
                      'InletFlowRate', 'ReactionTemperature','PropanePartialPressure',
                      'CompositionElements','PromoterElements','ActiveSpeciesElements',]
import itertools
for Item in tqdm.tqdm(list(itertools.combinations(AllInfluencingFactor, 2))):
    filename = f"{Item[0]}-{Item[1]}.csv"
    if os.path.exists(filename):
        draw_bubble_plot(filename)
