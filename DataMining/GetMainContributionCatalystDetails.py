import re
import os
import tqdm
from queue import Queue, Empty
from threading import Thread, Semaphore
import xml.etree.ElementTree as ET
import time
import json
import shutil
import requests
Folders=[i for i in os.listdir('RawFromPDF') if i.startswith('10.')]
Folders.sort()
HEAD='''<DOCUMENT>\n'''
END='''
</DOCUMENT>
Examine the content within the supplied document to determine if it pertains to any form of propane dehydrogenation, including both Propane Dehydrogenation (PDH) and Oxidative Propane Dehydrogenation (ODH). If the document discusses either of these processes in the context of converting propane to propylene, please continue to assess the main scientific contributions as outlined in the subsequent steps.
1. Identify the catalyst that represents the main scientific contribution in the document.
2. Extract and detail the following information for this catalyst:
    - Name
    - Type: Metal, Metal Oxide, Single Atom, Alloy, Others
    - Composition Element(s) (chemical symbols)
    - If the Type is "Alloy":
        - Structure Type: Nanoparticulate Alloys, Intermetallic Compounds, Single-atom Alloys, Others
        - Preparation Method: Impregnation Methods, Heat Treatment, Surface & Support Methods, Solution-Based Methods, In Situ Synthesis, Chemical Methods, Physical Methods, etc.
    - Active Species Element(s) (chemical symbols)
    - Promoter Element(s) (chemical symbols, if any)
    - Support Material: Silica Oxide, Aluminum Oxide, Oxides, Carbides, Zeolites, Others
    - Conversion (%): Specify type (e.g., single-pass conversion, propane conversion, overall conversion)
    - Selectivity (%)
    - Stability (if in h-1 or convert to h-1)
    - Deactivation Rate(s) (value and units)
    - Propane Production Rate (value and units)
    - Propylene Yield (%)
    - Feed Composition and Ratio(s)
    - Propane Partial Pressure
    - Reaction Temperature (value and units)
    - Inlet Flow Rate (value and units)
    - Catalyst Loading or Gas Hourly Space Velocity (GHSV) (value and units)
3. Determine how the manuscript increases selectivity, conversion, and stability, focusing on improvements in catalyst preparation method, structural composition, process conditions, or reactor design.
4. Describe the specific performance enhancements (selectivity, conversion, stability) and summarize the advancement in one sentence.
5. Convert the stability to an hourly rate (h-1) if not already in that unit.
6. Identify whether the catalyst is utilized for Propane Dehydrogenation (PDH), a process that does not involve oxidation, or for Oxidative Propane Dehydrogenation (ODH), where an oxidative process is integral. Clarify the distinction between PDH, where propane is dehydrogenated to propylene without the presence of oxygen or other oxidizing agent, and ODH, which involves the oxidation of propane as a part of the dehydrogenation process to propylene.
7. Identify the feed gas composition utilized with the catalyst.
8. Determine if the feed gas contains an oxidizing agent.
Output the information in an XML format following the provided template.
<output>
	<Relevance>
		(Indicate yes or no)
	</Relevance>
	<IfRelated>
		<MainScientificContribution>
			<Catalyst>
				<Name>____</Name> <!-- N/A if not mentioned -->
				<Type>____</Type> <!-- Metal, Metal Oxide, Single Atom, Alloy, Others -->
				<CompositionElements>
					<Element>__Chemical Symbol__</Element>
					<!-- Add more elements as necessary -->
				</CompositionElements> <!-- N/A if not mentioned -->
				<AlloyDetails> <!-- Include only if Type is Alloy -->
					<StructureType>____</StructureType> <!-- E.g., Nanoparticulate Alloys -->
					<PreparationMethod>____</PreparationMethod> <!-- E.g., Impregnation Methods -->
				</AlloyDetails> <!-- N/A if not mentioned -->
				<ActiveSpeciesElements>
					<Element>__Chemical Symbol__</Element>
					<!-- Add more elements as necessary -->
				</ActiveSpeciesElements> <!-- N/A if not mentioned -->
				<PromoterElements>
					<Element>__Chemical Symbol__</Element>
					<!-- Add more elements as necessary -->
				</PromoterElements> <!-- N/A if not mentioned -->
				<SupportMaterial>____</SupportMaterial> <!-- N/A if not mentioned -->
				<ConversionTypes>
					<Type>____</Type> <!-- E.g., single-pass conversion, propane conversion, overall conversion -->
					<Value>__Value%__</Value>
					<!-- Add more types as necessary -->
				</ConversionTypes> <!-- N/A if not mentioned -->
				<Selectivity>__Value%__</Selectivity> <!-- N/A if not mentioned -->
				<StabilityOriginal>__Value (Original Units)__</StabilityOriginal> <!-- N/A if not mentioned -->
				<ConvertedStability>__Value (h-1)__</ConvertedStability> <!-- N/A if not mentioned -->
				<DeactivationRates>
					<Rate>__Value (Units)__</Rate>
					<!-- Add more rates as necessary -->
				</DeactivationRates> <!-- N/A if not mentioned -->
				<PropaneProductionRate>__Value (Units)__</PropaneProductionRate> <!-- N/A if not mentioned -->
				<PropyleneYield>__Value%__</PropyleneYield> <!-- N/A if not mentioned -->
				<FeedCompositionAndRatios>
					<Ratio>____</Ratio>
					<!-- Add more ratios as necessary -->
				</FeedCompositionAndRatios> <!-- N/A if not mentioned -->
				<PropanePartialPressure>____</PropanePartialPressure> <!-- N/A if not mentioned -->
				<ReactionTemperature>__Value (Units)__</ReactionTemperature> <!-- N/A if not mentioned -->
				<InletFlowRate>__Value (Units)__</InletFlowRate> <!-- N/A if not mentioned -->
				<CatalystLoadingOrGHSV>__Value (Units)__</CatalystLoadingOrGHSV> <!-- N/A if not mentioned -->
 				<TypeIdentify>____</TypeIdentify>  <!-- PDH or ODH -->
				<FeedGasComposition>
					<Component>____</Component>
					<Component>____</Component>
					<!-- Add more items as necessary -->
				</FeedGasComposition>
				<ContainsOxidizingAgent>____</ContainsOxidizingAgent> <!-- Yes or No -->
			</Catalyst>
			<PerformanceEnhancement>
				<EnhancementDetails>
					<!-- Specify the aspect(s) that has/have been enhanced (Selectivity, Conversion, Stability) -->
					<!-- For example, if Selectivity has been enhanced due to a specific preparation method, list it here -->
					<Aspect>____</Aspect> <!-- E.g., Selectivity, Conversion, Stability -->
					<ImprovedBy>____</ImprovedBy> <!-- E.g., Preparation Method, Structural Composition, Process Conditions, Reactor Design -->
					<SummaryOfAdvancement>____</SummaryOfAdvancement>
				</EnhancementDetails>
				<!-- Repeat the <EnhancementDetails> element if there are multiple enhancements -->
			</PerformanceEnhancement>
		</MainScientificContribution>
	</IfRelated>
</output>
'''
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT,RateLimitError,APIError,APIResponseValidationError,APITimeoutError,BadRequestError,InternalServerError
anthropic = Anthropic(api_key=os.getenv('AnthropicKey', ''))
def GetResponseFromClaude(Prompt):
    try:
        return anthropic.completions.create(
            model="claude-2",
            max_tokens_to_sample=65536,
            prompt=f"{HUMAN_PROMPT}{Prompt}{AI_PROMPT}",
            ).completion
    except (RateLimitError,APIError,APIResponseValidationError,APITimeoutError,BadRequestError,InternalServerError) as e:
        import time
        for i in range(99999):
           print(f'TRY {i+1}',e,sep='\t')
           time.sleep(0.1)
           try:
               return anthropic.completions.create(
                model="claude-2",
                max_tokens_to_sample=65536,
                prompt=f"{HUMAN_PROMPT}{Prompt}{AI_PROMPT}",
                ).completion
           except :
               pass
        return ""
def GetResponseFromClaudeViaWebAgent(Prompt):
    ERRORLIST=[i.strip() for i in '''**claude-2 error**
        ```Exceeded completions limit, expires
         Claude2WebAPI
        ```Streaming error```
        AINewServer
        '''.split('\n')if i.strip() ]
    url=os.getenv('LLMWebUrl', '')
    headers = {"content-type": "application/json",
        "Authorization": os.getenv('LLMWEBKey', ''),}
    data={"messages":[{"role":"system","content":"",},{"role":"user",
          "content":Prompt},],
          "model":"claude-2-web","max_tokens_to_sample":65536,}
    response = requests.post(url, headers=headers, json=data)
    Current=json.loads(response.text)
    if 'error' in Current:
        raise RuntimeError(Current['error']['message'])
    Current=Current["choices"][0]['message']['content']
    if any([i for i in ERRORLIST if i in Current]):
        raise RuntimeError([i for i in ERRORLIST if i in Current])
    return Current
def GetResponseConcurrent(prompts):
    prompt_queue = Queue()
    for folder, prompt in prompts:
        prompt_queue.put((folder, prompt))
    semaphore1 = Semaphore(value=0)
    semaphore2 = Semaphore(value=2)
    progress_bar = tqdm.tqdm(total=len(prompts)*Repeat, position=0, leave=True)
    def worker():
        while True:
            try:
                folder, prompt = prompt_queue.get_nowait()
            except Empty:
                break
            for Time in range(Repeat):
                try_num = 0
                while True:
                    semaphore_acquired = None
                    try:
                        if semaphore1.acquire(blocking=False):
                            semaphore_acquired = semaphore1
                            response = GetResponseFromClaude(prompt)
                            semaphore1.release()
                        elif semaphore2.acquire(blocking=False):
                            semaphore_acquired = semaphore2
                            response = GetResponseFromClaudeViaWebAgent(prompt)
                            semaphore2.release()
                        else:
                            open('Waitlog','a').write('\t'.join([folder,time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime()),'waiting\n']))
                            time.sleep(0.5)
                            continue
                        try:
                            if ('<output>' not in response )or ('<Relevance>' not in response ):
                                raise RuntimeError('Error Response')
                            content='<?xml version="1.0" encoding="UTF-8"?>\n<output>\n'+response.strip().split('<output>')[-1]
                            content=content.split('</output>')[0]+'\n</output>'
                            root = ET.fromstring(content)
                        except:
                            with open(os.path.join(folder, f'MainContributionCatalystDetails_{Time}-{try_num}.txt'), 'w', encoding='UTF8') as file:
                                file.write(response + '\n')
                            try_num += 1
                            continue
                        with open(os.path.join(folder, f'MainContributionCatalystDetails_{Time}.txt'), 'w', encoding='UTF8') as file:
                            file.write(response.replace('>Not mentioned<','>N/A<') + '\n')
                        break
                    except Exception as e:
                        if semaphore_acquired:
                            semaphore_acquired.release()
                        open('Exceptionlog','a').write('\t'.join([folder,time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime()),str(e),'\n']))
                        continue
                progress_bar.update(1)
    threads = [Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    progress_bar.close()
prompts_to_check = []
Repeat=5
for File in Folders:
    print(File)
    file_content = open(f'RawFromPDF{os.sep}{File}', 'r', encoding='UTF8').read()
    Prompt = HEAD + file_content + END
    File_path = File.strip(".txt")
    if os.path.exists(File_path) and not os.path.exists(f'{File_path}{os.sep}MainContributionCatalystDetails_{Repeat-1}.txt') and len(Prompt)<333333:
        open(f'{File_path}{os.sep}PromptMainContributionCatalystDetails.txt', 'w', encoding='UTF8').write(Prompt)
        prompts_to_check.append((File_path, Prompt))
GetResponseConcurrent(prompts_to_check)
