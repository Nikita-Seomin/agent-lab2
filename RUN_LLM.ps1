param(
    [Parameter(Mandatory=$true)][string]$BaseUrl,
    [Parameter(Mandatory=$true)][string]$Model,
    [Parameter(Mandatory=$true)][string]$ApiKey
)

$env:MAS_LLM_BASE_URL = $BaseUrl.TrimEnd('/')
$env:MAS_LLM_MODEL = $Model
$env:MAS_LLM_API_KEY = $ApiKey

python run.py --policy llm --split dev --mode all --out results_llm_dev
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Dev completed. Review it before running the frozen test experiment."
Write-Host "Test command: python run.py --policy llm --split test --mode all --repeats 2 --out results_llm_test"
