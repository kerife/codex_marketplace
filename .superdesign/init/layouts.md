# Shared layouts

The plugin renders five offline artifact layouts. Each template is self-contained and has no remote stylesheet, script, image, or font dependency.

## Compact conversion outcome

Source: `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html`

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title><style>{{INLINE_CSS}}</style>
</head>
<body class="private-recruiter-outcome-document">
  <a class="skip-link" href="#main-content">{{SKIP}}</a>
  <main id="main-content" class="outcome-shell" tabindex="-1">
    <article class="outcome-card" aria-labelledby="outcome-heading">
      <p class="outcome-kicker">{{KICKER}}</p><h1 id="outcome-heading">{{HEADING}}</h1>
      <dl class="outcome-facts">
        <div><dt>{{EVENT_LABEL}}</dt><dd>{{EVENT}}</dd></div>
        <div><dt>{{DATE_LABEL}}</dt><dd><time datetime="{{DATE}}">{{DATE}}</time></dd></div>
        <div><dt>{{ACTION_LABEL}}</dt><dd>{{ACTION}}</dd></div>
        <div><dt>{{EVIDENCE_LABEL}}</dt><dd>{{EVIDENCE}}</dd></div>
      </dl>
      <p class="outcome-boundary">{{BOUNDARY}}</p>
    </article>
  </main>
  <footer class="outcome-footer"><strong>{{SAVE}}</strong>{{EMPLOYMENT_BOUNDARY}}</footer>
</body>
</html>
```

## Compact follow-through checkpoint

Source: `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html`

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title><style>{{INLINE_CSS}}</style>
</head>
<body class="private-recruiter-checkpoint-document">
  <a class="skip-link" href="#main-content">{{SKIP}}</a>
  <main id="main-content" class="checkpoint-shell" tabindex="-1">
    <article class="checkpoint-card" aria-labelledby="checkpoint-heading">
      <p class="checkpoint-kicker">{{KICKER}}</p>
      <h1 id="checkpoint-heading">{{HEADING}}</h1>
      <dl class="checkpoint-facts">
        <div><dt>{{STATE_LABEL}}</dt><dd>{{STATE}}</dd></div>
        <div><dt>{{EVENT_LABEL}}</dt><dd>{{EVENT}}</dd></div>
        <div><dt>{{DATE_LABEL}}</dt><dd><time datetime="{{DATE}}">{{DATE}}</time></dd></div>
        <div><dt>{{ACTION_LABEL}}</dt><dd>{{ACTION}}</dd></div>
      </dl>
      <p class="checkpoint-boundary">{{BOUNDARY}}</p>
    </article>
  </main>
  <footer class="checkpoint-footer"><strong>{{SAVE}}</strong>{{EMPLOYMENT_BOUNDARY}}</footer>
</body>
</html>
```

## Recruiter reply triage

Source: `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.html`

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <meta name="referrer" content="no-referrer">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; media-src 'none'; object-src 'none'; frame-src 'none'; worker-src 'none'; manifest-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title>
  <style>{{INLINE_CSS}}</style>
</head>
<body class="private-recruiter-triage-document">
  {{HEADER}}
  {{MAIN}}
</body>
</html>
```

## Recruiter practice session

Source: `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.html`

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <meta name="referrer" content="no-referrer">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; media-src 'none'; object-src 'none'; frame-src 'none'; worker-src 'none'; manifest-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title>
  <style>{{INLINE_CSS}}</style>
</head>
<body class="recruiter-practice-document">
  {{HEADER}}
  {{MAIN}}
</body>
</html>
```

## Executive career dossier

Source: `plugins/professional-growth-coach/assets/executive-career-dossier-v1.html`

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <meta name="referrer" content="no-referrer">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; media-src 'none'; object-src 'none'; frame-src 'none'; worker-src 'none'; manifest-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title>
  <style>{{INLINE_CSS}}</style>
</head>
<body class="dossier-document">
  {{HEADER}}
  {{MAIN}}
  <script>{{INLINE_SCRIPT}}</script>
</body>
</html>
```

## Private vacancy application packet

Source: `plugins/professional-growth-coach/assets/private-vacancy-application-packet-v1.html`

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <meta name="referrer" content="no-referrer">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; media-src 'none'; object-src 'none'; frame-src 'none'; worker-src 'none'; manifest-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{DOCUMENT_TITLE}}</title>
  <style>
{{INLINE_CSS}}
  </style>
</head>
<body class="private-vacancy-packet-document" data-print-private="{{PRINT_PRIVATE}}" data-print-boundary="{{PRINT_BOUNDARY}}">
  <a class="skip-link" href="#main-content">{{SKIP_LINK}}</a>
{{HEADER}}
{{MAIN}}
{{FOOTER}}
</body>
</html>
```
