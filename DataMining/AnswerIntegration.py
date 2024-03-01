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
Folders=[i for i in os.listdir('.') if i.startswith('10.')]
Folders.sort()
HEAD='''<DOCUMENTS>
'''
END='''</DOCUMENTS>
Review the multiple extractions from the same document related to propane dehydrogenation research. Integrate the information from these extractions to form a cohesive and comprehensive summary. Ensure the final aggregated data reflects a synthesized understanding, avoiding a mere enumeration or concatenation of individual items. Follow the structure of the provided XML template for the output, ensuring all pertinent information is seamlessly incorporated into the correct sections of the XML structure.
The goal is to create a single, unified XML entry that accurately represents the key findings and data related to the primary scientific contribution of the document. Here is the XML template to guide the structure of your output:
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
    progress_bar = tqdm.tqdm(total=len(prompts), position=0, leave=True)
    def worker():
        while True:
            try:
                folder, prompt = prompt_queue.get_nowait()
            except Empty:
                break
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
                        with open(os.path.join(folder, f'MainContributionCatalystDetails-{try_num}.txt'), 'w', encoding='UTF8') as file:
                            file.write(response + '\n')
                        try_num += 1
                        continue
                    with open(os.path.join(folder, f'MainContributionCatalystDetails.txt'), 'w', encoding='UTF8') as file:
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
for Folder in Folders:
    print(Folder)
    if all([ os.path.exists(f'{Folder}{os.sep}MainContributionCatalystDetails_{i}.txt') for i in range(Repeat)]):
        Prompt=[HEAD]
        for i in range(Repeat):
            Prompt.append(f'\t<DOCUMENT_{i}>\n\n')
            Prompt.append(open(f'{Folder}{os.sep}MainContributionCatalystDetails_{i}.txt', 'r', encoding='UTF8').read())
            Prompt.append(f'\n\n\t</DOCUMENT_{i}>\n')
        Prompt.append(END)
        Prompt = ''.join(Prompt)
        if os.path.exists(Folder) and not os.path.exists(f'{Folder}{os.sep}MainContributionCatalystDetails.txt') :
            open(f'{Folder}{os.sep}PromptAnswerIntegrationMainContributionCatalystDetails.txt', 'w', encoding='UTF8').write(Prompt)
            prompts_to_check.append((Folder, Prompt))
GetResponseConcurrent(prompts_to_check)
