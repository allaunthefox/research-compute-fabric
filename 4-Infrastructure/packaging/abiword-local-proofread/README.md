# abiword-local-proofread

Local AUR-style package for proofreading AbiWord and LibreOffice-style files
with the local writing tools already installed on this machine.

This is a bridge wrapper, not a native AbiWord shared-object plugin or a
LibreOffice UNO extension. It uses the native document converters already
available locally, then runs:

- `harper-cli` for local grammar checks
- `vale` for local prose/style checks

Conversion preference:

- `.abw` / `.zabw`: AbiWord first, LibreOffice fallback
- `.odt`, `.ott`, `.docx`, `.doc`, `.rtf`, and related office files:
  LibreOffice headless first, AbiWord fallback
- `.txt`, `.md`, `.rst`, `.adoc`, `.html`: lint directly

## Build

```sh
makepkg -f
```

## Install

```sh
yay -U --noconfirm abiword-local-proofread-0.1.0-1-any.pkg.tar.zst
```

## Use

```sh
abiword-local-proofread draft.abw
abiword-local-proofread draft.odt
abiword-local-proofread draft.docx
abiword-local-proofread draft.rtf
abiword-local-proofread notes.txt
```

Flags:

```sh
--no-harper
--no-vale
--keep-tmp
```

If the current directory or a parent directory has `.vale.ini`, that config is
used. Otherwise, the package falls back to
`/usr/share/abiword-local-proofread/vale.ini`, which enables Vale's built-in
rules.

## Smoke Evidence

Validated locally:

```sh
abiword-local-proofread --no-harper /usr/share/abiword-3.0/readme.abw
```

This confirms the AbiWord export path and Vale pass run against an `.abw`
document.

LibreOffice support was validated with a Pandoc-generated `.odt` converted via:

```sh
libreoffice --headless --convert-to txt:Text --outdir "$tmpdir" smoke.odt
```

LibreOffice TeX support installed on this machine:

- `libreoffice-extension-texmaths`
- `libreoffice-extension-writer2latex`
