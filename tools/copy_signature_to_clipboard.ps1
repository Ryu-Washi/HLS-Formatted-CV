# Puts config/signature.html on the Windows clipboard as rich HTML (CF_HTML),
# so it can be pasted straight into the Outlook web signature editor, Outlook
# desktop, or Word with the logo + gold rule + colours intact.
#
# Run:  powershell.exe -STA -ExecutionPolicy Bypass -File tools\copy_signature_to_clipboard.ps1

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$sigPath = Join-Path $root 'config\signature.html'
if (-not (Test-Path $sigPath)) { throw "Not found: $sigPath" }

$fragment = Get-Content -Raw -Encoding UTF8 $sigPath
$pre  = "<html><body><!--StartFragment-->"
$post = "<!--EndFragment--></body></html>"

$enc = [System.Text.Encoding]::UTF8
# Header has fixed width (10-digit zero-padded numbers) so its byte length is constant.
$headerTemplate = "Version:0.9`r`nStartHTML:{0:0000000000}`r`nEndHTML:{1:0000000000}`r`nStartFragment:{2:0000000000}`r`nEndFragment:{3:0000000000}`r`n"
$headerLen   = $enc.GetByteCount(($headerTemplate -f 0,0,0,0))
$startHtml   = $headerLen
$startFrag   = $headerLen + $enc.GetByteCount($pre)
$endFrag     = $startFrag + $enc.GetByteCount($fragment)
$endHtml     = $endFrag  + $enc.GetByteCount($post)
$cfHtml = ($headerTemplate -f $startHtml, $endHtml, $startFrag, $endFrag) + $pre + $fragment + $post

$plain = @"
Washirawish (Ryu) Raweerojthakul
Founder & Consulting Partner - HLS Bridge Advisory Co., Ltd.
M: +66 81-135-7286
Connect with me on LinkedIn: https://www.linkedin.com/in/washirawish-ryu-raweerojthakul-a8716b86/
"@

Add-Type -AssemblyName System.Windows.Forms
$data = New-Object System.Windows.Forms.DataObject
$data.SetData([System.Windows.Forms.DataFormats]::Html, $cfHtml)
$data.SetData([System.Windows.Forms.DataFormats]::UnicodeText, $plain)
[System.Windows.Forms.Clipboard]::SetDataObject($data, $true)

Write-Host "Signature copied to clipboard as rich HTML ($($enc.GetByteCount($cfHtml)) bytes)."
Write-Host "Now: click in the Outlook 'Edit signature' box, select-all, delete, then Ctrl+V, then Save."
