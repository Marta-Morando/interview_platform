# Transcript Analysis

__Conversations at Scale: Robust AI-led Interviews (https://ssrn.com/abstract=4974382)__

The Jupyter notebooks in this folder outline a two-step approach for the AI-assisted analysis of transcripts.

1. __Hypothesis generation (notebook `01-hypothesis-generation.ipynb`)__

2. __Labelling (notebook `02-labelling.ipynb`)__

For a detailed discussion, please refer to the notebooks and to Section 2.3 of the paper. While the notebooks allow for easy addition of explanations in markdown text, the relevant code can be stored in .py modules for use in research studies.

__Please also refer to the main [README.md](../README.md) for full details such as the licences which apply to the entire repository including transcript analysis.__

To run the two notebooks locally, simply install Python and the VS Code editor (or other editors such as [JupyterLab](https://jupyter.org/install)):

- Download Miniconda from https://www.anaconda.com/docs/getting-started/miniconda/install and install it (skip if already installed for the interview dashboard or otherwise)
- Install VS Code from https://code.visualstudio.com
- Install the VS Code Python extension and briefly review how to run code in Jupyter notebooks (for details, see e.g.: https://youtu.be/suAkMeWJ1yE?si=lpQIDNkrPpJbHInZ)
- Download this repository by clicking Code -> Download ZIP, extract the ZIP file, and move the resulting folder to a convenient location on your computer
- Obtain an API key from https://platform.openai.com or https://www.anthropic.com/api or https://ai.google.dev or https://ai.azure.com (for Azure, individual models have to be deployed in addition to obtaining an API key. You can click on "+ Create new" -> "Azure AI Foundry resource" -> "Create" -> "Models + endpoints" -> "Deploy model" -> "Deploy base model". Then choose from a range of proprietary and open-source models. Click on "Create resources and deploy". After some wait, copy the API key and select "SDK -> Azure Inference API" to copy the endpoint URL, and API version)
- In the repository's `analysis` folder on your computer, paste the API key that you would like to use in the file `details.py`. __Ensure that the file `details.py` containing your API keys is not accidentally shared in a public repository.__
- If you have not already created the `interviews` environment from the .yml file when running the interview platform locally, navigate to the repository folder with `cd` in Terminal (Mac) or Anaconda Prompt (Windows), write `conda env create -f interviewsenv.yml`, and confirm with Enter. This environment installs Python and all libraries necessary to run the interview platform and text analysis; it only has to be created once. You can ignore the file `requirements.txt`, which will only be used by Azure web applications as discussed in the [tutorial on online interviews](../tutorial-online-interviews.md).
- Open either the `01-hypothesis-generation.ipynb` or `02-labelling.ipynb` notebook in VS Code
- In the notebook, click on "Select Kernel" in the top right corner, and choose the environment called `interviews` which was just installed (this ensures that the code uses the correct Python installation and library versions)
- Follow the instructions in the respective notebook to run the code step by step