#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Rebuild every drawing and printable PDF for the RELAY-6 wireless launcher and join the build pack.
# Run from the repo root:   sh src/make_pack.sh
# Needs: python3, node (for nothing here), google-chrome or chromium, pdfunite (poppler-utils),
# and, for the BOM PDF only, bom_pdf.py from the fubsypoly website repo (set BOMPDF=/path/to/bom_pdf.py).
# Without it the committed shop/relay6-launcher-bom.pdf is kept as is.
set -e
HERE=$(pwd)
BOMPDF="${BOMPDF:-$HOME/Documents/claude/Projects/MyWebssite/packages/content-utils/scripts/bom_pdf.py}"
CHROME=$(command -v google-chrome || command -v chromium || command -v chromium-browser)

python3 -I src/gen_schematics.py figs
python3 -I src/gen_views.py figs
python3 -I src/gen_shop.py
python3 -I src/gen_guide.py

# Snap Chromium can only read and write under $HOME, so print from a folder there.
WORK="$HOME/.cache/relay6-pack"
rm -rf "$WORK"; mkdir -p "$WORK"
cp build_guide.html "$WORK/"
cp shop/cut_sheets.html "$WORK/"
"$CHROME" --headless=new --no-pdf-header-footer --print-to-pdf="$WORK/guide.pdf" "file://$WORK/build_guide.html" >/dev/null 2>&1
"$CHROME" --headless=new --no-pdf-header-footer --print-to-pdf="$WORK/sheets.pdf" "file://$WORK/cut_sheets.html" >/dev/null 2>&1
if [ -f "$BOMPDF" ]; then python3 "$BOMPDF" shop/bom.json -o "$WORK/bom.pdf"; cp "$WORK/bom.pdf" shop/relay6-launcher-bom.pdf; else echo "bom_pdf.py not found: keeping shop/relay6-launcher-bom.pdf"; cp shop/relay6-launcher-bom.pdf "$WORK/bom.pdf"; fi

cp "$WORK/guide.pdf" shop/relay6_build_guide.pdf
cp "$WORK/sheets.pdf" shop/relay6_cut_sheets_11x17.pdf
pdfunite "$WORK/guide.pdf" "$WORK/sheets.pdf" "$WORK/bom.pdf" shop/relay6_build_pack.pdf
python3 -c "import shutil,sys; shutil.make_archive(sys.argv[1], 'zip', sys.argv[2])" "$HERE/shop/relay6_dxf" "$HERE/shop/dxf"
rm -rf "$WORK"
echo "pack: $(pdfinfo shop/relay6_build_pack.pdf | awk '/^Pages/{print $2}') pages"
