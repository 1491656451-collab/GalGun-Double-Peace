$ct=[IO.File]::ReadAllBytes('romfs\GG2Game\CookedNX\Coalesced_INT.bin')
$cands=Get-Content 'work\aes_candidates_all.json'|ConvertFrom-Json
function HB($s){$a=New-Object byte[]($s.Length/2);for($i=0;$i -lt $s.Length;$i+=2){$a[$i/2]=[Convert]::ToByte($s.Substring($i,2),16)};return $a}
function IncBE([byte[]]$a){for($i=$a.Length-1;$i -ge 0;$i--){$a[$i]++;if($a[$i] -ne 0){break}}}
$ivs=@(@{l='zero';v=(New-Object byte[] 16)});
foreach($iv in @('0bad299aa9727ef6e9598ee14add21aa','c0d96d49c78c974d5cbdf6e190b981d4','9764d7caf92e3d7221e0d45f7435dbfa','0c120d33d34057401a4f135cb668fbfb')){$ivs+=@{l=$iv;v=(HB $iv)}}
foreach($c in $cands){$key=HB $c.key;foreach($iv0 in $ivs){$aes=[Security.Cryptography.Aes]::Create();$aes.Key=$key;$aes.Mode=[Security.Cryptography.CipherMode]::ECB;$aes.Padding=[Security.Cryptography.PaddingMode]::None;$ctr=[byte[]]$iv0.v.Clone();try{$ks=$aes.CreateEncryptor().TransformFinalBlock($ctr,0,16)}catch{continue};$x=New-Object byte[] 16;for($i=0;$i -lt 16;$i++){$x[$i]=$ct[$i]-bxor $ks[$i]};$n=[BitConverter]::ToUInt32((@($x[3],$x[2],$x[1],$x[0])),0);$score=0;if($n -gt 0 -and $n -lt 2000){$score+=3};if($x[0]-eq 0 -and $x[1]-eq 0){$score++};if($score -ge 3){Write-Output "$score $($c.label) iv=$($iv0.l) $([BitConverter]::ToString($x))"};$aes.Dispose()}}
