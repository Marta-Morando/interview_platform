## Qualtrics survey modification

Use `qualtrics_modify_ai_survey.py` to locate the survey named `AI_survey` and add an AI interview launch block.

### Required environment variables

PowerShell:

```powershell
$env:QUALTRICS_API_TOKEN = "YOUR_TOKEN"
$env:QUALTRICS_BASE_URL = "https://YOUR_DATACENTER.qualtrics.com/API/v3"
```

### Dry run

```powershell
& 'C:\ProgramData\Anaconda3\envs\interviews\python.exe' scripts\qualtrics_modify_ai_survey.py `
  --survey-name AI_survey `
  --interview-url https://YOUR-INTERVIEW-APP-URL `
  --dry-run
```

### Apply the change

```powershell
& 'C:\ProgramData\Anaconda3\envs\interviews\python.exe' scripts\qualtrics_modify_ai_survey.py `
  --survey-name AI_survey `
  --interview-url https://YOUR-INTERVIEW-APP-URL
```

### Optional return URL

```powershell
& 'C:\ProgramData\Anaconda3\envs\interviews\python.exe' scripts\qualtrics_modify_ai_survey.py `
  --survey-name AI_survey `
  --interview-url https://YOUR-INTERVIEW-APP-URL `
  --return-url https://YOUR-QUALTRICS-RETURN-URL
```

### What the script does

- Finds the survey by exact name.
- Inserts embedded-data field definitions for `Random_ID`, `interview_username`, and `interview_status`.
- Creates a block called `AI Interview` if it does not already exist.
- Creates a descriptive text question with a direct launch link into the interview app.

### Still required in Qualtrics

Create or confirm a Survey Flow element that assigns `Random_ID`, for example:

```text
${rand://int/1:100000000}
```

The script defines the field, but it does not create the random-number assignment in Survey Flow.
