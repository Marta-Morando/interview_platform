# Hosting Interviews on Cloud Platforms and Integrating Them into Online Surveys

This guide provides step-by-step instructions for setting up and running the interview platform online, and for integrating interviews into other survey components, e.g. those based on Qualtrics. The document discusses deployment via GitHub actions and Microsoft Azure as an example, but many other cloud providers can be used equally well. An additional video tutorial can be found [here](https://www.youtube.com/playlist?list=PLEKqeUuYDSq-O1niu2Kqm0FGa0mMgYRx7).

## Table of Contents

- [I. Setting up a GitHub repository for the interview platform](#i-setting-up-a-github-repository-for-the-interview-platform)
- [II. Setting up the interview platform on Azure](#ii-setting-up-the-interview-platform-on-azure)
- [III. Configuring GitHub and application](#iii-configuring-github-and-application)
- [IV. Finalising deployment](#iv-finalising-deployment)
- [V. Downloading the interview transcripts](#v-downloading-the-interview-transcripts)
- [VI. Scaling up the app's compute resources for larger studies](#vi-scaling-up-the-apps-compute-resources-for-larger-studies)
- [VII. Adding basic login details for respondents and integrating interviews into surveys such as Qualtrics](#vii-adding-basic-login-details-for-respondents-and-integrating-interviews-into-surveys-such-as-qualtrics)
  - [VII.1 Specifying usernames and passwords and sharing these with respondents separately](#vii1-specifying-usernames-and-passwords-and-sharing-these-with-respondents-separately)
  - [VII.2 Specifying and displaying usernames and passwords in a Qualtrics survey directly](#vii2-specifiying-and-displaying-usernames-and-passwords-in-a-qualtrics-survey-directly)
- [VIII. Shutting down interview dashboards after studies](#viii-shutting-down-interview-dashboards-after-studies)



## I. Setting up a GitHub repository for the interview platform

Additional resources: If helpful to review Git and Github before starting, see e.g. the documents at https://docs.github.com/en/get-started/start-your-journey or tutorials such as https://cs50.harvard.edu/web/weeks/1/

1. Create a new private GitHub repository.
    Navigate to https://github.com, create an account or log in, and create a new repository (e.g. called `interviews-online`).
2. Install Git on your computer: On Mac, type `git --version` into the terminal which should either show the current version or install Git. On Windows, download install the software from https://git-scm.com/download/win.
3. Clone (i.e. download) the repository to your local computer: In terminal (Mac) or the now installed Git Bash (Windows), navigate to the folder where you want to create your project. Run the following command in the terminal to download the empty repository to your computer:
   ```bash
   cd "where/you/want/to/save/the/repository"
   git clone https://github.com/<YOURGITHUBUSERNAME>/interviews-online.git
   ```
  
4. Download the repository `https://github.com/friedrichgeiecke/interviews` by clicking Code -> Download ZIP, extract the ZIP file, and move the resulting folder to a convenient location on your computer. Make hidden files visible on your computer (`CMD + Shift + .` on Mac, `Ctrl + Shift + .` on Windows), and copy the following files and folders into the root directory of your local repository downloaded in Step 3 (the `interviewsenv.yml` is not needed here as on the Azure cloud instance all libraries will be installed based on `requirements.txt`).
   - `.streamlit` folder (including the file `secrets.toml` with your API key and login credentials)
   - `interview.py`
   - `full_voice_interview.py`
   - `config.py`
   - `utils.py`
   - `requirements.txt`

5. In Terminal (Mac) or Git Bash (Windows), commit and push all copied files from your local directory to the remote GitHub repository:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push
   ```

## II. Setting up the interview platform on Azure

1. Sign in to the [Azure Portal](https://portal.azure.com/).
2. Click on **Create a resource**. 
3. Select **Web App**.
   - Create a new **Resource Group** (e.g., `interviews`).
   - Give the instance a name (will be part of the URL shared to the participants).
   - Select **Python 3.13** as the runtime stack.
   - Choose a region (e.g., `UK South`).
   - Keep **Zone redundancy disabled**.
4. Click on **Next: Databases**.
    - **No changes** needed here as the basic interview app works without a database (database functionality can be added to the application code where necessary).
5. Click on **Next: Deployment**.
   - Enable **Continuous Deployment**.
   - Link your GitHub account.
   - Choose the private repository you just created with the interview files.
   - Select the `main` branch (or the branch you're using).
6. Enable **Basic Authentication**: this allows to connect to the instance with a file transfer client later and download the transcripts.
7. Click on **Next: Networking**.
    - Keep **public access enabled**.
    - Keep **virtual network integration disabled**.
8. Click on **Next: Monitor + Secure**.
   - Enable or disable **App Insights**.
   - Enable **Microsoft Defender**.
9. Click on **Next: Tags**.
10. Click on **Next: Review + Create**.
11. Click on **Create**.
12. Wait for a while until the app is created successfully.

## III. Configuring GitHub and application

1. Go back to your **GitHub repository** on **GitHub**.
2. Click on **Actions**.
3. Wait for the workflow triggered by Azure to complete (it might take several minutes). If it fails, rerun it. If you get an error, check that all your interview files are located in the root directory of the repository (the folder `analysis` does not have to be copied for the interview platform).
4. Once successful (green tick visible), run `git pull` on your local machine to download the newest GitHub files that were just created by Azure and GitHub online.
5. In your local repository:
   - Make hidden files visible (`CMD + Shift + .` on Mac, `Ctrl + Shift + .` on Windows).
   - Open the folder `.github/workflows`.
   - Click on the `.yml` file.
   - Make sure the code runs on hidden files by having this section:
     ```yml
     # Optional: Add step to run tests here (PyTest, Django test suites, etc.)
      
      - name: Upload artifact for deployment jobs
        uses: actions/upload-artifact@v4
        with:
          name: python-app
          include-hidden-files: true 
          path: |
            .
            !venv/**
            !.git/**
            !.github/**
     ```
     
    - If not already done:
        - Open the file `.streamlit/secrets.toml`.
        - Add your API key and some login credentials.
        - In `config.py`, make the following changes:
            - Activate the basic login functionalty for online studies:
            ```python
             LOGINS = True 
             ```
            - Edit the folders to work with the cloud instance's file structure:
            ```python
            # Directories
            TRANSCRIPTS_DIRECTORY = "./transcripts/"
            METADATA_DIRECTORY = "./metadata/"
            BACKUPS_DIRECTORY = "./backups/"
            ```
            - with:
            ```python
            # Directories
            TRANSCRIPTS_DIRECTORY = "/home/interviews/transcripts/"
            METADATA_DIRECTORY = "/home/interviews/metadata/"
            BACKUPS_DIRECTORY = "/home/interviews/backups/"
            ```
    - Commit the changes and push them to GitHub:
      ```bash
         git add .
         git commit -m "Add .streamlit and update workflow"
         git push
      ```
6. Go back to your **GitHub repository** on **Github**.
    - Click on **Actions**.
    - Briefly wait a few minutes for the action triggered by the push to complete with a green tick. If it fails, simply rerun it.

## IV. Finalising deployment

1. Go back to the [Azure Portal](https://portal.azure.com/).
2. Select your **Web app** from your Recent resources.
3. Go on **Setting → Configuration → Stack settings** in the left dropdown menu.
4. Under **Startup Command**, enter:
   ```bash
   python -m streamlit run interview.py --server.port 8000 --server.address 0.0.0.0
   ```
   or, to run the full voice interview platform instead:
   ```bash
   python -m streamlit run full_voice_interview.py --server.port 8000 --server.address 0.0.0.0
   ```
5. **Save** this startup command and wait for 1-5 minutes.
6. Now, going to the app’s main page on Azure and clicking on the Default Domain should open the running interview application!

## V. Downloading the interview transcripts

If participants have completed interviews, transcripts are stored as `.txt` files in the `interviews/transcripts` folder on the cloud instance. In addition, the interview progress is stored continuously in the folder `interviews/backups` in JSON format and metadatdata is stored as `.txt` in the folder `interviews/metadata` at the end of the interview as well. 

**To be as simple and lightweight as possible, this version of the interview platform does not use a separate database to store data, but instead stores the transcripts, backups, and metadata on the cloud instance itself (data therefore has to be downloaded before cloud instances are shut down). It is discussed in detail in the following how to connect to the cloud instance via FTPS with a username and password and download these data. Researchers need to ensure that the data security and privacy requirements of their study are met when using these cloud instances for data storage. Otherwise they could e.g. extend the source code of this application to store the data in separate suitable (cloud) databases.**

1. Use a file-transfer client such as **Cyberduck**.
2. In the [Azure Portal](https://portal.azure.com/).
    - Go to the **app's main page**.
    - Go to **Deployment Center**.
    - Go to **FTPS Credentials**.
3. Copy **FTPS endpoint URL**, **username**, and **password** and paste into **Cyberduck’s Open Connection** tab (if disabled, FTPS can be enabled in **Configuration** → **Platform settings**).
4. Once connected to the app, go to the **root directory** in the Cyberduck window.
    - Click on the folder `interviews`.
    - Click on the folder `transcripts`.
    - Download the transcripts. These two folders should become visible after logging into the app via the Azure URL (default domain) with one of the non-test credentials and completing one interview.
    -  Additional metadata for each interview can then be found in the `metadata` folder.

## VI. Scaling up the app's compute resources for larger studies

1. Go to your **app's main page** on Azure.
2. Select a larger instance from the **Production settings** (key parameters are the virtual CPUs and memory settings). *To test the app or use it with a few users, Basic B2 is typically sufficient.*

## VII. Adding basic login details for respondents and integrating interviews into surveys such as Qualtrics

When hosting the interview platform on a cloud instance with public URL, it is advisable to add at least some simple login functionality to participate in the interview while the platform is online for the duration of a respective study. At the end of a study, platforms should be shut down again (see [VIII.](#viii-shutting-down-interview-dashboards-after-studies)). __Note that the following respondent logins are very basic (for further details see also `utils.py`). To add advanced respondent logins and authentication, researchers could modify the source code to feature authentication such as https://docs.streamlit.io/develop/concepts/connections/authentication.__ With the simple respondent logins discussed here, usernames and passwords can e.g. be shared in two ways. The second approach additionallys allows integrating AI-led interviews with further closed- or open-ended survey questions created with platforms such as Qualtrics.

First, to turn on the basic login functionality, set `LOGINS = True` in `config.py`.

### VII.1 Specifying usernames and passwords and sharing these with respondents separately

Custom usernames and passwords can easily be added to `.streamlit/secrets.toml` (see examples in the file; this requires making hidden files visible `CMD + Shift + .` on Mac or `Ctrl + Shift + .` on Windows). These username/password combinations can then be shared with survey participants to log in. During an interview, partial transcripts will be restored if an applicant logs in again. As soon as the interview has been completed, no further login and interview attempts are possible with the particular username to ensure transcripts are not overwritten.

### VII.2 Specifying and displaying usernames and passwords in a Qualtrics survey directly

For the particular use case of integrating AI-led interview components into surveys such as Qualtrics, a crosswalk is needed between the interview username and the responses to additional survey questions. In addition, it is helpful to display username and password directly on a survey page. The following discusses one simple way to achieve this. 

When starting a Qualtrics survey, each respondent can be assigned a large random number as username, which means that the probability of two respondents obtaining the same username is approaching zero. If the password is made a basic function of an integer user name, it can easily be computed and displayed in the Qualtrics surveys in real time as well. In detail, the simple password for this login mode has the form `alpha + beta*username` where the parameters `alpha` and `beta` can be set by the researcher in `config.py` such that interview dashboard login screen will accept only passwords that result from this formula.

The following is a step-by-step explanation of this setup:

1. First, enable this type of login in `config.py` by additionally setting `RANDOM_IDS = True` (keep `LOGINS = True`).

2. **Create a Qualtrics account** and create a new survey with questions of your choice (e.g., demographics, etc.).

3. In the **Survey Flow** section, add a block to **Set Embedded Data** as the **first** element. Click on **Set a Value Now** and have a `Random_ID` generated by:

   ```
   ${rand://int/1:100000000}
   ```

   This ID will enable us to generate a unique identifier and link Qualtrics answers to interview transcripts.

4. **Create a survey page that invites the participant to the interview platform:**

   - Into this page of the Qualtrics survey, copy **the interview platform's URL**, and username and password variables. Assuming the default values alpha=123 and beta=5 from `config.py` for this tuturial (ensure to change these values in `config.py` before your study), a Qualtrics block may look like the following (whitespaces are required after `$e{` and before `}` for the password):

     ```
     You are going to be interviewed next.  
     Please click on the link and use the following login details:

     **[Link to the interview]**

     Username: ${e://Field/Random_ID}
     Password: $e{ 123 + e://Field/Random_ID * 5 }

     This is the main part of the survey and should take around 20 minutes.  
     To successfully complete this survey, please wait until the end of the interview  
     and do not close the interview browser window before it finishes.
     ```

4. **Publish and test** your Qualtrics survey by taking it yourself and joining the interview platform to ensure everything works correctly.

5. Once your participants have completed the survey, download the data from the **Data & Analysis** tab in Qualtrics.  
   This data contains a column `Random_ID` which allows linking survey responses to the transcripts downloaded in **Step V.** The corresponding transcripts from the cloud instance have the same Random_IDs as file names.


## VIII. Shutting down interview dashboards after studies

Once a study is completed, the interview dashboards can either be stopped by clicking on ⏹️ or also fully deleted with 🗑️ on the application's main page at the [Azure Portal](https://portal.azure.com/) (ensure to download all interview data from the instance before!).