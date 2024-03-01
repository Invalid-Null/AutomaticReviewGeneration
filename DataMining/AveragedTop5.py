import pandas as pd
import numpy as np
import re
ElementTable={'Nu': 0, 'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90, 'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100, 'Md': 101, 'No': 102, 'Lr': 103, 'Rf': 104, 'Db': 105, 'Sg': 106, 'Bh': 107, 'Hs': 108, 'Mt': 109, 'Ds': 110, 'Rg': 111, 'Cn': 112, 'Nh': 113, 'Fl': 114, 'Mc': 115, 'Lv': 116, 'Ts': 117, 'Og': 118}
def extract_element(element_str):
    match = re.match(r"([A-Z][a-z]*)(.*)", element_str)
    if match:
        element = match.group(1)
        if element in ElementTable:
            return element
    return None
df=pd.read_csv('AllCleanedResult.csv')
[pd.DataFrame({k:{Metric:v.sort_values(Metric,ascending=False).iloc[:5][Metric].mean() for Metric in ['Selectivity','ConvertedStability']}
 for k,v in df[[Item,'Selectivity','ConvertedStability']].replace([np.inf, -np.inf], np.nan).dropna(subset=[Item]).fillna(0).groupby(Item)}
              ).T.to_csv(f'{Item}Top5.csv')
 for Item in ['Type',  'StructureType', 'SupportMaterial', 'PreparationMethod',
                      'InletFlowRate', 'ReactionTemperature','PropanePartialPressure',]]
pd.DataFrame({k:{Metric:v.sort_values(Metric,ascending=False).iloc[:5][Metric].mean()
                 for Metric in ['Selectivity','ConvertedStability']}
              for k,v in df[['PromoterElements', 'Selectivity','ConvertedStability']].dropna(subset=['PromoterElements']
                      ).assign(PromoterElements=df['PromoterElements'].str.split(', ')
                               ).explode('PromoterElements').dropna(subset=['PromoterElements']
                                    ).assign(PromoterElements=lambda df: df['PromoterElements'].apply(extract_element
                                      )).dropna(subset=['PromoterElements']).reset_index(drop=True
                                         ).replace([np.inf, -np.inf], np.nan).dropna(subset=['PromoterElements']
                                                                                     ).fillna(0).groupby('PromoterElements')}).T.sort_values(['Selectivity','ConvertedStability'],ascending=False).to_csv('PromoterElementsTop5.csv')
pd.DataFrame({k:{Metric:v.sort_values(Metric,ascending=False).iloc[:5][Metric].mean()
                 for Metric in ['Selectivity','ConvertedStability']}
              for k,v in df[['ActiveSpeciesElements', 'Selectivity','ConvertedStability']].dropna(subset=['ActiveSpeciesElements']
                      ).assign(ActiveSpeciesElements=df['ActiveSpeciesElements'].str.split(', ')
                               ).explode('ActiveSpeciesElements').dropna(subset=['ActiveSpeciesElements']
                                    ).assign(ActiveSpeciesElements=lambda df: df['ActiveSpeciesElements'].apply(extract_element
                                      )).dropna(subset=['ActiveSpeciesElements']).reset_index(drop=True
                                         ).replace([np.inf, -np.inf], np.nan).dropna(subset=['ActiveSpeciesElements']
                                                                                     ).fillna(0).groupby('ActiveSpeciesElements')}).T.sort_values(['Selectivity','ConvertedStability'],ascending=False).to_csv('ActiveSpeciesElementsTop5.csv')
pd.DataFrame({k:{Metric:v.sort_values(Metric,ascending=False).iloc[:5][Metric].mean()
                 for Metric in ['Selectivity','ConvertedStability']}
              for k,v in df[['CompositionElements', 'Selectivity','ConvertedStability']].dropna(subset=['CompositionElements']
                      ).assign(CompositionElements=df['CompositionElements'].str.split(', ')
                               ).explode('CompositionElements').dropna(subset=['CompositionElements']
                                    ).assign(CompositionElements=lambda df: df['CompositionElements'].apply(extract_element
                                      )).dropna(subset=['CompositionElements']).reset_index(drop=True
                                         ).replace([np.inf, -np.inf], np.nan).dropna(subset=['CompositionElements']
                                                                                     ).fillna(0).groupby('CompositionElements')}).T.sort_values(['Selectivity','ConvertedStability'],ascending=False).to_csv('CompositionElementsTop5.csv')
