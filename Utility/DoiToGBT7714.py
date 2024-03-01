import re
import requests
from crossref.restful import Works
works = Works()
def extract_doi_from_input(input_str):
    pattern = r'10\.\d{4,9}[/_]+[-._;()/:A-Za-z0-9]+'
    return re.findall(pattern,input_str)
def remove_xml_tags(title):
    return re.sub(r'<[^>]+>', '', title)
def get_metadata_from_doi(doi):
    return works.doi(re.sub(r'_', '/', doi, count=1))
def format_reference(metadata):
    authors = metadata["author"]
    formatted_authors = ", ".join([f"{author.get('given','')} {author.get('family','')}" for author in authors[:3]])
    if len(authors) > 3:
        formatted_authors += ", et al."    
    title = remove_xml_tags(metadata["title"][0]).replace('\n','')
    if metadata["type"] == "journal-article":
        journal = metadata["container-title"][0]
        volume = metadata.get("volume", "")
        issue = metadata.get("issue", "")
        page = metadata.get("page",metadata.get('article-number','')+'\t####PAGE NOT FOUND####')
        if journal=='Nature Communications':
            page=page.strip('\t####PAGE NOT FOUND####')
        if journal=='Angewandte Chemie International Edition' and page=='\t####PAGE NOT FOUND####':
            page=f'e{doi.split("anie.")[-1]}'
        if journal=='Science Advances' and page=='\t####PAGE NOT FOUND####':
            page=f'e{doi.split("sciadv.")[-1]}'
        if journal=='Advanced Science' and page=='\t####PAGE NOT FOUND####':
            page=f'{doi.split("advs.")[-1]}'
        if metadata.get("published-print",''):
            year = metadata["published-print"]["date-parts"][0][0]
        elif  metadata.get("published-online",''):
            year = metadata["published-online"]["date-parts"][0][0]
        elif metadata.get("created",''):
            year = metadata["created"]["date-parts"][0][0]
        return f"{formatted_authors}. {title}[J]. {journal}, {year}, {volume}({issue}): {page}."
    elif metadata["type"] == "book":
        publisher = metadata["publisher"]
        publication_place = metadata.get("published-print", {}).get("date-parts", [])[0][0]
        year = metadata.get("published-print", {}).get("date-parts", [])[0][0] if "published-print" in metadata else metadata["published-online"]["date-parts"][0][0]
        return f"{formatted_authors}. {title}[M]. {publication_place}: {publisher}, {year}."
    return f"{formatted_authors}. {title}."
dois =''''''
DOIList=[]
while True:
    try:
        DOIList.append(input())
    except:
        break
dois='\n'.join(DOIList)
print(len(extract_doi_from_input(dois)))
references = []
for idx, doi in enumerate(extract_doi_from_input(dois), start=1):
    metadata = get_metadata_from_doi(doi)
    if metadata:
        reference = format_reference(metadata).replace('&lt;','<').replace('&gt;','>').replace('&amp;','&').replace('&quot;','"').replace('&apos;',"'")
    else:
        reference=f'{doi}\t###NOT FOUND###'
    references.append(f"[{idx}] {reference}")
    if '#' in reference:
        print('#'*49)
    print(f"[{idx}] {reference}")
