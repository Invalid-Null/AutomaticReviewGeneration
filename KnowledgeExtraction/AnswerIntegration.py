import re
import os
import sys
import tqdm
from threading import Thread, Semaphore
from queue import Queue, Empty
import time
import json
import shutil
import requests
import func_timeout
import xml.etree.ElementTree as ET
def wrap_specific_tags_with_cdata(tag_name, content):
    tag_pattern = f'<{tag_name}>(.*?)</{tag_name}>'
    replacement = f'<{tag_name}><![CDATA[\\1]]></{tag_name}>'
    return re.sub(tag_pattern, replacement, content, flags=re.DOTALL)
tags_to_wrap = ["Quotes", "English", "Chinese"]
HEAD='''Read the questions and answers provided below. First, critically assess the overall relevance of the answers provided to the set of questions asked.
If, upon your assessment, you find that the answers do not contain information that is relevant to the questions asked, stop your review process immediately and respond with a single sentence: "※※※※※※※The provided answers are not relevant to the questions.※※※※※※※". Do not provide any additional explanation or background information, only this sentence should be given as a response in case of irrelevant answers.
If, however, the answers are relevant to the questions asked, proceed to compile answers for each question according to the instructions below. Ensure to aggregate all the relevant answers from the multiple answer results provided in the document, and organize them sequentially by their order number, compiling the corresponding quotes, English answers, and Chinese answers for each question.
If the provided answers' quotes are not differentiated by question, ensure to break them down and assign the quotes to each respective question, outputting them separately within each question’s section.
To provide a comprehensive review, differentiate the responses into quotes, English answers, and Chinese answers for each question based on the details given in the 'Answer' XML tags. Structure your review using the XML format showcased below if the answers are relevant to the questions asked:
<?xml version="1.0" encoding="UTF-8"?>
<Questions>
   <Question number="1"> 
      <Quotes>
          Quotes for question 1 from all the answer results
      </Quotes>
      <English>
          Aggregated English answer for question 1 from all the answer results
      </English>
      <Chinese>
          所有答案结果中的汇总中文答案 1
      </Chinese>
   </Question>
   <Question number="2">
      <Quotes>
          Quotes for question 2 from all the answer results
      </Quotes>
      <English>
          Aggregated English answer for question 2 from all the answer results
      </English>
      <Chinese>
          所有答案结果中的汇总中文答案 2
      </Chinese>
  </Question>
</Questions>
Here are the question lists, in <questions></questions>XML tags:
<questions>
'''
MIDDLE='''
</questions>
Here are the answer lists, in <Answer></Answer>XML tags:
<Answer>
'''
NotRelevant=[i.replace(' ','') for i in '''Iamunabletoprovide
Iamnotabletoprovide
Icannotprovide
Unfortunatelytheliteratureprovideddoesnot
Unfortunatelytheprovidedliteraturedoesnot
UnfortunatelyIdonothaveenoughrelevantinformation
theliteraturedoesnotcontain
theliteratureprovideddoesnotcontain
itdoesnotseemtocontain
Iamunabletoconclusivelyanswer
Idonotbelievetheycontain
Iwillbeunabletocompile
.However,Icansummarize
Unfortunatelytheprovidedanswersdonotcontain
※※※Theprovidedanswersarenotrelevanttothequestions.※※※'''.split('\n')]
def GetResponse(Folders,AllPrompt,chunk_size,Threads,FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT):
    prompt_queue = Queue()
    ClaudeAPISemaphore=[]
    OpenAIAPISemaphore=[]
    FunctionClaudeAPI={k:v for k,v in FunctionClaudeAPI.items() if v}
    FunctionOpenAIAPI={k:v for k,v in FunctionOpenAIAPI.items() if v}
    for i in FunctionClaudeAPI:
        ClaudeAPISemaphore.append(Semaphore(value=1))
    for i in FunctionOpenAIAPI:
        OpenAIAPISemaphore.append(Semaphore(value=3))
    for FolderIndex,Folder in enumerate(Folders):
        answer_files = [f for f in os.listdir(Folder) if f.startswith("answer.PART") and f.endswith(".txt")]
        parts = sorted(set(f.split("_")[0].split(".")[1] for f in answer_files))
        AnswerDict = {}
        for part in parts:
            part_files = sorted([f for f in answer_files if f.startswith(f"answer.{part}_")], key=lambda x: int(x.split("_")[1].split(".")[0]))
            merged_content = []
            for file_name in part_files:
                with open(os.path.join(Folder, file_name), 'r',encoding='UTF8') as file:
                    merged_content .append(file.read())
            AnswerDict.update({part:merged_content})
        Prompts={part:(HEAD+AllPrompt[int(part.strip('PART'))]+MIDDLE+'\n</Answer>\n<Answer>\n'.join(Answer).replace('Human: ','')+'\n</Answer>\n') for part,Answer in AnswerDict.items()}
        Responses={}
        for part in parts:
            if os.path.exists(f'{Folder}{os.sep}AnswerWithRelevanceCheck.{part}.txt'):
                Responses.update({part:open(f'{Folder}{os.sep}AnswerWithRelevanceCheck.{part}.txt','r',encoding='UTF8').read()})
            else:
                Responses.update({part:''})
        [prompt_queue.put((FolderIndex,Folder,part,Prompt,Responses[part])) for part,Prompt in Prompts.items()]
    progress_bar = tqdm.tqdm(total=prompt_queue.qsize(), position=0, desc='AnswerIntegrationWithRelevanceCheck',file=STDOUT)
    def worker():
        while True:
            try:
                FolderIndex,Folder,part,prompt,Response = prompt_queue.get_nowait()
            except Empty:
                break
            open('log','a').write('\t'.join([str(FolderIndex),Folder,part,time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime()),'start\n']))
            if ((f'<Questions><Questionnumber="{int(part.replace("PART",""))*chunk_size+1}"><Quotes>' not in  Response.replace(' ','').replace('\n',''))
                and ('<Questions><Questionnumber="1"><Quotes>' not in  Response.replace(' ','').replace('\n',''))
               and (('※※※※※※※The provided answers are not relevant to the questions.※※※※' not in Response)
                    and (all([NotRelevantItem not in Response.replace(' ','').replace('\n','') for NotRelevantItem in NotRelevant])))):
                TRY=0
                with open(f'{Folder}{os.sep}PromptAnswerWithRelevanceCheck.{part}.txt', 'w', encoding='UTF-8') as file:
                    file.write(prompt + '\n')
                while True:
                    semaphore_acquired = None
                    try:
                        for semaphore,GetResponseFunction in zip(ClaudeAPISemaphore,FunctionClaudeAPI.values()):
                            if semaphore.acquire(blocking=False):
                                semaphore_acquired = semaphore
                                Response = GetResponseFunction(prompt)
                                semaphore.release()
                                break
                        if not Response:
                            for semaphore,GetResponseFunction in zip(OpenAIAPISemaphore,FunctionOpenAIAPI.values()):
                                if semaphore.acquire(blocking=False):
                                    semaphore_acquired = semaphore
                                    Response = GetResponseFunction(prompt)
                                    semaphore.release()
                                    break
                        if not Response:
                            open('Waitlog','a').write('\t'.join([str(FolderIndex),Folder,part,time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime()),'waiting\n']))
                            time.sleep(0.5)
                            continue
                        if ((f'<Questions><Questionnumber="{int(part.replace("PART",""))*chunk_size+1}"><Quotes>' not in  Response.replace(' ','').replace('\n',''))
                            and ('<Questions><Questionnumber="1"><Quotes>' not in  Response.replace(' ','').replace('\n',''))
                               and (('※※※※※※※The provided answers are not relevant to the questions.※※※※' not in Response)
                                    and (all([NotRelevantItem not in Response.replace(' ','').replace('\n','') for NotRelevantItem in NotRelevant])))):
                            open(f'{Folder}{os.sep}AnswerWithRelevanceCheck_{TRY}.txt','w',encoding='UTF8').write(Response+'\n')
                            TRY+=1
                            continue
                        if any([NotRelevantItem in Response.replace(' ','').replace('\n','') for NotRelevantItem in NotRelevant]):
                                Response='※※※※※※※The provided answers are not relevant to the questions.※※※※※※※'
                        if '※※The provided answers are not relevant to the questions.※※' not in Response:
                            content = '<?xml version="1.0" encoding="UTF-8"?>\n<Questions>\n' + Response.split('<Questions>')[-1]
                            content=content=content.split('</Questions>')[0]+'\n</Questions>'
                            for tag in tags_to_wrap:
                                content = wrap_specific_tags_with_cdata(tag, content.strip())
                            try:
                                ET.fromstring(content)
                            except Exception as e:
                                open(f'{Folder}{os.sep}AnswerWithRelevanceCheck_{TRY}.txt','w',encoding='UTF8').write(Response+'\n')
                                TRY+=1
                                continue
                        with open(f'{Folder}{os.sep}AnswerWithRelevanceCheck.{part}.txt', 'w', encoding='UTF-8') as file:
                            file.write(Response + '\n')
                        break
                    except (Exception,func_timeout.exceptions.FunctionTimedOut) as e:
                        pattern = r"Function\s+(\S+).*?timed out after\s+(\d+\.\d+)\s+seconds."
                        replacement = r"\1 timed out after \2 s"
                        if semaphore_acquired:
                            semaphore_acquired.release()
                        open('Exceptionlog','a').write('\t'.join([str(FolderIndex),Folder,part,time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime()),
                                                                  re.sub(pattern, replacement, str(e), flags=re.DOTALL),'\n']))
                        TRY+=1
                        continue
                progress_bar.update(1)
            else:
                progress_bar.update(1)
            open('log','a').write('\t'.join([str(FolderIndex),Folder,part,time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime()),'end\n']))
    threads = [Thread(target=worker) for _ in range(Threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    progress_bar.close()
def Main(Folder,Threads,FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT):
    old_stdout = sys.stdout
    sys.stdout = STDOUT
    os.chdir(Folder)
    Folders=[i for i in os.listdir('.') if i.startswith('10.')]
    Folders.sort()
    chunk_size=7
    AllPrompt=[]
    with open('../QuestionsForReview.txt', 'r',encoding='UTF8') as f:
        content = [i for i in f.readlines() if i.strip()]
        SPLIT=False    
        if len(content)>chunk_size:
            SPLIT=True
            for i in range(0, len(content), chunk_size):
                AllPrompt.append('\n'.join(content[i:i+chunk_size]))
        else:
            AllPrompt.append(content)
    GetResponse(Folders,AllPrompt,chunk_size,Threads,FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT)
    os.chdir('..')
    sys.stdout = old_stdout
