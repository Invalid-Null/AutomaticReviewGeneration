import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from math import pi
import tqdm
fontsize=19
matplotlib.rc("font", family = "Arial", weight = "regular",size=fontsize)
matplotlib.rcParams['axes.unicode_minus']=False
def create_material_radar_chart_top_center_start(dataframe,filename):
    def create_radar_chart(ax, angles, values, color, label, marker,fill):
        ax.plot(angles, values, color=color, linewidth=2, linestyle='solid', marker=marker,markersize=11, label=label)
        if fill:
            ax.fill(angles, values, color=color, alpha=0.25)
    filtered_data = dataframe[~(dataframe[['Selectivity','ConvertedStability']]==0).all(axis=1)]
    sorted_data_reordered = filtered_data.sort_values(by='Selectivity', ascending=False)
    num_vars = len(sorted_data_reordered)
    angles_reordered = np.linspace(0, 4 * pi / 2, num_vars, endpoint=False).tolist() + [0]
    index_max_selectivity =np.argmin([abs(i-3*pi/2) for i in angles_reordered])
    sorted_data_rotated = sorted_data_reordered.iloc[np.roll(np.arange(len(sorted_data_reordered)), -index_max_selectivity)].reset_index(drop=True)
    values_selectivity_rotated = sorted_data_rotated['Selectivity'].tolist() + [sorted_data_rotated['Selectivity'].iloc[0]]
    max_stability_rotated = max(sorted_data_rotated['ConvertedStability'])
    scaled_stability_rotated = [s * 100 / max_stability_rotated for s in sorted_data_rotated['ConvertedStability']]
    values_stability_rotated = scaled_stability_rotated + [scaled_stability_rotated[0]]
    fig, ax = plt.subplots(figsize=(11, 11), subplot_kw=dict(polar=True))
    plt.xticks(angles_reordered[:-1], sorted_data_rotated['Unnamed: 0'])
    for label, angle in zip(ax.get_xticklabels(), angles_reordered):
        angle=angle-pi/2
        if angle in (0, pi):
            label.set_horizontalalignment('center')
        elif 0 < angle < pi:
            label.set_horizontalalignment('right')
        else:
            label.set_horizontalalignment('left')
        label.set_verticalalignment('center')
    create_radar_chart(ax, angles_reordered, values_selectivity_rotated, 'blue', 'Selectivity', marker='o',fill=False)
    create_radar_chart(ax, angles_reordered, values_stability_rotated, 'green', 'Stability (Scaled)', marker='d',fill=True)
    plt.yticks(np.linspace(-20, 100, 7), [f"{int(t)}%" if t>=0 else '' for t in np.linspace(-20, 100, 7)], color="black")
    plt.legend(loc='upper right', frameon=False, facecolor='none',bbox_to_anchor=(1.1, 1.1),)
    plt.tight_layout()
    plt.savefig(filename.replace('.csv', '.svg'),transparent=True)
AllInfluencingFactor=['Type',  'StructureType', 'SupportMaterial', 'PreparationMethod',
                      'InletFlowRate', 'ReactionTemperature','PropanePartialPressure',
                      'CompositionElements','PromoterElements','ActiveSpeciesElements',]
for IF in tqdm.tqdm(AllInfluencingFactor):
    file_path_new = f'{IF}Top5.csv'
    try:
        data_new = pd.read_csv(file_path_new)
        create_material_radar_chart_top_center_start(data_new, file_path_new)
    except Exception as e:
        print(f"An error occurred: {e}")
