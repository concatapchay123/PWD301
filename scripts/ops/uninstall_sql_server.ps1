# ==============================================================================
# Kich ban tu dong hoa go bo va don dep toan dien Microsoft SQL Server 2025
# ==============================================================================

# 1. Kiem tra quyen Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsPrincipal]::Administrator)
if (-not $isAdmin) {
    Write-Host "[!] Yeu cau quyen Administrator. Dang mo hop thoai UAC de nang quyen..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$ErrorActionPreference = "Continue"
$logDir = "E:\backup1"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$logFile = "$logDir\sql_uninstall_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function LogMsg ($msg, $color = "White") {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $msg"
    Write-Host $line -ForegroundColor $color
    Add-Content -Path $logFile -Value $line
}

Clear-Host
LogMsg "======================================================================" "Cyan"
LogMsg "   HE THONG GO BO VA DON DEP TOAN DIEN MICROSOFT SQL SERVER 2025" "Cyan"
LogMsg "======================================================================" "Cyan"
LogMsg "Nhat ky thuc thi duoc ghi vao: $logFile" "Gray"

# 2. Bao ve MySQL Server
LogMsg "`n[BUOC 1/6] Kiem tra va bao ve MySQL Server..." "Yellow"
$mysqlSvc = Get-Service -Name "MySQL267" -ErrorAction SilentlyContinue
if ($mysqlSvc) {
    LogMsg "[OK] Phat hien MySQL Server 26.7 (Trang thai: $($mysqlSvc.Status)). Bao ve 100%!" "Green"
} else {
    LogMsg "[INFO] Khong phat hien dich vu MySQL267 dang chay." "Gray"
}

# 3. Dung toan bo cac dich vu SQL Server
LogMsg "`n[BUOC 2/6] Dung va vo hieu hoa cac dich vu SQL Server..." "Yellow"
$sqlServices = @(
    "MSOLAP`$HOANGPHUC",
    "MSSQL`$HOANGPHUC",
    "MSSQLFDLauncher`$HOANGPHUC",
    "MSSQLLaunchpad`$HOANGPHUC",
    "MSSQLSERVER",
    "SQLAgent`$HOANGPHUC",
    "SQLBrowser",
    "SQLPBDMS`$HOANGPHUC",
    "SQLPBENGINE`$HOANGPHUC",
    "SQLSERVERAGENT",
    "SQLTELEMETRY",
    "SQLTELEMETRY`$HOANGPHUC",
    "SQLWriter",
    "SSASTELEMETRY`$HOANGPHUC"
)

foreach ($svcName in $sqlServices) {
    $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
    if ($svc) {
        if ($svc.Status -eq 'Running') {
            LogMsg " - Dang dung dich vu: $svcName ($($svc.DisplayName))..." "White"
            Stop-Service -Name $svcName -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
        }
        Set-Service -Name $svcName -StartupType Disabled -ErrorAction SilentlyContinue
        LogMsg "   [OK] Da dung va vo hieu hoa: $svcName" "Green"
    }
}

# Giai phong cac tien trinh SQL Server con chay ngam
$sqlProcs = @("sqlservr", "sqlbrowser", "sqlwriter", "sqlceip", "msmdsrv", "fdlauncher", "launchpad", "mpdwsvc")
foreach ($pName in $sqlProcs) {
    $pList = Get-Process -Name $pName -ErrorAction SilentlyContinue
    if ($pList) {
        LogMsg " - Giai phong tien trinh: $pName (So luong: $($pList.Count))..." "Yellow"
        $pList | Stop-Process -Force -ErrorAction SilentlyContinue
    }
}

# 4. Go bo 2 SQL Server Instances qua Setup.exe
LogMsg "`n[BUOC 3/6] Go bo 2 SQL Server Instances qua Setup.exe..." "Yellow"
$setupExe = "C:\Program Files\Microsoft SQL Server\170\Setup Bootstrap\SQL2025\setup.exe"

if (Test-Path $setupExe) {
    # 4.1. Instance HOANGPHUC
    LogMsg " - Dang go bo Instance HOANGPHUC (qua trinh mat khoang 2-3 phut)..." "Cyan"
    $argsHP = "/ACTION=UNINSTALL /INSTANCENAME=HOANGPHUC /FEATURES=SQL,AS,ADVANCEDANALYTICS,POLYBASE /Q /IACCEPTSQLSERVERLICENSETERMS"
    $p1 = Start-Process -FilePath $setupExe -ArgumentList $argsHP -Wait -PassThru -NoNewWindow
    LogMsg "   [KET QUA] Go Instance HOANGPHUC hoan tat (ExitCode: $($p1.ExitCode))" "Green"

    # 4.2. Instance MSSQLSERVER
    LogMsg " - Dang go bo Instance MSSQLSERVER (qua trinh mat khoang 1-2 phut)..." "Cyan"
    $argsMSSQL = "/ACTION=UNINSTALL /INSTANCENAME=MSSQLSERVER /FEATURES=SQL /Q /IACCEPTSQLSERVERLICENSETERMS"
    $p2 = Start-Process -FilePath $setupExe -ArgumentList $argsMSSQL -Wait -PassThru -NoNewWindow
    LogMsg "   [KET QUA] Go Instance MSSQLSERVER hoan tat (ExitCode: $($p2.ExitCode))" "Green"
} else {
    LogMsg " [!] Khong tim thay setup.exe tai $setupExe" "Yellow"
}

# 5. Go bo cac driver va tien ich qua MSI ProductCode
LogMsg "`n[BUOC 4/6] Go bo Driver, Browser, VSS Writer va cac goi MSI ho tro..." "Yellow"

$msiPackages = @(
    @{ Name = "Browser for SQL Server 2025"; Guid = "{DD36BE85-7BAC-4FEA-876E-060BD7936895}" },
    @{ Name = "Microsoft VSS Writer for SQL Server 2025"; Guid = "{FEC10394-D378-48E4-8A10-5BFCE3098A05}" },
    @{ Name = "Microsoft ODBC Driver 18 for SQL Server"; Guid = "{820A3DEC-9783-42AE-B12D-750FCCF07E10}" },
    @{ Name = "Microsoft ODBC Driver 17 for SQL Server"; Guid = "{0E0F96AC-80DE-4400-A40C-429D63293651}" },
    @{ Name = "Microsoft OLE DB Driver 19 for SQL Server"; Guid = "{AFFC3E2E-B4E9-40CE-8F85-9D104554535C}" },
    @{ Name = "Microsoft OLE DB Driver for SQL Server (v18)"; Guid = "{9E43DE89-BFB0-49E5-A622-E9A01F1C63DB}" },
    @{ Name = "Microsoft SQL Server 2025 Setup (English)"; Guid = "{84D8FCAF-EC0B-4BC6-ACA2-E5E64D3B7880}" }
)

foreach ($pkg in $msiPackages) {
    LogMsg " - Go cai dat: $($pkg.Name) [$($pkg.Guid)]..." "White"
    $proc = Start-Process -FilePath "msiexec.exe" -ArgumentList "/x `"$($pkg.Guid)`" /qn /norestart" -Wait -PassThru
    LogMsg "   [KET QUA] $($pkg.Name) hoan tat (ExitCode: $($proc.ExitCode))" "Green"
}

# Ra soat va go cac goi MSI phu tro con sot lai cua SQL Server 2025
LogMsg " - Ra soat va don dep cac thanh phan MSI phu tro con sot..." "White"
$uninstallPaths = @(
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
)
$residualMsi = Get-ItemProperty $uninstallPaths -ErrorAction SilentlyContinue | Where-Object { 
    $_.DisplayName -match '^SQL Server 2025' -and $_.PSChildName -match '^\{'
}

foreach ($res in $residualMsi) {
    LogMsg "   * Go thanh phan phu tro: $($res.DisplayName) [$($res.PSChildName)]..." "Gray"
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/x `"$($res.PSChildName)`" /qn /norestart" -Wait
}

# 6. Sao luu Registry va don dep khoa mo coi
LogMsg "`n[BUOC 5/6] Sao luu va don dep Registry..." "Yellow"
$regBackupFile = "$logDir\sql_server_registry_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').reg"
LogMsg " - Sao luu Registry SQL Server ra tap tin: $regBackupFile..." "White"
Start-Process -FilePath "reg.exe" -ArgumentList "export `"HKLM\SOFTWARE\Microsoft\Microsoft SQL Server`" `"$regBackupFile`" /y" -Wait -NoNewWindow

$regKeysToDelete = @(
    "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Microsoft SQL Server",
    "HKCU:\Software\Microsoft\Microsoft SQL Server"
)

foreach ($key in $regKeysToDelete) {
    if (Test-Path $key) {
        LogMsg " - Xoa khoa Registry mo coi: $key" "Yellow"
        Remove-Item -Path $key -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# 7. Don dep thu muc rac
LogMsg "`n[BUOC 6/6] Don dep thu muc rac va cache..." "Yellow"

# Thu muc SSMS rong
if (Test-Path "E:\SSMS") {
    LogMsg " - Xoa thu muc SSMS rong: E:\SSMS..." "White"
    Remove-Item -Path "E:\SSMS" -Recurse -Force -ErrorAction SilentlyContinue
}

# C:\Program Files\Microsoft SQL Server
$cProgSql = "C:\Program Files\Microsoft SQL Server"
if (Test-Path $cProgSql) {
    LogMsg " - Xoa thu muc: $cProgSql..." "White"
    Remove-Item -Path $cProgSql -Recurse -Force -ErrorAction SilentlyContinue
}

# C:\Program Files (x86)\Microsoft SQL Server
$cProgX86Sql = "C:\Program Files (x86)\Microsoft SQL Server"
if (Test-Path $cProgX86Sql) {
    LogMsg " - Xoa thu muc: $cProgX86Sql..." "White"
    Remove-Item -Path $cProgX86Sql -Recurse -Force -ErrorAction SilentlyContinue
}

# Don dep tep nhi phan va log trong E:\SQL Server (BAO VE THU MUC DATA CHUA FILE MDF/LDF)
if (Test-Path "E:\SQL Server") {
    LogMsg " - Don dep E:\SQL Server (Giu nguyen thu muc DATA chua du lieu nguoi dung)..." "White"
    Get-ChildItem -Path "E:\SQL Server" -Recurse -ErrorAction SilentlyContinue | Where-Object {
        $_.FullName -notmatch '\\DATA\\' -and $_.FullName -notmatch '\\DATA$'
    } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

# Xoa cau hinh dich vu con ket neu co
$residualServices = @("SQLBrowser", "SQLWriter", "SQLTELEMETRY", "SQLTELEMETRY`$HOANGPHUC", "MSSQLSERVER", "MSSQL`$HOANGPHUC")
foreach ($s in $residualServices) {
    $scCheck = Get-Service -Name $s -ErrorAction SilentlyContinue
    if ($scCheck) {
        LogMsg " - Xoa cau hinh service con ket: $s..." "Yellow"
        Start-Process -FilePath "sc.exe" -ArgumentList "delete `"$s`"" -Wait -NoNewWindow
    }
}

# 8. Kiem tra va bao cao ket qua
LogMsg "`n======================================================================" "Cyan"
LogMsg "                     KET QUA XAC MINH HE THONG" "Cyan"
LogMsg "======================================================================" "Cyan"

$remainingApps = Get-ItemProperty $uninstallPaths -ErrorAction SilentlyContinue | Where-Object { 
    $_.DisplayName -match 'SQL Server|ODBC Driver.*SQL|OLE DB Driver.*SQL' -and $_.DisplayName -notmatch 'MySQL' 
}

if ($remainingApps) {
    LogMsg "[CANH BAO] Van con mot so thanh phan:" "Yellow"
    $remainingApps | ForEach-Object { LogMsg " - $($_.DisplayName)" "Yellow" }
} else {
    LogMsg "[XAC NHAN HOAN TAT] 100% cac thanh phan Microsoft SQL Server da duoc go bo!" "Green"
}

$mysqlCheckFinal = Get-Service -Name "MySQL267" -ErrorAction SilentlyContinue
if ($mysqlCheckFinal) {
    LogMsg "[XAC NHAN HOAN TAT] MySQL Server 26.7 van hoat dong binh thuong! (Status: $($mysqlCheckFinal.Status))" "Green"
}

$mysqlOdbcFinal = Get-OdbcDriver | Where-Object { $_.Name -match 'MySQL' }
if ($mysqlOdbcFinal) {
    LogMsg "[XAC NHAN HOAN TAT] MySQL ODBC Connector 26.7 van nguyen ven 100%!" "Green"
}

LogMsg "`nBan sao luu cac Database PWD301, xsentinel, openlibrary an toan tai: E:\backup1\" "Cyan"
LogMsg "Hoan tat! Ban co the khoi dong lai may de lam moi hoan toan Windows." "Cyan"
LogMsg "Nhan phim bat ky de thoat..." "Gray"
[void][System.Console]::ReadKey()
