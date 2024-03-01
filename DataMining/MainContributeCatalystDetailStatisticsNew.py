from elsapy.elsclient import ElsClient
from elsapy.elsdoc import FullDoc
from crossref.restful import Works
works = Works()
import xml.etree.ElementTree as ET
from io import StringIO
import pandas as pd
import numpy as np
import tqdm
tqdm.tqdm.pandas()
import os
import re
ElsevierClient = ElsClient(os.getenv('ElsClientKey', ''))
def truncate_at_first_digit(text):
    match = re.search(r'\d', text)
    if match:
        return text[:match.start()]
    else:
        return text
def get_text(element, default='N/A'):
    return (element.text if element.text else '') if element is not None else default
def GetResult(File, xml_content):
    tree = ET.parse(StringIO(xml_content))
    root = tree.getroot()
    if root.findall('.//Relevance') and ('yes' in root.find('.//Relevance').text.lower()):
        dataframes = {}
        global catalyst
        catalyst = root.find('.//Catalyst')
        if catalyst is not None:
            for child in catalyst:
                if child.tag not in dataframes and child.tag != "AlloyDetails":
                    dataframes[child.tag] = []
                if child.tag in ["CompositionElements", "ActiveSpeciesElements", "PromoterElements"]:
                    elements = [get_text(elem) for elem in child.findall("Element")]
                    dataframes[child.tag].append(", ".join(elements))
                elif child.tag == "ConversionTypes":
                    types = {get_text(t):get_text(v) for t,v in zip(child.findall("Type"),child.findall("Value"))}
                    dataframes[child.tag].append(str(types))
                elif child.tag == "DeactivationRates":
                    rates = [get_text(rate) for rate in child.findall("Rate")]
                    dataframes[child.tag].append(", ".join(rates))
                elif child.tag == "FeedCompositionAndRatios":
                    ratios = [get_text(ratio) for ratio in child.findall("Ratio")]
                    dataframes[child.tag].append(", ".join(ratios))
                elif child.tag == "FeedGasComposition":
                    ratios = [get_text(ratio) for ratio in child.findall("Component")]
                    dataframes[child.tag].append(", ".join(ratios))
                elif child.tag == "AlloyDetails":
                    structure_type = get_text(child.find("StructureType"))
                    preparation_method = get_text(child.find("PreparationMethod"))
                    dataframes["StructureType"] = [structure_type]
                    dataframes["PreparationMethod"] = [preparation_method]
                else:
                    dataframes[child.tag].append(get_text(child))
        performance_enhancements = root.findall('.//PerformanceEnhancement')
        details=dict()
        for enhancement in performance_enhancements:
            for detail in enhancement.findall('.//EnhancementDetails'):
                details.update({get_text(detail.find('Aspect')):get_text(detail.find('ImprovedBy'))})
        if 'Enhancement' not in dataframes:
            dataframes['Enhancement'] = []
        dataframes['Enhancement'].append(str(details))
        try:
            return pd.DataFrame({key: [(item.replace('Â°C','℃').replace('−','-') if item else item) for item in value ] for key, value in dataframes.items() if value != ['N/A']},index=[File])
        except:
            return pd.DataFrame({key: ['-'.join([(item.replace('Â°C','℃').replace('−','-') if item else item) for item in value ])] for key, value in dataframes.items() if value != ['N/A']},index=[File])
def GetYearFromDOI(DOI):
    metadata=works.doi(DOI)
    if metadata:
        if metadata.get("published-print",''):
            year = metadata["published-print"]["date-parts"][0][0]
        elif  metadata.get("published-online",''):
            year = metadata["published-online"]["date-parts"][0][0]
        elif metadata.get("created",''):
            year = metadata["created"]["date-parts"][0][0]
        return year
All=[]
for File in tqdm.tqdm([txt for txt in os.listdir('MainContributionCatalystDetails') if txt.startswith('10.') and txt.endswith('.txt')]):
    content='<?xml version="1.0" encoding="UTF-8"?>\n<output>\n'+open(os.path.join('MainContributionCatalystDetails',File),'r',encoding='UTF8').read().strip().split('<output>')[-1]
    content=content.split('</output>')[0]+'\n</output>'
    if File.startswith('10._pii_S'):
        doc = FullDoc(sd_pii=File.replace('10._pii_','').replace('.txt',''))
        doc.read(ElsevierClient)
        DOI=doc.int_id
    else:
        DOI=File.replace('.txt','').replace('_','/',1).replace('_Review','')
    All.append(GetResult(DOI,content))
df=pd.concat(All)
df['DOI']=df.index
df['Year']=df.DOI.progress_apply(GetYearFromDOI)
df.to_csv('AllResult.csv',encoding='UTF-8-sig',index=False)
print(df)
ElementTable={'Nu': 0, 'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90, 'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100, 'Md': 101, 'No': 102, 'Lr': 103, 'Rf': 104, 'Db': 105, 'Sg': 106, 'Bh': 107, 'Hs': 108, 'Mt': 109, 'Ds': 110, 'Rg': 111, 'Cn': 112, 'Nh': 113, 'Fl': 114, 'Mc': 115, 'Lv': 116, 'Ts': 117, 'Og': 118}
for ElementItem in ['CompositionElements','PromoterElements','ActiveSpeciesElements']:
    Elements=pd.DataFrame([[truncate_at_first_digit(j.strip()),y] for i,y in df[[ElementItem,'Year']].to_numpy() if i==i for j in i.replace('/',',').split(',') if j.strip() in ElementTable.keys()],columns=['Element','Year']).dropna()
    Elements.to_csv(f'{ElementItem}.csv',encoding='UTF-8-sig',index=False)
    ElementCount=Elements.groupby(['Year', 'Element']).size().reset_index(name='Frequency').pivot(index='Year', columns='Element', values='Frequency').fillna(0)
    ElementCount.to_csv(f'{ElementItem}Count.csv',encoding='UTF-8-sig')
    print(ElementCount,'\n')
def flexible_map_type(value):
    type_keywords_mapping = {
        'Metal': ['metal'],
        'Metal Oxide': ['metal oxide'],
        'Single Atom': ['single atom'],
        'Alloy': ['alloy']
    }
    lower_value = value.lower()
    for main_category, keywords in type_keywords_mapping.items():
        if any(keyword in lower_value for keyword in keywords):
            if main_category == 'Metal' and 'oxide' in lower_value:
                continue
            return main_category
    return "Others"
Type=pd.concat([df['Type'].astype(str).apply(flexible_map_type),df.Year],axis=1).dropna()
Type.to_csv('Type.csv',encoding='UTF-8-sig',index=False)
TypeCount=Type.groupby(['Year', 'Type']).size().reset_index(name='Frequency').pivot(index='Year', columns='Type', values='Frequency').fillna(0)
TypeCount.to_csv('TypeCount.csv',encoding='UTF-8-sig')
print(TypeCount,'\n')
def flexible_map_support_material_updated(value):
    support_material_keywords_updated = {
        'Silica Oxide': ['silica oxide', 'silica'],
        'Aluminum Oxide': ['aluminum oxide', 'alumina', 'al2o3'],
        'Zeolites': ['zeolite', 'zsm-5', 'silicalite', 'chabazite', 'beta zeolite'],
        'Carbides': ['carbide', 'silicon carbide'],
        'Oxides': ['oxide', 'in2o3', 'mgal2o4'],
        'MOFs': ['metal-organic framework', 'mof', 'uio-66'],
        'Carbon-based': ['carbon', 'graphene', 'nanodiamond'],
        'Boron-based': ['boron nitride', 'hexagonal boron nitride', 'bn'],
    }
    lower_value = value.lower()
    for main_category, keywords in support_material_keywords_updated.items():
        if any(keyword in lower_value for keyword in keywords):
            return main_category
    return "Others"
SupportMaterial= pd.concat([df['SupportMaterial'].astype(str).apply(flexible_map_support_material_updated),df.Year],axis=1)
SupportMaterial=SupportMaterial[~df['SupportMaterial'].astype(str).str.lower().isin(['none', 'none mentioned', 'nan'])].dropna()
SupportMaterial.to_csv('SupportMaterial.csv',encoding='UTF-8-sig',index=False)
SupportMaterialCount=SupportMaterial.groupby(['Year', 'SupportMaterial']).size().reset_index(name='Frequency').pivot(index='Year', columns='SupportMaterial', values='Frequency').fillna(0)
SupportMaterialCount.to_csv('SupportMaterialCount.csv',encoding='UTF-8-sig')
print(SupportMaterialCount,'\n')
def process_reaction_temperature(temp_str):
    temp_str=temp_str.replace('50-600','500-600')
    if any(celsius_indicator in temp_str for celsius_indicator in ["℃", "°", "ï¿½C"]):
        matches = re.findall(r"(\d+\.*\d*)", temp_str)
        kelvin_values = [float(match) + 273.15 for match in matches]
        kelvin_str =np.mean(kelvin_values)
        return kelvin_str
    temp_str=re.sub(r"[^\d\.]", "", temp_str)
    return float(temp_str) if temp_str else None
ReactionTemperature=pd.concat([df['ReactionTemperature'].astype(str).apply(process_reaction_temperature),df.Year],axis=1).dropna()
ReactionTemperature.to_csv('ReactionTemperature.csv',encoding='UTF-8-sig',index=False)
ReactionTemperatureBins = list(range(0, int(np.percentile(ReactionTemperature.ReactionTemperature,90)+1), int(np.percentile(ReactionTemperature.ReactionTemperature,90)//10))) + [float('inf')]
ReactionTemperature['Bin']=pd.cut(ReactionTemperature['ReactionTemperature'], ReactionTemperatureBins)
ReactionTemperatureCount=ReactionTemperature.groupby(['Year', 'Bin']).size().reset_index(name='Frequency').pivot(index='Year', columns='Bin', values='Frequency').fillna(0)
ReactionTemperatureCount.to_csv('ReactionTemperatureCount.csv',encoding='UTF-8-sig')
print(ReactionTemperatureCount,'\n')
def classify_preparation_method(method):
    if pd.isna(method):
        return method
    method_lower = str(method).lower()
    if any(keyword in method_lower for keyword in ["wet chemical", "hydroxide", "chemical vapor deposition", "chemical"]):
        return "Chemical Methods"
    elif any(keyword in method_lower for keyword in ["ultrasonication", "mechanical", "grinding", "milling"]):
        return "Physical Methods"
    elif any(keyword in method_lower for keyword in ["surface", "support", "deposition", "metal-support"]):
        return "Surface & Support Methods"
    elif any(keyword in method_lower for keyword in ["heat", "melting", "reduction", "calcination"]):
        return "Heat Treatment"
    elif any(keyword in method_lower for keyword in ["impregnation"]):
        return "Impregnation Methods"
    elif any(keyword in method_lower for keyword in ["sol-gel", "gel", "impregnation", "one-pot", "co-precipitation"]):
        return "Other Solution-Based Methods"
    elif "hydrothermal" in method_lower or "solvothermal" in method_lower:
        return "Hydrothermal & Solvothermal Methods"
    elif "zeolite" in method_lower:
        return "Zeolite-Related Methods"
    elif "encapsulation" in method_lower:
        return "Encapsulation"
    elif "in situ" in method_lower:
        return "In Situ Synthesis"
    else:
        return "Others"
PreparationMethod= pd.concat([df['PreparationMethod'].apply(classify_preparation_method),df.Year],axis=1).dropna()
PreparationMethod.to_csv('PreparationMethod.csv',encoding='UTF-8-sig',index=False)
PreparationMethodCount=PreparationMethod.groupby(['Year', 'PreparationMethod']).size().reset_index(name='Frequency').pivot(index='Year', columns='PreparationMethod', values='Frequency').fillna(0)
PreparationMethodCount.to_csv('PreparationMethodCount.csv',encoding='UTF-8-sig')
print(PreparationMethodCount,'\n')
def get_percentage_from_multi_ratio_v3(ratio_str, target_list=['C3H6', 'Propene', 'propene']):
    Ratio=re.search(r'(\d+(\.\d*)?)(:\d+(\.\d*)?)+', ratio_str)
    if not Ratio:
        return None
    values = [float(val) for val in Ratio.group().split(':')]
    total = sum(values)
    compounds = re.findall(r'[\w\d]+', ''.join(ratio_str.split(Ratio.group())))
    target_index = None
    for target in target_list:
        if target in compounds:
            target_index = compounds.index(target)
            break
    if target_index is not None:
        return str(values[target_index] / total * 100)
    return None
def process_selectivity(selectivity):
    if pd.isna(selectivity):
        return selectivity
    selectivity = selectivity.lower().replace("greater than", ">").replace("less than", "<")
    selectivity = selectivity.lower().replace("above", ">").replace("below", "<")
    selectivity = selectivity.lower().replace("about", "~")
    fraction_like_match = re.search(r'\s*0\.\d+(?![\s\S]*%)', selectivity)
    if fraction_like_match:
        value = float(fraction_like_match.group()) * 100
        selectivity = f"{value:.2f}%"
    multi_percentage_values = re.findall(r'(\d+\.\d*|\d+)%', selectivity)
    if len(multi_percentage_values) > 1:
        for value in multi_percentage_values:
            match = re.search(r'{}%\s*for\s*([\w\d]+)'.format(value), selectivity)
            if match:
                compound = match.group(1)
                if 'C3H6' in compound or 'Propene' in compound or 'propene' in compound:
                    return value
    general_percent_match = re.search(r'([^\d-]*?)(\d+\.\d*|\d+)\s*\D*%', selectivity)
    if general_percent_match:
        modifier = general_percent_match.group(1).strip()
        value = general_percent_match.group(2)
        return float(f"{value}")
    multi_ratio_match = re.search(r'(\d+\.\d*|\d+)(:\d+\.\d*|\d+)+', selectivity)
    if multi_ratio_match:
        return get_percentage_from_multi_ratio_v3(selectivity)
    return None
Selectivity= pd.concat([df['Selectivity'].apply(process_selectivity),df.Year],axis=1).dropna()
Selectivity.to_csv('Selectivity.csv',encoding='UTF-8-sig',index=False)
SelectivityBins = list(range(0, int(np.percentile(Selectivity.Selectivity,90)+1), int(np.percentile(Selectivity.Selectivity,90)//10))) + [float('inf')]
Selectivity['Bin']=pd.cut(Selectivity['Selectivity'], SelectivityBins)
SelectivityCount=Selectivity.groupby(['Year', 'Bin']).size().reset_index(name='Frequency').pivot(index='Year', columns='Bin', values='Frequency').fillna(0)
SelectivityCount.to_csv('SelectivityCount.csv',encoding='UTF-8-sig')
print(SelectivityCount,'\n')
def refined_classify_structure_type(structure):
    if not isinstance(structure,str):
        return
    if "intermetallic" in structure.lower():
        return "Intermetallic Compounds"
    elif "nanoparticulate" in structure.lower():
        return "Nanoparticulate Alloys"
    elif "single-atom" in structure.lower():
        return "Single-atom Alloys"
    elif any(term in structure.lower() for term in ["core-shell", "disordered", "liquid metal", "surface skin", "solid solution"]):
        return "Miscellaneous Alloys"
    else:
        return "Others"
StructureType= pd.concat([df['StructureType'].apply(refined_classify_structure_type),df.Year],axis=1).dropna()
StructureType.to_csv('StructureType.csv',encoding='UTF-8-sig',index=False)
StructureTypeCount=StructureType.groupby(['Year', 'StructureType']).size().reset_index(name='Frequency').pivot(index='Year', columns='StructureType', values='Frequency').fillna(0)
StructureTypeCount.to_csv('StructureTypeCount.csv',encoding='UTF-8-sig')
print(StructureTypeCount,'\n')
def process_conversion_rate(rate):
    """Extract the percentage value from the ConversionRate column."""
    if type(rate)==str:
        rate={k:v for k,v in eval(rate.replace('}-{',',')).items() if 'conversion' in k}
        if len(rate)>1:
            rate={k:v for k,v in rate.items() if 'propane' in k}
        if len(rate)==1:
            match = re.search(r'(\d+\.\d*|\d+)(\D*)%', str(rate))
            if match:
                return float(match.group(1))
        elif rate:
            raise RuntimeError(rate)
        else:
            return None            
    return None
df['ConversionRate']=df['ConversionTypes'].apply(process_conversion_rate)
ConversionRate = pd.concat([df['ConversionRate'],df.Year],axis=1).dropna()
ConversionRate.to_csv('ConversionRate.csv',encoding='UTF-8-sig',index=False)
ConversionRateBins = list(range(0, int(np.percentile(ConversionRate.ConversionRate,90)+1), int(np.percentile(ConversionRate.ConversionRate,90)//10))) + [float('inf')]
ConversionRate['Bin']=pd.cut(ConversionRate['ConversionRate'], ConversionRateBins)
ConversionRateCount=ConversionRate.groupby(['Year', 'Bin']).size().reset_index(name='Frequency').pivot(index='Year', columns='Bin', values='Frequency').fillna(0)
ConversionRateCount.to_csv('ConversionRateCount.csv',encoding='UTF-8-sig')
print(ConversionRateCount,'\n')
def process_PropyleneYield(rate):
    """Extract the percentage value from the ConversionRate column."""
    match = re.search(r'(\d+\.\d*|\d+)(\D*)%', str(rate))
    if match:
        return float(match.group(1))
    return None
PropyleneYield = pd.concat([df['PropyleneYield'].apply(process_PropyleneYield),df.Year],axis=1).dropna()
PropyleneYield.to_csv('PropyleneYield.csv',encoding='UTF-8-sig',index=False)
PropyleneYieldBins = list(range(0, int(np.percentile(PropyleneYield.PropyleneYield,90)+1), int(np.percentile(PropyleneYield.PropyleneYield,90)//10))) + [float('inf')]
PropyleneYield['Bin']=pd.cut(PropyleneYield['PropyleneYield'], PropyleneYieldBins)
PropyleneYieldCount=PropyleneYield.groupby(['Year', 'Bin']).size().reset_index(name='Frequency').pivot(index='Year', columns='Bin', values='Frequency').fillna(0)
PropyleneYieldCount.to_csv('PropyleneYieldCount.csv',encoding='UTF-8-sig')
print(PropyleneYieldCount,'\n')
def convert_to_kpa(pressure_str):
    """Convert various pressure units to kPa."""
    if type(pressure_str)!=str:
        return
    match_atm = re.search(r'(\d+\.\d*|\d+)\s*atm', pressure_str)
    if match_atm:
        value_atm = float(match_atm.group(1))
        return (value_atm * 101.325)
    match_bar = re.search(r'(\d+\.\d*|\d+)\s*bar', pressure_str)
    if match_bar:
        value_bar = float(match_bar.group(1))
        return (value_bar * 100)
    match_mpa = re.search(r'(\d+\.\d*|\d+)\s*MPa', pressure_str)
    if match_mpa:
        value_mpa = float(match_mpa.group(1))
        return (value_mpa * 1000)
    match_mbar = re.search(r'(\d+\.\d*|\d+)\s*mbar', pressure_str)
    if match_mbar:
        value_mbar = float(match_mbar.group(1))
        return (value_mbar * 0.1)
    match_kpa = re.search(r'(\d+\.\d*|\d+)\s*kPa', pressure_str)
    if match_kpa:
        return float(match_kpa.group(1))
    return None
PropanePartialPressure = pd.concat([df['PropanePartialPressure'].apply(convert_to_kpa),df.Year],axis=1).dropna()
PropanePartialPressure.to_csv('PropanePartialPressure.csv',encoding='UTF-8-sig',index=False)
PropanePartialPressureBins = list(range(0, int(np.percentile(PropanePartialPressure.PropanePartialPressure,90)+1), int(np.percentile(PropanePartialPressure.PropanePartialPressure,90)//10))) + [float('inf')]
PropanePartialPressure['Bin']=pd.cut(PropanePartialPressure['PropanePartialPressure'], PropanePartialPressureBins)
PropanePartialPressureCount=PropanePartialPressure.groupby(['Year', 'Bin']).size().reset_index(name='Frequency').pivot(index='Year', columns='Bin', values='Frequency').fillna(0)
PropanePartialPressureCount.to_csv('PropanePartialPressureCount.csv',encoding='UTF-8-sig')
print(PropanePartialPressureCount,'\n')
def convert_to_ml_per_min(flow_rate_str):
    """Convert various flow rate units to ml/min."""
    if flow_rate_str:
        flow_rate_str=flow_rate_str.replace(',','')
    match_ml_per_min = re.search(r'((\d+\s*)+\.\d*|(\d+\s*)+)\s*(mL/min|mL min-1|mL min^-1|mL·min–1|sccm|cm3/min|cm3 min-1|cm3 min^-1|cm3·min–1|cc/min|cc min-1|cc min^-1|cc·min–1)', flow_rate_str, re.IGNORECASE)
    if match_ml_per_min:
        return float(match_ml_per_min.group(1).replace(' ',''))
    match_ml_per_hr = re.search(r'((\d+\s*)+\.\d*|(\d+\s*)+)\s*(mL/h|mL h-1|mL h^-1|mL·h–1|cm3/h|cm3 h-1|cm3 h^-1|cm3·h–1|cc/h|cc h-1|cc h^-1|cc·h–1)', flow_rate_str, re.IGNORECASE)
    if match_ml_per_hr:
        value_ml_per_hr = float(match_ml_per_hr.group(1).replace(' ',''))
        return (value_ml_per_hr / 60)
    match_ml_per_sec = re.search(r'((\d+\s*)+\.\d*|(\d+\s*)+)\s*(mL/s|mL s-1|mL s^-1|mL·s–1|cm3/s|cm3 s-1|cm3 s^-1|cm3·s–1|cc/s|cc s-1|cc s^-1|cc·s–1)', flow_rate_str, re.IGNORECASE)
    if match_ml_per_sec:
        value_ml_per_sec = float(match_ml_per_sec.group(1).replace(' ',''))
        return (value_ml_per_sec * 60)
    match_l_per_hr = re.search(r'((\d+\s*)+\.\d*|(\d+\s*)+)\s*(L/h|L h-1|L h^-1|L·h–1)', flow_rate_str, re.IGNORECASE)
    if match_l_per_hr:
        value_l_per_hr = float(match_l_per_hr.group(1).replace(' ',''))
        return (value_l_per_hr * 1000 / 60)
    return None
InletFlowRate = pd.concat([df['InletFlowRate'].apply(lambda x: convert_to_ml_per_min(x) if isinstance(x, str) else x),df.Year],axis=1).dropna()
InletFlowRate.to_csv('InletFlowRate.csv',encoding='UTF-8-sig',index=False)
InletFlowRateBins = list(range(0, int(np.percentile(InletFlowRate.InletFlowRate,90)+1), int(np.percentile(InletFlowRate.InletFlowRate,90)//10))) + [float('inf')]
InletFlowRate['Bin']=pd.cut(InletFlowRate['InletFlowRate'], InletFlowRateBins)
InletFlowRateCount=InletFlowRate.groupby(['Year', 'Bin']).size().reset_index(name='Frequency').pivot(index='Year', columns='Bin', values='Frequency').fillna(0)
InletFlowRateCount.to_csv('InletFlowRateCount.csv',encoding='UTF-8-sig')
print(InletFlowRate,'\n')
def process_ConvertedStability(rate):
    """Extract the percentage value from the ConvertedStability column."""
    match = re.search(r'(\d+\.\d*|\d+)(\D*)(\s*)(h-1|h\^-1)', str(rate))
    if match:
        return float(match.group(1))
    return None
ConvertedStability=pd.concat([df['ConvertedStability'].apply(process_ConvertedStability),df.Year],axis=1).dropna()
ConvertedStability.to_csv('ConvertedStability.csv',encoding='UTF-8-sig',index=False)
ConvertedStabilityBins = list(range(0, int(np.percentile(ConvertedStability.ConvertedStability,90)+1), int(np.percentile(ConvertedStability.ConvertedStability,90)//10))) + [float('inf')]
ConvertedStability['Bin']=pd.cut(ConvertedStability['ConvertedStability'], ConvertedStabilityBins)
ConvertedStabilityCount=ConvertedStability.groupby(['Year', 'Bin']).size().reset_index(name='Frequency').pivot(index='Year', columns='Bin', values='Frequency').fillna(0)
ConvertedStabilityCount.to_csv('ConvertedStabilityCount.csv',encoding='UTF-8-sig')
print(ConvertedStabilityCount,'\n')
TypeIdentify=pd.concat([df['TypeIdentify'].apply(lambda x:('ODH' if 'ODH' in x else 'PDH') if x==x else None),df.Year],axis=1).dropna()
TypeIdentify.to_csv('TypeIdentify.csv',encoding='UTF-8-sig',index=False)
TypeIdentifyCount=TypeIdentify.groupby(['Year', 'TypeIdentify']).size().reset_index(name='Frequency').pivot(index='Year', columns='TypeIdentify', values='Frequency').fillna(0)
TypeIdentifyCount.to_csv('TypeIdentifyCount.csv',encoding='UTF-8-sig')
print(TypeIdentifyCount,'\n')
ContainsOxidizingAgent=pd.concat([df['ContainsOxidizingAgent'].apply(lambda x:(True if 'yes' in x.lower() else False) if x==x else None),df.Year],axis=1).dropna()
ContainsOxidizingAgent.to_csv('ContainsOxidizingAgent.csv',encoding='UTF-8-sig',index=False)
ContainsOxidizingAgentCount=ContainsOxidizingAgent.groupby(['Year', 'ContainsOxidizingAgent']).size().reset_index(name='Frequency').pivot(index='Year', columns='ContainsOxidizingAgent', values='Frequency').fillna(0)
ContainsOxidizingAgentCount.to_csv('ContainsOxidizingAgentCount.csv',encoding='UTF-8-sig')
print(ContainsOxidizingAgentCount,'\n')
def categorize_aspects_general(x):
    categories = {
        'Selectivity': ['selectivity'],
        'Conversion': ['conversion'],
        'Stability': ['stability','stable']
    }
    return  next((category for category, keywords in categories.items() if any(keyword in x.lower() for keyword in keywords)),'Other')
def categorize_improvement_by(x):
    categories = {
        'Preparation method': ['doping', 'modification', 'preparation', 'synthesis', 'fabrication', 'addition', 'reduction', 'treatment', 'anchoring', 'dispersion', 'loading', 'dealumination', 'dopants'],
        'Structural composition': ['size', 'content', 'type', 'state', 'dispersion', 'structure', 'species', 'presence', 'composition', 'material', 'promoter', 'surface', 'lattice', 'site','alloying'],
        'Process conditions': ['temperature', 'pressure', 'concentration', 'condition', 'heat', 'regeneration', 'cycle', 'pathway', 'mechanism', 'kinetics', 'feed gas', 'shift', 'inhibition','feed'],
        'Reactor design': ['design', 'configuration', 'reactor']
    }
    return  next((category for category, keywords in categories.items() if any(keyword in x.lower() for keyword in keywords)),'Other')
Enhancement=df[['Enhancement',  'DOI', 'Year']].dropna().assign(Enhancement=df['Enhancement'].apply(lambda x: [{k: v} for k, v in eval(x).items()])).explode('Enhancement').reset_index(drop=True)
Enhancement['EnhancementAspect'] = Enhancement['Enhancement'].apply(lambda x: list(x.keys())[0]).map(categorize_aspects_general)
Enhancement['EnhancementImprovedBy'] = Enhancement['Enhancement'].apply(lambda x: list(x.values())[0]).map(categorize_improvement_by)
Enhancement.to_csv('Enhancement.csv',encoding='UTF-8-sig',index=False)
EnhancementAspectCount=Enhancement.groupby(['Year', 'EnhancementAspect']).size().reset_index(name='Frequency').pivot(index='Year', columns='EnhancementAspect', values='Frequency').fillna(0)
EnhancementAspectCount.to_csv('EnhancementAspectCount.csv',encoding='UTF-8-sig')
EnhancementImprovedByCount=Enhancement.groupby(['Year', 'EnhancementImprovedBy']).size().reset_index(name='Frequency').pivot(index='Year', columns='EnhancementImprovedBy', values='Frequency').fillna(0)
EnhancementImprovedByCount.to_csv('EnhancementImprovedByCount.csv',encoding='UTF-8-sig')
frequency = {}
for column in df.columns:
    if column not in ['Type', 'CompositionElements', 'StructureType', 'PreparationMethod', 'ActiveSpeciesElements',
                      'SupportMaterial', 'ConversionRate', 'Selectivity', 'ReactionTemperature', 'InletFlowRate', 'PromoterElements',
                      'PropyleneYield', 'PropanePartialPressure','StabilityOriginal','ConversionTypes','ConvertedStability',
                      'TypeIdentify','ContainsOxidizingAgent','Enhancement','DOI']:
        frequency[column] = df[column].value_counts()
for column, freq in frequency.items():
    print(f"\nColumn: {column}")
    print("-----------------------")
    print(freq)
