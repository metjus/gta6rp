<?php
// Country-level detection only; no API key, external lookup or IP logging.
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: private, no-store, max-age=0');
header('Vary: CF-IPCountry, Accept-Language');
header('X-Robots-Tag: noindex, nofollow');
header('X-Content-Type-Options: nosniff');
$country = strtoupper(trim($_SERVER['HTTP_CF_IPCOUNTRY'] ?? ''));
if (preg_match('/^[A-Z]{2}$/D', $country) && $country !== 'XX') {
    $language = $country === 'SK' ? 'sk' : 'en';
    $source = 'country';
} else {
    $candidates = [];
    foreach (explode(',', substr($_SERVER['HTTP_ACCEPT_LANGUAGE'] ?? '', 0, 1024)) as $part) {
        $pieces = explode(';', trim($part));
        $locale = strtolower(trim($pieces[0]));
        $quality = 1.0;
        foreach (array_slice($pieces, 1) as $parameter) {
            if (preg_match('/^\s*q\s*=\s*([01](?:\.[0-9]+)?)\s*$/', $parameter, $m)) $quality = (float) $m[1];
        }
        if ($locale !== '' && $locale !== '*' && $quality > 0) $candidates[] = ['locale' => $locale, 'q' => $quality];
    }
    usort($candidates, static fn($a, $b) => $b['q'] <=> $a['q']);
    $preferred = $candidates[0]['locale'] ?? 'en';
    $language = preg_match('/^(sk|cs)(-|$)/', $preferred) ? 'sk' : 'en';
    $source = 'browser';
}
echo json_encode(['language' => $language, 'source' => $source], JSON_UNESCAPED_SLASHES);
