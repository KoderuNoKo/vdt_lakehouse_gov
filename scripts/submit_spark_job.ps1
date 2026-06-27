<#
.SYNOPSIS
    Zip the entire spark_jobs project and submit a Spark job to the spark-master container.

.DESCRIPTION
    1. Builds project.zip from /opt/spark/jobs/ inside the spark-master container
       (using Python's zipfile — no external 'zip' binary required).
    2. Submits the specified job via spark-submit with --py-files project.zip.

.PARAMETER JobFile
    Relative path to the Python job file to submit
    (e.g. ingest_data/ingest_csv.py, pipelines/metadata_ingestion.py).
    The path is relative to src/spark_jobs/ (mounted at /opt/spark/jobs/ in the container).

.EXAMPLE
    .\scripts\submit_spark_job.ps1 ingest_data/ingest_csv.py
    .\scripts\submit_spark_job.ps1 pipelines/metadata_ingestion.py
    .\scripts\submit_spark_job.ps1 test_conns.py
#>

param(
    [Parameter(Mandatory = $true, Position = 0,
               HelpMessage = "Relative path to the job file (e.g. ingest_data/ingest_csv.py)")]
    [string]$JobFile
)

# ── Constants ────────────────────────────────────────────────────────────────
$Container   = "spark-master"
$JobsDir     = "/opt/spark/jobs"
$ZipPath     = "/tmp/project.zip"
$SparkMaster = "spark://spark-master:7077"

# ── Preflight checks ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Spark Job Submission" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verify the container is running
$running = docker inspect -f '{{.State.Running}}' $Container 2>$null
if ($running -ne "true") {
    Write-Host "[ERROR] Container '$Container' is not running." -ForegroundColor Red
    Write-Host "        Start it with: docker compose up -d" -ForegroundColor Yellow
    exit 1
}

# Verify the job file exists inside the container
docker exec $Container test -f "$JobsDir/$JobFile"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Job file not found: $JobsDir/$JobFile" -ForegroundColor Red
    Write-Host "        Available jobs:" -ForegroundColor Yellow
    docker exec $Container find $JobsDir -name "*.py" -not -path "*__pycache__*" -printf "          %P\n"
    exit 1
}

Write-Host "[INFO]  Job file : $JobFile" -ForegroundColor Green
Write-Host "[INFO]  Container: $Container" -ForegroundColor Green
Write-Host ""

# ── Step 1: Zip the entire project directory ─────────────────────────────────
Write-Host "[1/2] Zipping project..." -ForegroundColor Yellow

# Use Python's zipfile to create the archive (zip CLI may not be installed).
# Zips all .py files under /opt/spark/jobs/, skipping __pycache__ and .pyc.
# Archive paths are relative to $JobsDir so imports resolve correctly.
$zipScript = @"
import zipfile, os
zip_path = '$ZipPath'
jobs_dir = '$JobsDir'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(jobs_dir):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            if not f.endswith('.py'):
                continue
            full = os.path.join(root, f)
            arcname = os.path.relpath(full, jobs_dir)
            zf.write(full, arcname)
            print(f'  + {arcname}')
print(f'\nCreated {zip_path}')
"@

docker exec $Container python3 -c $zipScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to create project.zip" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ── Step 2: Submit the Spark job ─────────────────────────────────────────────
Write-Host "[2/2] Submitting job..." -ForegroundColor Yellow
Write-Host ""

# Merge stderr into stdout so Spark logs and Python tracebacks appear in order.
docker exec -i $Container /opt/spark/bin/spark-submit `
    --master $SparkMaster `
    --py-files $ZipPath `
    "$JobsDir/$JobFile" 2>&1

$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Job completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  Job failed (exit code: $exitCode)" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

exit $exitCode
