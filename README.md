# Conversations at Scale: Robust AI-led Interviews

__https://ssrn.com/abstract=4974382__

This repository contains code for an interview platform to conduct AI-led interviews in research studies as well as notebooks for the AI-assisted analysis of the resulting transcripts. Conducting and analysing interviews is supported for large language models (LLMs) from OpenAI, Anthropic, and Google, as well as various open-source/weight models via Microsoft Azure. __All content in this repository is strictly for non-commercial research only; please refer to the [licence section](#3-data-and-licence) for further details.__

For a comprehensive discussion on how to set up and analyse AI-led interviews in your research studies, you can follow this readme and the linked tutorials such as the one on how to integrate interviews into online surveys [here](tutorial-online-interviews.md) or on how to analyse transcripts [here](analysis/README.md). You may also find these additional [video tutorials](https://www.youtube.com/playlist?list=PLEKqeUuYDSq-O1niu2Kqm0FGa0mMgYRx7) helpful for details. If you have remaining questions about the repository, please open an issue at https://github.com/friedrichgeiecke/interviews/issues.


## Table of contents

- [1. AI-led interviews](#1-ai-led-interviews)
  - [1.1 Testing AI-led interviews within minutes](#11-testing-ai-led-interviews-within-minutes)
  - [1.2 Full interview platform](#12-full-interview-platform)
    - [1.2.1 Local setup](#121-local-setup)
    - [1.2.2 Cloud setup for research studies including online surveys](#122-cloud-setup-for-research-studies-including-online-surveys)
- [2. AI-assisted transcript analysis](#2-ai-assisted-transcript-analysis)
- [3. Data and licence](#3-data-and-licence)
- [4. Paper](#4-paper)

## 1. AI-led interviews

There are two options to explore and run the AI-led interviews discussed in the paper.

### 1.1 Testing AI-led interviews within minutes

To try out your own ideas for interviews within minutes and without the need to install Python, see https://colab.research.google.com/drive/1sYl2BMiZACrOMlyASuT-bghCwS5FxHSZ (requires obtaining an API key)

### 1.2 Full interview platform

### 1.2.1 Local setup

Testing the full interview platform locally on your computer in Python takes around 1h from scratch with the following steps. The platform is built using the library `streamlit` and supports various language models APIS as well as text-based and voice-based interviews.

- Download miniconda from https://www.anaconda.com/docs/getting-started/miniconda/install and install it (skip if `conda` is already installed)
- Download this repository by clicking Code -> Download ZIP, extract the ZIP file, and move the resulting folder to a convenient location on your computer
- Obtain an API key from https://platform.openai.com or https://www.anthropic.com/api or https://ai.google.dev or https://ai.azure.com (for Azure, individual models have to be deployed in addition to obtaining an API key. You can click on "+ Create new" -> "Azure AI Foundry resource" -> "Create" -> "Models + endpoints" -> "Deploy model" -> "Deploy base model". Then choose from a range of proprietary and open-source models. Click on "Create resources and deploy". After some wait, copy the API key and select "SDK -> Azure Inference API" to copy the endpoint URL, and API version)
- Paste your API key (+ endpoint URL and API version for Azure) into the file `/.streamlit/secrets.toml` (this requires making hidden folders visible: `CMD + Shift + .` on Mac, `Ctrl + Shift + .` on Windows). __Ensure that the file `/.streamlit/secrets.toml` containing your API keys is not accidentally shared in a public repository.__
- In `config.py`:
  - Set the API and name of the language model you would like to use for the interview 
  - Adjust the interview outline to the topics you would like to cover
  - Set other variables such as text and voice input options
  - Add additional API arguments via 'ADDITIONAL_API_KWARGS' if needed or leave blank (some models may e.g. require additional reasoning parameters)
- In Terminal (Mac) or Anaconda Prompt (Windows), navigate to the repository with `cd`
   ```bash
   cd "where/you/saved/the/repository"
   ```
- Once in the folder, create the `interviews` environment from the .yml file by typing in the terminal
   ```bash
   conda env create -f interviewsenv.yml
   ```
  and confirming with Enter. This environment contains Python and all libraries necessary to run the interview platform and analysis; it only has to be created once. You can ignore the file `requirements.txt`, which will only be used by Azure web applications as discussed in the [tutorial on online interviews](tutorial-online-interviews.md).
- Next, activate the environment with
   ```bash
   conda activate interviews
   ```
- Lastly, to start the main interview platform (which features a text-based interviewer and both text and voice input options for the respondent), run:
   ```bash
   streamlit run interview.py
   ```
- For an alternative interview platform with a voice-based interviewer and also only voice input for the respondent, run `streamlit run full_voice_interview.py` instead. Rather than simply passing the text LLM output through a separate text-to-speech model, this voice interview uses a recent multimodal model which generates sound directly. Such models may e.g. adjust intonation endogenously depending on the conversation content. Unlike the main interview platform, `full_voice_interview.py` currently only supports the OpenAI API. Before running this voice interview platform, make sure to change the following options in `config.py`:
   ```python
   API = "openai"
   MODEL = "gpt-audio-2025-08-28" # or another audio-capable model
   ```

### 1.2.2 Cloud setup for research studies including online surveys

After testing the interview platform locally, it can be hosted on cloud instances for easy access by respondents in research studies. The following detailed [tutorial](tutorial-online-interviews.md) describes step by step how AI-led interviews can be hosted online and be integrated into other survey components.

## 2. AI-assisted transcript analysis

Please refer to the separate folder `analysis` for code and [discussion](analysis/README.md) on how interview transcripts can be analysed using LLMs.

## 3. Data and licence

### Data

The platform in its current form works with language model APIs from OpenAI, Anthropic, Google, and Microsoft Azure. Similarly to when using common tools like ChatGPT, Claude, Gemini, or others, the input data is thereby sent to the API providers to compute answers. These providers process the data under their terms of use, privacy policies, and data-retention settings, which need to be reviewed before studies are undertaken. Any study that uses this code needs to ensure to comply with all applicable data-protection laws and research ethics requirements (for example, institutional review board / ethics committee approvals), and to flag to respondents as part of consent forms that their interview data will be sent to third-party AI providers for computing interview responses and for analysing transcripts. It is the responsibility of researchers to ensure that all necessary approvals and consents are in place before conducting any studies using this platform.

### Licence

#### Code

All __source code__ in this repository is licensed under the __PolyForm Noncommercial License 1.0.0__.

You may use, modify, and distribute the code exclusively for non-commercial purposes. See [LICENCE-CODE](LICENCE-CODE) for the full licence text, or visit: https://polyformproject.org/licenses/noncommercial/1.0.0

#### Documentation

All __non-code content__ in this repository—such as README files, Markdown documentation, written explanations, and text in Jupyter notebooks—is licensed under the __Creative Commons Attribution–NonCommercial 4.0 International License (CC BY-NC 4.0)__.

You may share and adapt this content for non-commercial purposes, provided appropriate attribution is given. See [LICENCE-DOCS](LICENCE-DOCS) for the full licence text, or visit: https://creativecommons.org/licenses/by-nc/4.0/

#### Summary

| Component     | Licence                      |
|---------------|------------------------------|
| Source code   | PolyForm Noncommercial 1.0.0 |
| Documentation | CC BY-NC 4.0                 |

## 4. Paper

The paper discusses the interview and analysis methods from this repository in detail. It is available at [https://ssrn.com/abstract=4974382](https://ssrn.com/abstract=4974382) and can be cited with the following BibTex entry:

```
@article{geieckejaravel2026,
  title={Conversations at Scale: Robust AI-led Interviews},
  author={Geiecke, Friedrich and Jaravel, Xavier},
  url={https://ssrn.com/abstract=4974382},
  year={2026}
}
```
