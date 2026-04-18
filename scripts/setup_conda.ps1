param(
    [string]$EnvName = "gridrag"
)

$ErrorActionPreference = "Stop"

Write-Host "==> 检查 conda"
conda --version | Out-Host

Write-Host "==> 创建或更新环境: $EnvName"
$existing = conda env list | Select-String -Pattern "^\s*$EnvName\s"
if ($existing) {
    conda env update -n $EnvName -f environment.yml --prune | Out-Host
}
else {
    conda env create -f environment.yml | Out-Host
}

Write-Host "==> 安装前端依赖"
Push-Location frontend
try {
    npm install | Out-Host
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "环境准备完成。"
Write-Host "激活命令: conda activate $EnvName"
Write-Host "后端启动: cd backend; alembic upgrade head; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Write-Host "前端启动: cd frontend; npm run dev"

