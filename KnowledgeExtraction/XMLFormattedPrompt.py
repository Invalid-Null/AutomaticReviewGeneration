import os
import re
import json
file_path_prompt16 = os.path.join('..', 'QuestionsForReview.txt')
FormattedPromptHead='''I'm going to give you a scientific literature. Then I'm going to ask you some questions about it. I'd like you to first write down exact quotes of parts of the document word by word that would help answer the question, and then I'd like you to answer the question using facts from the quoted content. Do not omit any relevant information from the text, and avoid introducing any falsehoods or assumptions that aren't directly supported by the literature. Here is the literature, in <literature></literature> XML tags:
<literature>
'''
FormattedPromptMiddle='''
</literature>
Here are the question lists, in <questions></questions>XML tags:
<questions>
'''
FormattedPromptEnd='''
</questions>
First, you need to sequentially extract any quotes in the literature that are most relevant to each question, and print them in numbered order, separated by newlines. Quotes should be relatively brief. Do not attempt to summarize or answer questions at this stage, but simply repeat exactly what the corresponding part of the literature says.
Please enclose the full list of quotes in <quotes></quotes> XML tags. If there are no relevant quotes, write "No relevant quotes" instead.
Then, answer the question, starting with "Answer:".  Do not include or reference quoted content verbatim in the answer. Don't say "According to Quote [1]" when answering. Do not write reference number of quotes after answer. Put your answer to the user inside <answer></answer> XML tags. Output formatted text, with line breaks for each question.Separate quotes and answers with a blank line. Provide the answers to all questions in English. After completing the English answers, translate all those answers into Chinese and provide the Chinese version.
Thus, the format of your overall response should look like what's shown between the <example></example> tags.  Make sure to follow the formatting and spacing exactly.
<example>
<quotes>
[1] "Company X reported revenue of $12 million in 2021."
</quotes>
<English version answer>
1.Company X earned $12 million in 2021.
</English version answer>
<Chinese version answer>
1.X公司在2021年赚了1200万美元。
</Chinese version answer>
<quotes>
[1] "Almost 90% of revenue came from widget sales, with gadget sales making up the remaining 10%."
</quotes>
<English version answer>
2.Almost 90% of it came from widget sales.
</English version answer>
<Chinese version answer>
2.几乎90%的收入来自小部件销售。
</Chinese version answer>
</example>
If the question cannot be answered by the document, say so.If deemed necessary, the answer to the question can be extended entirely from the content of the document.
Answer all of the questions immediately without preamble. '''
TitlePattern = r'^[^a-zA-Z0-9\u4e00-\u9FFF\s]*\s*(' + '|'.join([
                                'ACKNOWLEDGMENT',
                                'ACKNOWLEDGEMENT',
                                'SUPPLEMENTARY MATERIAL',
                                'REFERENCE',
                                'References',
                                'DATA AVAILABILITY',
                                'Declaration of competing interest',
                                'ABBREVIATIONS',
                                'ASSOCIATED CONTENT',
                                'Conflicts of interest',
                                'Supporting Information',
                                ]) + ')'
InvaildSymbolPattern = r"[^a-zA-Z0-9\u4e00-\u9fa5\u0370-\u03FF ,.!?\-_:;'\"(){}\[\]&<>%\$@\*/=#·Å+•×\\]"
def GetRefineContents(Contents):
    Contents=Contents.replace('ﬀ', 'ff').replace('','fi').replace('ﬁ', 'fi').replace('ﬂ', 'fl').replace('ﬃ', 'ffi').replace('ﬄ', 'ffl').replace('ﬅ', 'ft').replace('ﬆ', 'st').split('\n')
    Contents=[re.sub(InvaildSymbolPattern, '', Content) for  Content in Contents]
    Final=[]
    threshold=320
    for x in Contents:
        if len(x) < threshold and re.match(TitlePattern, x.strip(), re.IGNORECASE) and Final:
            break
        else:
            Final.append(x)
    return '\n'.join(Final)
def GetDataList(Folder):
    os.chdir(Folder)
    os.makedirs('Prompt',exist_ok=True)
    folders=[i for i in os.listdir('RawFromPDF') if i.startswith('10.') and i.endswith('.txt')]
    chunk_size=7
    AllPrompt=[]
    with open(file_path_prompt16, 'r',encoding='UTF8') as f:
        content = [i for i in f.readlines() if i.strip()]
        SPLIT=False    
        if len(content)>chunk_size:
            SPLIT=True
            for i in range(0, len(content), chunk_size):
                AllPrompt.append('\n'.join(content[i:i+chunk_size]))
        else:
            AllPrompt.append(content)
    data_list = []
    for folder in folders:
        file_path_doc = f'RawFromPDF/{folder}'
        with open(file_path_doc,'r',encoding='UTF8') as f:
            doc = GetRefineContents(f.read())
        for i,j in enumerate(AllPrompt):
            with open(f'Prompt{os.sep}Prompt{folder}.PART{i}', 'w',encoding='UTF8') as f:            
                f.write((FormattedPromptHead+ '\n' +doc.strip().replace('\n\n','\n') + '\n' + FormattedPromptMiddle + '\n' + j.strip().replace('\n\n','\n')+ '\n' + FormattedPromptEnd))
    os.chdir('..')
