param(
    [Parameter(Mandatory = $true)]
    [string]$InputDocx,

    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot,

    [string]$OutputDocx,

    [string]$DiagramRoot = (Join-Path $PSScriptRoot '..\artifacts\strongwine-oop-essay\plantuml_overhaul'),

    [string]$ValidationProfile,

    [switch]$Prepare,

    [switch]$UpdateVisuals,

    [switch]$RepairCaptionSequence
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$inputPath = (Resolve-Path -LiteralPath $InputDocx).Path
$projectPath = (Resolve-Path -LiteralPath $ProjectRoot).Path
$diagramPath = (Resolve-Path -LiteralPath $DiagramRoot).Path
$env:PYTHONPATH = Join-Path $repoRoot 'src'
$env:PYTHONIOENCODING = 'utf-8'
$pythonExe = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) { throw 'Python was not found. Create the project .venv or install Python.' }
    $pythonExe = $pythonCommand.Source
}

function Invoke-QACommand {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$ReportPath
    )
    Write-Host "== $Name =="
    $stderrPath = "$ReportPath.stderr.log"
    $commandOutput = & $pythonExe @Arguments 2> $stderrPath
    $commandExitCode = $LASTEXITCODE
    $commandOutput | Set-Content -LiteralPath $ReportPath -Encoding utf8
    Write-Host "Exit code: $commandExitCode. stdout saved to $ReportPath; stderr saved to $stderrPath"
    if ($commandExitCode -ne 0) {
        throw "$Name failed with exit code $commandExitCode. See $ReportPath"
    }
}

function Update-WordFields {
    param([Parameter(Mandatory = $true)][string]$Path)
    $word = $null
    $document = $null
    try {
        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        $word.DisplayAlerts = 0
        $document = $word.Documents.Open($Path, $false, $false, $false)
        foreach ($story in $document.StoryRanges) {
            $current = $story
            while ($null -ne $current) {
                $null = $current.Fields.Update()
                $current = $current.NextStoryRange
            }
        }
        $document.Repaginate()
        foreach ($table in $document.TablesOfContents) { $null = $table.Update() }
        foreach ($table in $document.TablesOfFigures) { $null = $table.Update() }
        $document.Repaginate()
        $document.Save()
        Write-Host "Updated and saved Word fields in $Path"
    } finally {
        if ($document) { $document.Close(0) }
        if ($word) { $word.Quit() }
    }
}

$selectedModes = @()
if ($Prepare) { $selectedModes += 'Prepare' }
if ($UpdateVisuals) { $selectedModes += 'UpdateVisuals' }
if ($RepairCaptionSequence) { $selectedModes += 'RepairCaptionSequence' }
if ($selectedModes.Count -gt 1) {
    throw 'Use only one of -Prepare, -UpdateVisuals, or -RepairCaptionSequence per run.'
}

if ($RepairCaptionSequence) {
    if (-not $OutputDocx) {
        throw '-OutputDocx is required when -RepairCaptionSequence is used.'
    }
    $outputPath = [System.IO.Path]::GetFullPath($OutputDocx)
    if (Test-Path -LiteralPath $outputPath) {
        throw "Refusing to overwrite existing output: $outputPath"
    }
    Invoke-QACommand -Name 'Repair reviewed caption sequence field in an output copy' `
        -Arguments @(
            (Join-Path $repoRoot 'scripts\strongwine_course_essay.py'), 'repair-caption-sequence',
            '--input', $inputPath, '--output', $outputPath,
            '--project-root', $projectPath, '--diagram-root', $diagramPath,
            '--report', "$outputPath.caption-repair.json"
        ) -ReportPath "$outputPath.caption-repair.log"
    Update-WordFields -Path $outputPath
    Invoke-QACommand -Name 'Restore authored raster bytes after Word field update' `
        -Arguments @(
            (Join-Path $repoRoot 'scripts\strongwine_course_essay.py'), 'restore-media',
            '--input', $outputPath, '--project-root', $projectPath, '--diagram-root', $diagramPath,
            '--report', "$outputPath.media-restore.json"
        ) -ReportPath "$outputPath.media-restore.log"
    $docxPath = $outputPath
} elseif ($UpdateVisuals) {
    if (-not $OutputDocx) {
        throw '-OutputDocx is required when -UpdateVisuals is used.'
    }
    $outputPath = [System.IO.Path]::GetFullPath($OutputDocx)
    if (Test-Path -LiteralPath $outputPath) {
        throw "Refusing to overwrite existing output: $outputPath"
    }
    $reportPath = "$outputPath.visual-update.json"
    Invoke-QACommand -Name 'Refresh verified diagrams and wireframes in an output copy' `
        -Arguments @(
            (Join-Path $repoRoot 'scripts\strongwine_course_essay.py'), 'update-visuals',
            '--input', $inputPath, '--output', $outputPath,
            '--project-root', $projectPath, '--diagram-root', $diagramPath,
            '--report', $reportPath
        ) -ReportPath "$outputPath.visual-update.log"
    Update-WordFields -Path $outputPath
    Invoke-QACommand -Name 'Restore authored raster bytes after Word field update' `
        -Arguments @(
            (Join-Path $repoRoot 'scripts\strongwine_course_essay.py'), 'restore-media',
            '--input', $outputPath, '--project-root', $projectPath, '--diagram-root', $diagramPath,
            '--report', "$outputPath.media-restore.json"
        ) -ReportPath "$outputPath.media-restore.log"
    $docxPath = $outputPath
} elseif ($Prepare) {
    if (-not $OutputDocx) {
        throw '-OutputDocx is required when -Prepare is used.'
    }
    $outputPath = [System.IO.Path]::GetFullPath($OutputDocx)
    if (Test-Path -LiteralPath $outputPath) {
        throw "Refusing to overwrite existing output: $outputPath"
    }
    $reportPath = "$outputPath.prepare.json"
    Invoke-QACommand -Name 'Project diagram audit, render, and DOCX preparation' `
        -Arguments @(
            (Join-Path $repoRoot 'scripts\strongwine_course_essay.py'), 'prepare',
            '--input', $inputPath, '--output', $outputPath,
            '--project-root', $projectPath, '--diagram-root', $diagramPath,
            '--report', $reportPath
        ) -ReportPath "$outputPath.prepare.log"
    Update-WordFields -Path $outputPath
    Invoke-QACommand -Name 'Restore authored raster bytes after Word field update' `
        -Arguments @(
            (Join-Path $repoRoot 'scripts\strongwine_course_essay.py'), 'restore-media',
            '--input', $outputPath, '--project-root', $projectPath, '--diagram-root', $diagramPath,
            '--report', "$outputPath.media-restore.json"
        ) -ReportPath "$outputPath.media-restore.log"
    $docxPath = $outputPath
} else {
    $docxPath = $inputPath
}

$docxPath = (Resolve-Path -LiteralPath $docxPath).Path
$docxHash = (Get-FileHash -LiteralPath $docxPath -Algorithm SHA256).Hash.ToLowerInvariant()
$docxStem = [System.IO.Path]::GetFileNameWithoutExtension($docxPath)
$runId = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$qaRoot = Join-Path (Split-Path -Parent $docxPath) ("strongwine-course-essay-qa-$docxStem-" + $docxHash.Substring(0, 12) + "-$runId")
New-Item -ItemType Directory -Path $qaRoot -Force | Out-Null

Invoke-QACommand -Name 'Read-only StrongWine diagram and DOCX audit' `
    -Arguments @(
        (Join-Path $repoRoot 'scripts\strongwine_course_essay.py'), 'audit',
        '--input', $docxPath, '--project-root', $projectPath,
        '--diagram-root', $diagramPath,
        '--report', (Join-Path $qaRoot 'strongwine-audit.json')
    ) -ReportPath (Join-Path $qaRoot 'strongwine-audit.log')

Invoke-QACommand -Name 'WordAssistant environment doctor' `
    -Arguments @('-m', 'wordassistant.cli', 'doctor', '--json') `
    -ReportPath (Join-Path $qaRoot 'wordassistant-doctor.json')

Invoke-QACommand -Name 'WordAssistant capabilities' `
    -Arguments @('-m', 'wordassistant.cli', 'capabilities', '--json') `
    -ReportPath (Join-Path $qaRoot 'wordassistant-capabilities.json')

Invoke-QACommand -Name 'DOCX summary inspection' `
    -Arguments @('-m', 'wordassistant.cli', 'inspect', $docxPath, '--summary', '--json') `
    -ReportPath (Join-Path $qaRoot 'wordassistant-inspect.json')

if ($ValidationProfile) {
    Invoke-QACommand -Name "DOCX validation ($ValidationProfile profile)" `
        -Arguments @('-m', 'wordassistant.cli', 'validate', $docxPath, '--profile', $ValidationProfile, '--json') `
        -ReportPath (Join-Path $qaRoot 'wordassistant-validate.json')
} else {
    '{"status":"NOT_RUN","reason":"No course-essay rubric/profile was supplied; the generic profile is not used as a grading standard."}' |
        Set-Content -LiteralPath (Join-Path $qaRoot 'wordassistant-validate.json') -Encoding utf8
    Write-Host '== DOCX validation == NOT RUN (no course rubric/profile supplied; generic profile excluded)'
}

Invoke-QACommand -Name 'Page-number structure' `
    -Arguments @('-m', 'wordassistant.cli', 'page-number', 'inspect', $docxPath, '--json') `
    -ReportPath (Join-Path $qaRoot 'wordassistant-page-numbers.json')

$renderRoot = Join-Path $qaRoot 'word-render'
Invoke-QACommand -Name 'Microsoft Word render' `
    -Arguments @('-m', 'wordassistant.cli', 'render', $docxPath, '--engine', 'word', '--outdir', $renderRoot, '--json') `
    -ReportPath (Join-Path $qaRoot 'wordassistant-render.json')

$renderResult = Get-Content -LiteralPath (Join-Path $qaRoot 'wordassistant-render.json') -Raw | ConvertFrom-Json
$pdfHash = (Get-FileHash -LiteralPath $renderResult.pdf -Algorithm SHA256).Hash.ToLowerInvariant()
$visualPageRoot = Join-Path $renderRoot ("review-pages-" + $pdfHash.Substring(0, 12))
Invoke-QACommand -Name 'Rendered-page previews and cover-frame pixel audit' `
    -Arguments @(
        (Join-Path $repoRoot 'scripts\render_strongwine_qa_pages.py'),
        '--pdf', $renderResult.pdf,
        '--outdir', $visualPageRoot,
        '--report', (Join-Path $qaRoot 'visual-page-audit.json'),
        '--all-pages',
        '--pages', '1', '2', '3', '13',
        '--anchor', 'Hình 3.1: Sơ đồ lớp kiến trúc phân tầng',
        '--anchor', 'Hình 3.2: Mô hình miền cốt lõi StrongWine',
        '--anchor', 'Hình 3.19.c: Sơ đồ luồng xác thực và kiểm toán mã bảo mật giao hàng OTP',
        '--anchor', 'Hình 4.0: Sơ đồ phân rã màn hình phân hệ Khách hàng',
        '--anchor', 'Hình 4.0b: Sơ đồ Use Case chi tiết phân hệ Khách hàng',
        '--anchor', 'Hình 4.4: Sơ đồ hoạt động (Activity Diagram) quy trình Checkout',
        '--anchor', 'Hình 4.5: Sơ đồ tuần tự (Sequence Diagram) xử lý Đặt hàng',
        '--anchor', 'Hình 5.0: Sơ đồ phân rã màn hình phân hệ Quản trị',
        '--anchor', 'Hình 5.0b: Sơ đồ Use Case chi tiết phân hệ Quản trị',
        '--anchor', 'Hình 5.1: Sơ đồ hoạt động (Activity Diagram) Quản trị viên thêm rượu',
        '--anchor', 'Hình 5.2: Sơ đồ tuần tự Admin tạo rượu qua form MVC',
        '--anchor', 'Hình 5.3: Wireframe Bảng điều khiển quản trị Dashboard KPI',
        '--anchor', 'Hình 5.4: Wireframe Quản lý danh mục và sản phẩm rượu vang',
        '--anchor', 'Hình 5.5: Wireframe Thêm mới và chỉnh sửa thông tin rượu',
        '--anchor', 'Hình 4.1: Wireframe Trang chủ sàn thương mại điện tử StrongWine',
        '--anchor', 'Hình 4.5: Wireframe Giao diện thanh toán đơn hàng Checkout',
        '--anchor', 'Hình 4.6: Wireframe Chi tiết đơn hàng và theo dõi vận chuyển',
        '--anchor', 'Hình 4.2: Wireframe Danh mục rượu và bộ lọc đa tiêu chí',
        '--anchor', 'Hình 4.2.b: Giao diện trang chủ StrongWine',
        '--anchor', 'Hình 4.3: Wireframe Chi tiết sản phẩm rượu và tasting notes',
        '--anchor', 'Hình 4.7: Wireframe Đăng nhập và tạo tài khoản thành viên',
        '--anchor', 'Hình 4.8: Wireframe Biểu mẫu yêu cầu đặt lại mật khẩu bảo mật',
        '--anchor', 'Hình 4.4: Wireframe Quản lý giỏ hàng và cập nhật số lượng',
        '--anchor', 'Hình 4.9.b: Giao diện chi tiết đơn hàng và theo dõi giao nhận',
        '--anchor', 'Hình 5.7: Wireframe Quản lý tài khoản người dùng và phân quyền',
        '--anchor', 'Hình 5.8: Wireframe Quản lý danh sách nhân viên giao hàng Shipper',
        '--anchor', 'Hình 5.9: Wireframe Giám sát đơn hàng toàn sàn và trạng thái thanh toán',
        '--anchor', 'Hình 5.10: Wireframe Bảng quản trị tồn kho và điều phối chi nhánh',
        '--anchor', 'Hình 5.6: Wireframe Nhập danh mục rượu hàng loạt từ tệp Excel',
        '--anchor', 'Hình 5.10: Giao diện chỉnh sửa hồ sơ Shipper',
        '--anchor', 'Hình 6.1: Wireframe Bảng điều khiển công việc Shipper',
        '--anchor', 'Hình 6.2: Wireframe trạng thái xem chi tiết vận đơn trên bảng điều khiển Shipper',
        '--anchor', 'Hình 6.3: Wireframe trạng thái nhập OTP hoàn tất giao hàng trên bảng điều khiển Shipper',
        '--anchor', 'Hình 6.0: Sơ đồ phân rã màn hình phân hệ Giao hàng',
        '--anchor', 'Hình 6.0b: Sơ đồ Use Case chi tiết phân hệ Giao hàng',
        '--check-cover-borders'
    ) -ReportPath (Join-Path $qaRoot 'visual-page-audit.log')

Write-Host "QA reports: $qaRoot"
Write-Host "Rendered DOCX and selected review pages: $renderRoot"
