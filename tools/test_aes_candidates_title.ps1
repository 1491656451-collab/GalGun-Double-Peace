$bytes = [IO.File]::ReadAllBytes('romfs\GG2Game\CookedNX\Coalesced_INT.bin')
$cands = Get-Content 'work\aes_candidates_title.json' | ConvertFrom-Json
function HexBytes($s) { $a=New-Object byte[] ($s.Length/2); for($i=0;$i -lt $s.Length;$i+=2){$a[$i/2]=[Convert]::ToByte($s.Substring($i,2),16)}; return $a }
$ivs = @(@{label='zero';bytes=(New-Object byte[] 16)})
foreach($c in $cands){ $key=HexBytes $c.key; foreach($ivcase in $ivs){
  foreach($mode in @([Security.Cryptography.CipherMode]::ECB,[Security.Cryptography.CipherMode]::CBC)){
    $aes=[Security.Cryptography.Aes]::Create(); $aes.Key=$key; $aes.Mode=$mode; $aes.Padding=[Security.Cryptography.PaddingMode]::None; if($mode -eq [Security.Cryptography.CipherMode]::CBC){$aes.IV=$ivcase.bytes}
    try{$x=$aes.CreateDecryptor().TransformFinalBlock($bytes,0,16)}catch{continue}
    $count=[BitConverter]::ToUInt32((@($x[3],$x[2],$x[1],$x[0])),0)
    $score=0; if($count -gt 0 -and $count -lt 1000){$score+=3}; if($x[4] -ge 0xf0 -and $x[5] -ge 0xf0 -and $x[6] -ge 0xf0 -and $x[7] -ge 0xf0){$score+=2}; if($x[0] -eq 0 -and $x[1] -eq 0){$score+=1}
    if($score -ge 3){Write-Output "$score $($c.label) $mode $([BitConverter]::ToString($x))"}
    $aes.Dispose()
  }
}}
