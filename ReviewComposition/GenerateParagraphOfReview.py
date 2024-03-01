from threading import Thread, Semaphore
from queue import Queue, Empty
import xml.etree.ElementTree as ET
import time
import os
import re
import sys
import tqdm
import json
import shutil
import requests
import func_timeout
def replace_with_html_entities(text):
    entities = {
        '[':'\[',
        ']':'\]',
        '_':'\_',
        '&': '&amp;',
        '©': '&copy;',
        '®': '&reg;',
        '™': '&trade;',
        '€': '&euro;',
        '£': '&pound;',
        '¥': '&yen;',
        '¢': '&cent;',
        '—': '&mdash;',
        '–': '&ndash;',
        '•': '&bull;',
        '…': '&hellip;'
    }
    for char, entity in entities.items():
        text = text.replace(char, entity)
    return text
def wrap_specific_tags_with_cdata(tag_name, content):
    tag_pattern = f'<{tag_name}>(.*?)</{tag_name}>'
    replacement = f'<{tag_name}><![CDATA[\\1]]></{tag_name}>'
    return re.sub(tag_pattern, replacement, content, flags=re.DOTALL)
def GetResponseConcurrent(prompts,Threads,FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT):
    prompt_queue = Queue()
    for item in prompts:
        prompt_queue.put(item)
    ClaudeAPISemaphore=[]
    OpenAIAPISemaphore=[]
    FunctionClaudeAPI={k:v for k,v in FunctionClaudeAPI.items() if v}
    FunctionOpenAIAPI={k:v for k,v in FunctionOpenAIAPI.items() if v}
    for i in FunctionClaudeAPI:
        ClaudeAPISemaphore.append(Semaphore(value=1))
    for i in FunctionOpenAIAPI:
        OpenAIAPISemaphore.append(Semaphore(value=3))
    progress_bar = tqdm.tqdm(total=len(prompts), position=0, desc='GenerateParagraphOfReview',file=STDOUT)
    def worker():
        while True:
            try:
                i, Time,folder, part, prompt,DOI = prompt_queue.get_nowait()
            except Empty:
                break
            if os.path.exists(os.path.join(f'Paragraph{"All" if "All" in part else ""}', f'{part}_{Time}.txt')):
                progress_bar.update(1)
                continue
            TRY = 0
            while True:
                semaphore_acquired = None
                response=None
                try:
                    for semaphore,GetResponseFunction in zip(ClaudeAPISemaphore,FunctionClaudeAPI.values()):
                        if semaphore.acquire(blocking=False):
                            semaphore_acquired = semaphore
                            response = GetResponseFunction(prompt)
                            semaphore.release()
                            break
                    if not response:
                        for semaphore,GetResponseFunction in zip(OpenAIAPISemaphore,FunctionOpenAIAPI.values()):
                            if semaphore.acquire(blocking=False):
                                semaphore_acquired = semaphore
                                response = GetResponseFunction(prompt)
                                semaphore.release()
                                break
                    if not response:
                        open('Waitlog', 'a').write('\t'.join([str(i), folder, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()), 'waiting\n']))
                        time.sleep(0.5)
                        continue
                    if not bool(re.search(r'\[\s*10\.\d+[/_]+[-._;()/:A-Za-z0-9]+', response)):
                        TRY+=1
                        with open(os.path.join(f'Paragraph{"All" if "All" in part else ""}', f'{part}_{Time}_{TRY}.txt'), 'w', encoding='UTF8') as file:
                            file.write(response + '\n')
                        continue
                    content='<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n<English>\n'+response.strip().split('<English>')[-1]
                    content=content.split('</References>')[0]+'\n</References>\n</Response>'
                    tags_to_wrap = ["English", "Chinese","References"]
                    for tag in tags_to_wrap:
                      content = wrap_specific_tags_with_cdata(tag, content.strip())
                    WrongDOI=[]
                    try:
                      root = ET.fromstring(content)
                      DOIFromResponse=[doi.strip() for doi in root.findall('References')[0].text.split('\n') if doi.strip()]
                      WrongDOI=[doi for doi in DOIFromResponse if doi not in DOI]
                      if WrongDOI:
                        raise RuntimeError('WrongDOI')
                    except Exception as e:
                      TRY+=1
                      with open(os.path.join(f'Paragraph{"All" if "All" in part else ""}', f'{part}_{Time}_{TRY}.txt'), 'w', encoding='UTF8') as file:
                          file.write(response + '\nWrongDOI\n')
                      continue
                    with open(os.path.join(f'Paragraph{"All" if "All" in part else ""}', f'{part}_{Time}.txt'), 'w', encoding='UTF8') as file:
                        file.write(response + '\n')
                    break
                except (Exception,func_timeout.exceptions.FunctionTimedOut) as e:
                    pattern = r"Function\s+(\S+).*?timed out after\s+(\d+\.\d+)\s+seconds."
                    replacement = r"\1 timed out after \2 s"
                    if semaphore_acquired:
                        semaphore_acquired.release()
                    open('Exceptionlog', 'a').write('\t'.join([str(i), folder, part, time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime()),
                                                               re.sub(pattern, replacement, str(e), flags=re.DOTALL),'\n']))
                    continue
            progress_bar.update(1)
    threads = [Thread(target=worker) for _ in range(Threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    progress_bar.close()
def Main(Folder,TOPIC,Threads,FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT,REPEAT=9):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    ParagraphQuestionsForReview=[i.strip() for i in open('../ParagraphQuestionsForReview.txt','r',encoding='UTF8').readlines() if i.strip()]
    QuestionsForReview=[i.strip() for i in open('../QuestionsForReview.txt','r',encoding='UTF8').readlines() if i.strip()]
    NumberOfParts=len(QuestionsForReview)
    HEAD="""Based on the in-depth details extracted from the file related to '"""
    MIDDLE0=f"""', construct an analytical and comprehensive review section on {TOPIC}, emphasizing '"""
    MIDDLE1="""'.
    While developing the content, adhere to the following protocols:
    1. **Accurate Citations**: Reference specific content from the file by embedding the actual DOI numbers furnished, without any alterations. Utilize the format '[Placeholder_Of_DOI]' right after the sentence where the reference is applied. 
    2. **Strict Adherence**: Stick to the particulars and DOI details from the file; avoid integrating external or speculative data.
    3. **Scientific Language**: Uphold a technical and scholarly diction akin to chemical engineering literature.
    4. **Format & Translation**: After creating the main review content, append an 'integrative understanding and prospective outlook' section within the same <English></English> and <Chinese></Chinese> XML tags, demarcated with '※※※'. This segment should transcend a mere summation and foster a forward-thinking discussion, potentially elucidating future directions and broader horizons grounded in the file's content. 
    The content structure should resemble:
    <example>
            <English> 
                    Detailed analysis established from the study of reference [Placeholder_Of_DOI1]. Synthesized comprehension stemming from references [Placeholder_Of_DOI2] and [Placeholder_Of_DOI3]. 
                    ※※※
                    Integrative understanding and prospective outlook: Taking into consideration the advancements and findings discussed in the file, there lies an opportunity to explore emerging fields and innovative methodologies. Future research endeavors might focus on ...
            </English>
            <Chinese> 
                    基于[Placeholder_Of_DOI1]参考文献的深度分析。从[Placeholder_Of_DOI2]和[Placeholder_Of_DOI3]的参考文献中获得的综合理解。
                    ※※※
                    综合理解与未来展望: 考虑到文件中讨论的先进成果和发现，我们有机会探索新兴领域和创新方法。未来的研究努力可能会集中在...
            </Chinese>
            <References> 
                    Placeholder_Of_DOI1
                    Placeholder_Of_DOI2
                    Placeholder_Of_DOI3
            </References>
    </example>
    In the 'integrative understanding and prospective outlook' segment, aspire to:
    - **Offer an expansive perspective**: Illuminate potential pathways and pioneering research opportunities, grounded in the details divulged in the file.
    - **Propose forward-thinking suggestions**: Advocate for innovative angles and burgeoning domains that might take center stage in future explorations, while rooted in the file's details.
    Finally, compile all the cited DOIs in the 'References' compartment, adhering to the <References></References> XML tag, using the exact DOIs designated in the file.
    <file-attachment-contents filename="""
    END="""
    </file-attachment-contents>
    """
    prompts = []
    os.makedirs('Paragraph',exist_ok=True)
    for Time in range(0,REPEAT):
        for i in range(NumberOfParts):
            if os.path.exists(f'{i+1}') :
                document = open(f'{i+1}/EnglishWithQuotes.txt', 'r', encoding='UTF8').read().strip()[:-1]
                DOI=[j['Doi'] for j in json.loads('['+document+']')]
                prompt = replace_with_html_entities(HEAD + QuestionsForReview[i] + MIDDLE0 + ParagraphQuestionsForReview[i] + MIDDLE1 + f'"Paragraph{i+1}Info.txt">\n') + document + END
                open(f'Paragraph{os.sep}Prompt{i+1}.txt', 'w', encoding='UTF8').write(prompt)
                prompts.append((i,Time, f"{i+1}", f"Paragraph{i+1}", prompt,DOI))
    GetResponseConcurrent(prompts,Threads,FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT)
    os.chdir('..')
    sys.stdout = old_stdout
