import tkinter as tk
import tkinter.simpledialog
import io
import re
import os
import sys
import json
import time
import shutil
import threading
import traceback
import functools
import importlib
import subprocess
RootDir=os.path.abspath('.')
os.makedirs('Temp',exist_ok=True)
os.chdir('Temp')
import Utility.License
import Utility.GetResponse
import LiteratureSearch.One_key_download
import TopicFormulation.GetQuestionsFromReview
import KnowledgeExtraction.XMLFormattedPrompt
import KnowledgeExtraction.GetAllResponse
import KnowledgeExtraction.AnswerIntegration
import KnowledgeExtraction.SplitIntoFolders
import KnowledgeExtraction.LinkAnswer
import ReviewComposition.GenerateParagraphOfReview
import ReviewComposition.GenerateRatingsForReviewParagraphs
import ReviewComposition.ExtractSectionsWithTags
RunningLock=False
RunningCheckLLMLock=False
LLMChecked=False
WindowsTextLength=36
Parameters={}
ParametersLists={}
EncryptParameters={}
EncryptParametersLists={}
InputButtons={}
InputEntrys={}
InputCheckButtons={}
OutsideInputEntrys={}
OutsideInputCheckButtons={}
FunctionClaudeAPI={}
FunctionOpenAIAPI={}
def Print(*Content,sep='\t'):
    with open(f'{RootDir}{os.sep}Temp{os.sep}run.log','a',encoding='UTF8') as FILE:
        FILE.write(sep.join([str(i) for i in Content])+'\n')
class TextRedirector(io.StringIO):
    def __init__(self, widget):
        self.widget = widget
        self.progress_line = None
        io.StringIO.__init__(self)
    def write(self, str):
        cleaned_str = re.sub(r'\x1b\[.*?[@-~]', '', str.replace("\r", ""))
        Print(str)
        if "\r" in str:
            cleaned_str=cleaned_str.replace('\n','')
            if self.progress_line is not None:
                self.widget.delete(self.progress_line, f"{self.progress_line} lineend")
            else:
                self.widget.insert(tk.END, "\n")
                self.progress_line = self.widget.index("end-1c linestart")
            self.widget.insert(self.progress_line, cleaned_str)
            if "100%" in str:
                self.progress_line = None
        else:
            if cleaned_str.replace('\n','').strip():
                if cleaned_str.replace('\n','').strip()=='█':
                    cleaned_str='\n'
                self.widget.insert(tk.END, cleaned_str + '\n')
        self.widget.see(tk.END)
    def flush(self):
        pass
def run_command(command):
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        subprocess.Popen(command, startupinfo=startupinfo)
    else:
        subprocess.Popen(command)
def SaveParameters():
    with open(f'{RootDir}{os.sep}Parameters','w',encoding='UTF8') as File:
        json.dump([Parameters,ParametersLists,
                   {k:Utility.License.Encrypt(v,Utility.License.Public) for k,v in EncryptParameters.items()},
                   {k:'Ο'.join([Utility.License.Encrypt(i,Utility.License.Public) for i in v]) if v else Utility.License.Encrypt('',Utility.License.Public) for k,v in EncryptParametersLists.items()}],File)
if not os.path.exists(f'{RootDir}{os.sep}Parameters'):
    Parameters.update({
        'StartYear':'StartYear',
        'EndYear':'EndYear',
        'Q1':True,
        'Q2&Q3':False,
        'Demo':True,
        'WholeProcess':False,
        'Threads':0,
        'TOPIC':'Review Topic',
        'SkipSearching':False,
        'SkipTopicFormulation':False,
        'SkipKnowledgeExtraction':False,
        'SkipReviewComposition':False
        })
    ParametersLists.update({
        'ResearchKeys':[],
        'ScreenKeys':[],
        })
    EncryptParametersLists.update({
        'SerpApiList':[],
        'ClaudeApiKey':[],
        'OpenAIApiUrl':[],
        'OpenAIApiKey':[],
        })
    SaveParameters()
else:    
    with open(f'{RootDir}{os.sep}Parameters','r',encoding='UTF8') as File:
        Parameters,ParametersLists,EncryptParameters,EncryptParametersLists=json.load(File)
        try:
            EncryptParameters={k:Utility.License.Decrypt(v,Utility.License.Private) for k,v in EncryptParameters.items()}
            EncryptParametersLists={k:[Utility.License.Decrypt(i,Utility.License.Private) for i in v.split('Ο')] for k,v in EncryptParametersLists.items()}
            EncryptParametersLists={k:[i for i in v if i] for k,v in EncryptParametersLists.items()}
        except Exception as e:
            root = tk.Tk()
            root.withdraw()
            tk.messagebox.showerror('Error','Wrong License.')
            sys.exit(0)
ParametersType={k:Dict  for Dict in ['Parameters','ParametersLists','EncryptParameters','EncryptParametersLists'] for k in eval(Dict).keys()}
def RunAutomaticReviewGenerationThreaded():
    global RunningLock
    if not RunningLock:
        RunningLock=True
        [importlib.reload(Lib) for Lib in [Utility.License,Utility.GetResponse,LiteratureSearch.One_key_download,TopicFormulation.GetQuestionsFromReview,KnowledgeExtraction.XMLFormattedPrompt,KnowledgeExtraction.GetAllResponse,KnowledgeExtraction.AnswerIntegration,KnowledgeExtraction.SplitIntoFolders,KnowledgeExtraction.LinkAnswer,ReviewComposition.GenerateParagraphOfReview,ReviewComposition.GenerateRatingsForReviewParagraphs]]
        try:
            SaveParameters()
            toggle_frames() if Row0Frame.winfo_viewable() else None
            for Folder in ['data','search_logs','search_results']:
                try:
                    shutil.rmtree(Folder)
                except FileNotFoundError:
                    pass
            try:
                os.remove('run.log')
            except FileNotFoundError:
                pass
            threading.Thread(target=lambda: RunAutomaticReviewGeneration()).start()
        except Exception as e :
            tk.messagebox.showerror(f"Error\t{str(e)}", traceback.format_exc())
            RunningLock=False
    else:
        tk.messagebox.showerror('Automatic Review Generation is running','Only run one process in the same time.')
def RunAutomaticReviewGeneration():
    old_stdout = sys.stdout
    sys.stdout = TextRedirector(display)
    try:
        print('█')
        print('█'*WindowsTextLength)
        print(f"Start\t{time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime())}")
        print('Run Demo') if Parameters['Demo'] else None
        print('Run Whole Process') if Parameters['WholeProcess'] else None
        print('Skip Searching') if Parameters['SkipSearching'] else None
        print('Skip Topic Formulation') if Parameters['SkipTopicFormulation'] else None
        print('Skip Knowledge Extraction') if Parameters['SkipKnowledgeExtraction'] else None
        print('Skip Review Composition') if Parameters['SkipReviewComposition'] else None
        print('█'*WindowsTextLength)
        if not Parameters['SkipSearching']:
            print('█')
            print('█'*WindowsTextLength)
            print(f"Start LiteratureSearch\t{time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime())}")
            print('█'*WindowsTextLength)
            LiteratureSearch.One_key_download.User_pages(EncryptParametersLists['SerpApiList'], ParametersLists['ResearchKeys'],
                                               ParametersLists['ScreenKeys'],int(Parameters['StartYear']),int(Parameters['EndYear']),
                                               Parameters['Q1'],Parameters['Q2&Q3'],Parameters['Demo'],STDOUT=sys.stdout)
            Parameters['SkipSearching']=True
            UpdateButtons()
            print('█')
            print('█'*WindowsTextLength)
            print(f"End LiteratureSearch\t{time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime())}")
            print('█'*WindowsTextLength)
        if Parameters['WholeProcess']:
            if not LLMChecked:
                global FunctionClaudeAPI,FunctionOpenAIAPI
                FunctionClaudeAPI={Index:functools.partial(Utility.GetResponse.GetResponseFromClaude,api_key=Key) for Index,Key in enumerate(EncryptParametersLists['ClaudeApiKey'])}
                FunctionOpenAIAPI={Index:functools.partial(Utility.GetResponse.GetResponseFromClaudeViaWebAgent,url=Url,key=Key) for Index,(Url,Key) in enumerate(zip(EncryptParametersLists['OpenAIApiUrl'],EncryptParametersLists['OpenAIApiKey']))}
            if not Parameters['SkipTopicFormulation']:
                if os.path.exists(f'{RootDir}{os.sep}Temp{os.sep}LiteratureSearchWorkDir'):       
                    print('█')
                    print('█'*WindowsTextLength)
                    print(f"Start TopicFormulation\t{time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime())}")
                    print('█'*WindowsTextLength)
                    os.makedirs(f'{RootDir}{os.sep}Temp{os.sep}TopicFormulationWorkDir',exist_ok=True)
                    [shutil.copy(f'{RootDir}{os.sep}Temp{os.sep}LiteratureSearchWorkDir{os.sep}{i}',f'{RootDir}{os.sep}Temp{os.sep}TopicFormulationWorkDir{os.sep}{i}') for i in os.listdir(f'{RootDir}{os.sep}Temp{os.sep}LiteratureSearchWorkDir') if i.startswith('10.') and i.endswith('_Review.txt')]
                    TopicFormulation.GetQuestionsFromReview.Main(f'{RootDir}{os.sep}Temp{os.sep}TopicFormulationWorkDir',Parameters['TOPIC'],Parameters['Threads'],FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT=sys.stdout)
                    if not os.path.exists(f'{RootDir}{os.sep}Temp{os.sep}ParagraphQuestionsForReview.txt'):
                        tk.messagebox.showinfo('','In the window that pops up below, modify and save the outline.\nClose the window and the next step will be executed.')
                        process =subprocess.Popen(["notepad.exe", f'{RootDir}{os.sep}Temp{os.sep}TopicFormulationWorkDir{os.sep}AllQuestionsFromReview{os.sep}QuestionsFromReviewManual.txt'])
                        process.wait()
                    TopicFormulation.GetQuestionsFromReview.Main2(f'{RootDir}{os.sep}Temp{os.sep}TopicFormulationWorkDir',Parameters['TOPIC'],Parameters['Threads'],FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT=sys.stdout)
                    Parameters['SkipTopicFormulation']=True
                    UpdateButtons()
                    print('█')
                    print('█'*WindowsTextLength)
                    print(f"End TopicFormulation\t{time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime())}")
                    print('█'*WindowsTextLength)
                else:
                    tk.messagebox.showinfo('','Prepare papers before run TopicFormulation\nPapers can be generated by LiteratureSearch')
            if not Parameters['SkipKnowledgeExtraction']:
                if os.path.exists(f'{RootDir}{os.sep}Temp{os.sep}QuestionsForReview.txt'):                    
                    print('█')
                    print('█'*WindowsTextLength)
                    print(f"Start KnowledgeExtraction\t{time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime())}")
                    print('█'*WindowsTextLength)
                    os.makedirs(f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir{os.sep}RawFromPDF',exist_ok=True)
                    [shutil.copy(f'{RootDir}{os.sep}Temp{os.sep}LiteratureSearchWorkDir{os.sep}{i}',f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir{os.sep}RawFromPDF{os.sep}{i}') for i in os.listdir(f'{RootDir}{os.sep}Temp{os.sep}LiteratureSearchWorkDir') if i.startswith('10.') and i.endswith('.txt')]
                    KnowledgeExtraction.XMLFormattedPrompt.GetDataList(f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir')
                    print('Prompts Generated.')
                    KnowledgeExtraction.GetAllResponse.Main(f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir',Parameters['Threads'],FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT=sys.stdout)
                    KnowledgeExtraction.AnswerIntegration.Main(f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir',Parameters['Threads'],FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT=sys.stdout)
                    print('Answers Integrationed.')
                    KnowledgeExtraction.LinkAnswer.Main(f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir')
                    KnowledgeExtraction.SplitIntoFolders.Main(f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir{os.sep}Answer',STDOUT=sys.stdout)
                    Parameters['SkipKnowledgeExtraction']=True
                    UpdateButtons()
                    print('█')
                    print('█'*WindowsTextLength)
                    print(f"End KnowledgeExtraction\t{time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime())}")
                    print('█'*WindowsTextLength)
                else:
                    tk.messagebox.showinfo('','Prepare QuestionsForReview.txt before run KnowledgeExtraction\nQuestionsForReview.txt can be generated by TopicFormulation')
            if not Parameters['SkipReviewComposition']:
                if os.path.exists(f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir{os.sep}Answer') and os.listdir(f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir{os.sep}Answer'):
                    print('█')
                    print('█'*WindowsTextLength)
                    print(f"Start ReviewComposition\t{time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime())}")
                    print('█'*WindowsTextLength)
                    os.makedirs(f'{RootDir}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph',exist_ok=True)
                    [shutil.copytree(f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir{os.sep}Answer{os.sep}{PART}{os.sep}{num}',f'{RootDir}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}{int(PART.split("PART")[-1])*7+int(num)}',dirs_exist_ok=True)
                         for PART in os.listdir(f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir{os.sep}Answer') if PART.startswith('PART')
                         for num in os.listdir(f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir{os.sep}Answer{os.sep}{PART}') if (not num.endswith('.txt')) and (os.listdir(f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir{os.sep}Answer{os.sep}{PART}{os.sep}{num}'))]
                    ReviewComposition.GenerateParagraphOfReview.Main(f'{RootDir}{os.sep}Temp{os.sep}ReviewCompositionWorkDir',Parameters['TOPIC'],Parameters['Threads'],FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT=sys.stdout)
                    ReviewComposition.GenerateRatingsForReviewParagraphs.Main(f'{RootDir}{os.sep}Temp{os.sep}ReviewCompositionWorkDir',Parameters['Threads'],FunctionClaudeAPI,FunctionOpenAIAPI,STDOUT=sys.stdout)
                    os.makedirs(f'{RootDir}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}BestParagraph',exist_ok=True)
                    [shutil.copy(f'{RootDir}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph{os.sep}{BestParagraph}',f'{RootDir}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}BestParagraph{os.sep}{BestParagraph}') for BestParagraph in os.listdir(f'{RootDir}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Paragraph') if re.match('BestParagraph\d+.txt',BestParagraph)]
                    ReviewComposition.ExtractSectionsWithTags.Main(f'{RootDir}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}BestParagraph',STDOUT=sys.stdout)
                    shutil.copy(f'{RootDir}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}BestParagraph{os.sep}draft.txt',f'{RootDir}{os.sep}ReviewDraft.txt')
                    for File in ['Waitlog','Exceptionlog',
                                 f'{RootDir}{os.sep}Temp{os.sep}TopicFormulationWorkDir{os.sep}Exceptionlog',
                                 f'{RootDir}{os.sep}Temp{os.sep}KnowledgeExtractionWorkDir{os.sep}Exceptionlog',
                                 f'{RootDir}{os.sep}Temp{os.sep}ReviewCompositionWorkDir{os.sep}Exceptionlog']:
                        try:
                            os.remove(File)
                        except FileNotFoundError:
                            pass
                    Parameters['SkipReviewComposition']=True
                    UpdateButtons()
                    print('█')
                    print('█'*WindowsTextLength)
                    print(f"End ReviewComposition\t{time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime())}")
                    print('█'*WindowsTextLength)
                    process =subprocess.Popen(["notepad.exe", f'{RootDir}{os.sep}ReviewDraft.txt'])
                else:
                    tk.messagebox.showinfo('','Prepare AnswerList before run ReviewComposition\nAnswerList can be generated by KnowledgeExtraction')
        print('█')
        print('█'*WindowsTextLength)
        print(f"End\t{time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime())}")
        print('█'*WindowsTextLength)
    except BaseException as e:
        tk.messagebox.showerror(f"Error {str(e)}", traceback.format_exc())
    finally:
        os.chdir(f'{RootDir}{os.sep}Temp')
        sys.stdout = old_stdout
        shutil.copy('run.log',f"logs{os.sep}run{time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime())}.log")
        SaveParameters()
        toggle_frames() if not Row0Frame.winfo_viewable() else None
        os.chdir(RootDir)
        display.see(tk.END)
        global RunningLock
        RunningLock=False
def get_user_input(list_name):
    user_input = tk.simpledialog.askstring("Input", f"Enter a string for {list_name}\nEnter '!!!~~~!!!' to clean all items in {list_name}\nEnter nothing will change nothing")
    if user_input:
        if user_input=='!!!~~~!!!':
            eval(ParametersType[list_name])[list_name].clear()
            display.insert(tk.END, f'{list_name} Cleared.\n')
        else:
            eval(ParametersType[list_name])[list_name].append(user_input)
            display.insert(tk.END, f'{list_name} Saved.\n')
    if list_name in ['ClaudeApiKey']:
        global FunctionClaudeAPI
        FunctionClaudeAPI={Index:functools.partial(Utility.GetResponse.GetResponseFromClaude,api_key=Key) for Index,Key in enumerate(EncryptParametersLists['ClaudeApiKey'])}
    if list_name in ['OpenAIApiUrl', 'OpenAIApiKey']:
        global FunctionOpenAIAPI
        FunctionOpenAIAPI={Index:functools.partial(Utility.GetResponse.GetResponseFromClaudeViaWebAgent,url=Url,key=Key) for Index,(Url,Key) in enumerate(zip(EncryptParametersLists['OpenAIApiUrl'],EncryptParametersLists['OpenAIApiKey']))}
def CheckYear(Entry):
    try:
        Year=int(Entry.get())
        assert 1900<Year<time.localtime().tm_year+2 , f'1900<Year<{time.localtime().tm_year+3}'
        update_display()
    except Exception as e :
        tk.messagebox.showerror(f"Error  {str(e)}", traceback.format_exc())
def OpenSearchOptions():
    top = tk.Toplevel(root)
    top.title("Search Options")
    Row0Frame = tk.Frame(top)
    Row0Frame.pack()
    Row1Frame = tk.Frame(top)
    Row1Frame.pack()
    ButtonSerpApiList= tk.Button(Row0Frame, text="Add to Serp API List", command=lambda: get_user_input('SerpApiList'))
    ButtonSerpApiList.pack(side=tk.LEFT)
    InputButtons.update({ButtonSerpApiList:'SerpApiList'})
    ButtonResearchKeys=tk.Button(Row0Frame, text="Add to Research Keys", command=lambda: get_user_input('ResearchKeys'))
    ButtonResearchKeys.pack(side=tk.LEFT)
    InputButtons.update({ButtonResearchKeys:'ResearchKeys'})
    ButtonScreenKeys = tk.Button(Row0Frame, text="Add to Screen Keys", command=lambda: get_user_input('ScreenKeys'))
    ButtonScreenKeys.pack(side=tk.LEFT)
    InputButtons.update({ButtonScreenKeys:'ScreenKeys'})
    EntryStartYear= tk.Entry(Row1Frame,width=10)
    EntryStartYear.pack(side=tk.LEFT)
    EntryStartYear.insert(0, Parameters['StartYear'])
    EntryStartYear.bind("<Return>", lambda event: CheckYear(EntryStartYear))
    InputEntrys.update({EntryStartYear:'StartYear'})
    EntryEndYear = tk.Entry(Row1Frame,width=10)
    EntryEndYear.pack(side=tk.LEFT)
    EntryEndYear.insert(0, Parameters['EndYear'])
    EntryEndYear.bind("<Return>", lambda event: CheckYear(EntryEndYear))
    InputEntrys.update({EntryEndYear:'EntryEndYear'})
    BooleanVarQ1= tk.BooleanVar(value=Parameters['Q1'])
    CheckbuttonQ1= CustomCheckbutton(Row1Frame, text="Q1", variable=BooleanVarQ1)
    CheckbuttonQ1.pack(side=tk.LEFT)
    InputCheckButtons.update({CheckbuttonQ1:[BooleanVarQ1,'Q1']})
    BooleanVarQ23=tk.BooleanVar(value=Parameters['Q2&Q3'])
    CheckbuttonQ23 = CustomCheckbutton(Row1Frame, text="Q2&Q3", variable=BooleanVarQ23)
    CheckbuttonQ23.pack(side=tk.LEFT)
    InputCheckButtons.update({CheckbuttonQ23:[BooleanVarQ23,'Q2&Q3']})
    save_button = tk.Button(top, text="Save", command=lambda: save_settings())
    save_button.pack()
    def save_settings():
        Parameters['StartYear']=EntryStartYear.get()
        Parameters['EndYear']=EntryEndYear.get()
        Parameters['Q1']=BooleanVarQ1.get()
        Parameters['Q2&Q3']=BooleanVarQ23.get()
        SaveParameters()
        display.insert(tk.END, 'Search Options Saved.\n')
    def on_close():
        old_stdout = sys.stdout
        sys.stdout = TextRedirector(display)
        print('█')
        print(f"SerpApi List: {len(EncryptParametersLists['SerpApiList'])} APIs")
        print(f"Research Keys: {ParametersLists['ResearchKeys']}")
        print(f"Screen Keys: {ParametersLists['ScreenKeys']}")
        print(f"Start Year: {Parameters['StartYear']}")
        print(f"End Year: {Parameters['EndYear']}")
        print(f"CAS Q1: {Parameters['Q1']}")
        print(f"CAS Q2&Q3: {Parameters['Q2&Q3']}")
        sys.stdout = old_stdout
        top.destroy()
    top.protocol("WM_DELETE_WINDOW", on_close)        
def CheckLLMResponseThreaded():
    global RunningCheckLLMLock
    if not RunningCheckLLMLock:
        RunningCheckLLMLock=True
        threading.Thread(target=lambda: CheckLLMResponse()).start()
    else:
        tk.messagebox.showerror('Check LLM Response is running','Only run one process in the same time.')
def CheckLLMResponse():
    old_stdout = sys.stdout
    sys.stdout = TextRedirector(display)
    print('█')
    print('Check LLM Response:')
    print('Check ClaudeAPI Response:')
    for Index,Key in enumerate(EncryptParametersLists['ClaudeApiKey']):
        try:
            Response=Utility.GetResponse.GetResponseFromClaude('Who are you?',Key)
            print(f'{Index}\t{Response}')
            FunctionClaudeAPI.update({Index:functools.partial(Utility.GetResponse.GetResponseFromClaude,api_key=Key)})
        except Exception as e:
            FunctionClaudeAPI.update({Index:False})
            print(f'{Index}\tFailed',e)
    print('Check OpenAIAPI Response:')
    for Index,(Url,Key) in enumerate(zip(EncryptParametersLists['OpenAIApiUrl'],EncryptParametersLists['OpenAIApiKey'])):
        try:
            Response=Utility.GetResponse.GetResponseFromClaudeViaWebAgent('Who are you?',Url,Key)
            print(f'{Index}\t{Response}')
            FunctionOpenAIAPI.update({Index:functools.partial(Utility.GetResponse.GetResponseFromClaudeViaWebAgent,url=Url,key=Key)})
        except Exception as e:
            FunctionOpenAIAPI.update({Index:False})
            print(f'{Index}\tFailed',e)
    print('Check LLM finished')
    print(f'FunctionClaudeAPI\t{ {k:bool(v) for k,v in FunctionClaudeAPI.items()} }') if FunctionClaudeAPI else None
    print(f'FunctionOpenAIAPI\t{ {k:bool(v) for k,v in FunctionOpenAIAPI.items()} }') if FunctionOpenAIAPI else None
    sys.stdout = old_stdout
    global RunningCheckLLMLock,LLMChecked
    LLMChecked=True
    RunningCheckLLMLock=False
def OpenLLMOptions():
    top = tk.Toplevel(root)
    top.title("LLM Options")
    Row0Frame = tk.Frame(top)
    Row0Frame.pack()
    Row1Frame = tk.Frame(top)
    Row1Frame.pack()
    Row2Frame = tk.Frame(top)
    Row2Frame.pack()    
    ButtonClaudeApiKey= tk.Button(Row0Frame, text="Add to Claude Api Key List", command=lambda: get_user_input('ClaudeApiKey'))
    ButtonClaudeApiKey.pack(side=tk.LEFT)
    InputButtons.update({ButtonClaudeApiKey:'ClaudeApiKey'})
    ButtonOpenAIApiUrl= tk.Button(Row1Frame, text="Add to OpenAI-compatible API Url List", command=lambda: get_user_input('OpenAIApiUrl'))
    ButtonOpenAIApiUrl.pack(side=tk.LEFT)
    InputButtons.update({ButtonOpenAIApiUrl:'OpenAIApiUrl'})
    ButtonOpenAIApiKey= tk.Button(Row2Frame, text="Add to OpenAI-compatible API Key List", command=lambda: get_user_input('OpenAIApiKey'))
    ButtonOpenAIApiKey.pack(side=tk.LEFT)
    InputButtons.update({ButtonOpenAIApiKey:'OpenAIApiKey'})
    ButtonCheckLLMResponse=tk.Button(Row2Frame, text="Check LLM Response", command=CheckLLMResponseThreaded)
    ButtonCheckLLMResponse.pack(side=tk.LEFT)
    def on_close():
        old_stdout = sys.stdout
        sys.stdout = TextRedirector(display)
        print('█')
        print(f"ClaudeApiKey List: {len(EncryptParametersLists['ClaudeApiKey'])} Keys")
        print(f"OpenAIApiUrl List: {len(EncryptParametersLists['OpenAIApiUrl'])} Urls")
        print(f"OpenAIApiKey List: {len(EncryptParametersLists['OpenAIApiKey'])} Keys")
        Parameters["Threads"]=len(list(zip(EncryptParametersLists['OpenAIApiUrl'],EncryptParametersLists['OpenAIApiKey'])))*3+len(EncryptParametersLists['ClaudeApiKey'])
        print(f'Theads: {Parameters["Threads"]}\n')
        SaveParameters()
        display.insert(tk.END, 'LLM Options Saved.\n')
        sys.stdout = old_stdout
        top.destroy()
    top.protocol("WM_DELETE_WINDOW", on_close)
class CustomCheckbutton(tk.Frame):
    def __init__(self, parent, text="", variable=None, command=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._variable = variable
        self.command = command
        self.canvas = tk.Canvas(self, width=20, height=20, bg='black', highlightthickness=0)
        self.check_rect = self.canvas.create_rectangle(1, 1, 19, 19, outline='white', fill='black', width=4)
        self.canvas.bind("<Button-1>", self.toggle)
        self.canvas.pack(side=tk.LEFT)
        self.label = tk.Label(self, text=text, bg='black', fg='white')
        self.label.pack(side=tk.LEFT)
        self.label.bind("<Button-1>", self.toggle)
        self.update_check()
    def toggle(self, event=None):
        if self._variable.get() == 0:
            self._variable.set(1)
        else:
            self._variable.set(0)
        self.update_check()
        if self.command is not None:
            self.command()
    def update_check(self):
        if self._variable.get() == 0:
            self.canvas.itemconfig(self.check_rect, fill='black')
        else:
            self.canvas.itemconfig(self.check_rect, fill='white')
    def config(self, **kwargs):
        if "variable" in kwargs:
            self._variable = kwargs.pop("variable")
        super().config(**kwargs)
        self.update_check()
    def configure(self, **kwargs):
        self.config(**kwargs)
def UpdateButtons():
    for k in OutsideInputCheckButtons.keys():
        OutsideInputCheckButtons[k][0].set(eval(ParametersType[OutsideInputCheckButtons[k][1]])[OutsideInputCheckButtons[k][1]])
        k.config(variable=OutsideInputCheckButtons[k][0])
def update_display():
    UpdateButtons()
    display.insert(tk.END, f"\n")
    display.insert(tk.END, f"TOPIC: {Parameters['TOPIC']}\n")
    display.insert(tk.END, f"Demo: {Parameters['Demo']}\n")
    display.insert(tk.END, f"WholeProcess: {Parameters['WholeProcess']}\n")
    display.insert(tk.END, f"SkipSearching: {Parameters['SkipSearching']}\n")
    display.insert(tk.END, f"SkipTopicFormulation: {Parameters['SkipTopicFormulation']}\n")
    display.insert(tk.END, f"SkipKnowledgeExtraction: {Parameters['SkipKnowledgeExtraction']}\n")
    display.insert(tk.END, f"SkipReviewComposition: {Parameters['SkipReviewComposition']}\n")
    display.see(tk.END)
def SaveAndUpdateDisplay():
    for k in OutsideInputEntrys.keys():
        eval(ParametersType[InputEntrys[k]])[InputEntrys[k]]=k.get()
    for k in OutsideInputCheckButtons.keys():
        eval(ParametersType[InputCheckButtons[k][1]])[InputCheckButtons[k][1]]=InputCheckButtons[k][0].get()
    SaveParameters()
    update_display()
def toggle_frames():
    is_visible = Row0Frame.winfo_viewable()
    for frame in [Row0Frame, Row1Frame, Row2Frame, Row3Frame, Row4Frame,display,scrollbar]:
        frame.pack_forget()
    if is_visible:
        Row4Frame.pack()
        display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    else:
        for frame in [Row0Frame, Row1Frame, Row2Frame, Row3Frame, Row4Frame]:
            frame.pack()
        display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
root = tk.Tk()
root.title("Automatic Review Generation V0.0")
root.option_add("*Font", "{Times New Roman} 25")
root.option_add('*background', 'black')
root.option_add('*foreground', 'white')
root.option_add('*Entry*insertBackground', 'white')
root.option_add('*Text*insertBackground', 'white')
root.configure(bg='black')
Row0Frame = tk.Frame(root)
Row0Frame.pack()
Row1Frame = tk.Frame(root)
Row1Frame.pack()
Row2Frame = tk.Frame(root)
Row2Frame.pack()
Row3Frame = tk.Frame(root)
Row3Frame.pack()
Row4Frame = tk.Frame(root)
Row4Frame.pack()
tk.Label(Row0Frame, text="TOPIC:").pack(side=tk.LEFT)
EntryTOPIC= tk.Entry(Row0Frame)
EntryTOPIC.pack(side=tk.LEFT, padx=(0, 32))
EntryTOPIC.insert(0, Parameters['TOPIC'])
EntryTOPIC.bind("<Return>", lambda event: SaveAndUpdateDisplay())
InputEntrys.update({EntryTOPIC:'TOPIC'})
OutsideInputEntrys.update({EntryTOPIC:'TOPIC'})
BooleanVarDemo=tk.BooleanVar(value=Parameters['Demo'])
CheckbuttonDemo=CustomCheckbutton(Row0Frame, text="Demo", variable=BooleanVarDemo, command=SaveAndUpdateDisplay)
CheckbuttonDemo.pack(side=tk.LEFT, padx=(0, 17))
InputCheckButtons.update({CheckbuttonDemo:[BooleanVarDemo,'Demo']})
OutsideInputCheckButtons.update({CheckbuttonDemo:[BooleanVarDemo,'Demo']})
BooleanVarWholeProcess=tk.BooleanVar(value=Parameters['WholeProcess'])
CheckbuttonWholeProcess=CustomCheckbutton(Row0Frame, text="Whole Process", variable=BooleanVarWholeProcess, command=SaveAndUpdateDisplay)
CheckbuttonWholeProcess.pack(side=tk.LEFT)
InputCheckButtons.update({CheckbuttonWholeProcess:[BooleanVarWholeProcess,'WholeProcess']})
OutsideInputCheckButtons.update({CheckbuttonWholeProcess:[BooleanVarWholeProcess,'WholeProcess']})
BooleanVarSkipSearching= tk.BooleanVar(value=Parameters['SkipSearching'])
CheckbuttonSkipSearching=CustomCheckbutton(Row1Frame, text="Skip Literature Search", variable=BooleanVarSkipSearching, command=SaveAndUpdateDisplay)
CheckbuttonSkipSearching.pack(side=tk.LEFT, padx=(0,114))
InputCheckButtons.update({CheckbuttonSkipSearching:[BooleanVarSkipSearching,'SkipSearching']})
OutsideInputCheckButtons.update({CheckbuttonSkipSearching:[BooleanVarSkipSearching,'SkipSearching']})
BooleanVarSkipTopicFormulation= tk.BooleanVar(value=Parameters['SkipTopicFormulation'])
CheckbuttonSkipTopicFormulation=CustomCheckbutton(Row1Frame, text="Skip Topic Formulation", variable=BooleanVarSkipTopicFormulation, command=SaveAndUpdateDisplay)
CheckbuttonSkipTopicFormulation.pack(side=tk.LEFT,padx=(0,27))
InputCheckButtons.update({CheckbuttonSkipTopicFormulation:[BooleanVarSkipTopicFormulation,'SkipTopicFormulation']})
OutsideInputCheckButtons.update({CheckbuttonSkipTopicFormulation:[BooleanVarSkipTopicFormulation,'SkipTopicFormulation']})
BooleanVarSkipKnowledgeExtraction= tk.BooleanVar(value=Parameters['SkipKnowledgeExtraction'])
CheckbuttonSkipKnowledgeExtraction=CustomCheckbutton(Row2Frame, text="Skip Knowledge Extraction", variable=BooleanVarSkipKnowledgeExtraction, command=SaveAndUpdateDisplay)
CheckbuttonSkipKnowledgeExtraction.pack(side=tk.LEFT, padx=(0, 49))
InputCheckButtons.update({CheckbuttonSkipKnowledgeExtraction:[BooleanVarSkipKnowledgeExtraction,'SkipKnowledgeExtraction']})
OutsideInputCheckButtons.update({CheckbuttonSkipKnowledgeExtraction:[BooleanVarSkipKnowledgeExtraction,'SkipKnowledgeExtraction']})
BooleanVarSkipReviewComposition= tk.BooleanVar(value=Parameters['SkipReviewComposition'])
CheckbuttonSkipReviewComposition=CustomCheckbutton(Row2Frame, text="Skip Review Composition", variable=BooleanVarSkipReviewComposition, command=SaveAndUpdateDisplay)
CheckbuttonSkipReviewComposition.pack(side=tk.LEFT)
InputCheckButtons.update({CheckbuttonSkipReviewComposition:[BooleanVarSkipReviewComposition,'SkipReviewComposition']})
OutsideInputCheckButtons.update({CheckbuttonSkipReviewComposition:[BooleanVarSkipReviewComposition,'SkipReviewComposition']})
ButtonOpenSearchOptions = tk.Button(Row3Frame, text="Search Options", command=OpenSearchOptions)
ButtonOpenSearchOptions.pack(side=tk.LEFT)
ButtonOpenLLMOptions = tk.Button(Row3Frame, text="LLM Options", command=OpenLLMOptions)
ButtonOpenLLMOptions.pack(side=tk.LEFT)
toggle_button = tk.Button(Row4Frame, text="Show/Hide Options", command=toggle_frames)
toggle_button.pack(side=tk.LEFT)
ButtonRunAutomaticReviewGeneration = tk.Button(Row4Frame, text="Run Automatic Review Generation", command=RunAutomaticReviewGenerationThreaded)
ButtonRunAutomaticReviewGeneration.pack(side=tk.LEFT)
display = tk.Text(root, height=13, width=49)
scrollbar = tk.Scrollbar(root, command=display.yview)
display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
display.config(yscrollcommand=scrollbar.set)
update_display()
root.attributes('-topmost', True)
root.update()
root.attributes('-topmost', False)
window_width = root.winfo_width()
window_height = root.winfo_height()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = int((screen_width / 2) - (window_width / 2))
y = int((screen_height / 2) - (window_height / 2))
root.geometry(f'{window_width}x{window_height}+{x}+{y}')
root.mainloop()
os.chdir(RootDir)
try:
    shutil.copy(f'Temp{os.sep}run.log',f"Temp{os.sep}logs{os.sep}run{time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime())}.log")
except:
    pass
run_command(f"TASKKILL /F /IM {os.path.basename(sys.executable) if 'python' not in os.path.basename(sys.executable) else 'GUI.exe'}")
