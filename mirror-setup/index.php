# index.php
‘;
$host = preg_replace(‘/^[^\/]+\/\//’,”,$URL);
$tarray = explode(‘/’,$host);
$host = array_shift($tarray);
$URI = ‘/’ . implode(‘/’,$tarray);
$content = ”;
$fp = @fsockopen($host,80,$errno,$errstr,30);
if(!$fp) { echo “Unable to open socked: $errstr ($errno)\n”; exit; }
fwrite($fp,”GET $URI HTTP/1.0\r\n”);
fwrite($fp,”Host: $host\r\n”);
if( isset($_SERVER[“HTTP_USER_AGENT”]) ) { fwrite($fp,’User-Agent: ‘.$_SERVER[“HTTP_USER_AGENT”].”\r\n”); }
fwrite($fp,”Connection: Close\r\n”);
fwrite($fp,”\r\n”);
while (!feof($fp)) { $content .= fgets($fp, 128); }
fclose($fp);
if( strpos($content,”\r\n”) > 0 ) { $eolchar = “\r\n”; }
else { $eolchar = “\n”; }
$eolpos = strpos($content,”$eolchar$eolchar”);
$content = substr($content,($eolpos + strlen(“$eolchar$eolchar”)));
$content = str_replace($wc_source,$wc_mirror,$content);
// replaces paths with / in the begining without full url. not required unless you are in subfolder
$content = str_replace(‘href=”/’,’href=”http://prime.uncoded.life’.$wc_mirror.’/’,$content);
$content = str_replace(‘src=”/’,’src=”http://prime.uncoded.life’.$wc_mirror.’/’,$content);

// $fsize = filesize($fullPath);
$path_parts = pathinfo($fullPath);
$ext = strtolower($path_parts[“extension”]);

// Determine Content Type
switch ($ext) {
case “pdf”: $ctype=”application/pdf”; break;
case “exe”: $ctype=”application/octet-stream”; break;
case “zip”: $ctype=”application/zip”; break;
case “doc”: $ctype=”application/msword”; break;
case “xls”: $ctype=”application/vnd.ms-excel”; break;
case “ppt”: $ctype=”application/vnd.ms-powerpoint”; break;
case “gif”: $ctype=”image/gif”; break;
case “png”: $ctype=”image/png”; break;
case “jpeg”: $ctype=”image/jpg”; break;
case “jpg”: $ctype=”image/jpg”; break;
case “js”: $ctype=”text/javascript”; break;
case “css”: $ctype=”text/css”; break;
}

header(“Pragma: public”); // required
header(“Expires: 0”);
header(“Cache-Control: must-revalidate, post-check=0, pre-check=0”);
header(“Cache-Control: private”,false); // required for certain browsers
header(“Content-Type: $ctype”);
header(“Content-Transfer-Encoding: binary”);
// header(“Content-Length: “.$fsize);

if( preg_match(‘//i’,$content) ) { echo( preg_replace(‘//i’,’‘.$base,$content,1) ); }
else { echo ( str_replace($wc_source,$wc_mirror,preg_replace(‘/<([a-z])([^>]+)>/i’,”<\\1\\2>“.$base,$content,1) ));
}
?>
