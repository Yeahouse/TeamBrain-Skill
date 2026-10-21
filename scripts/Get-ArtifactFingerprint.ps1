param([Parameter(Mandatory = $true)][string]$Path)
$ErrorActionPreference = 'Stop'
$item = Get-Item -LiteralPath $Path
if ($item.PSIsContainer) { throw 'Please supply a file, not a directory.' }
[pscustomobject]@{
    Name = $item.Name
    Bytes = $item.Length
    SHA256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
