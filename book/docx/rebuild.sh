#!/bin/sh
cd "$(dirname "$0")"
node build_doc.js >/dev/null && python3 fixids.py "Miner 2049er Commented.docx" && cp "Miner 2049er Commented.docx" render/mc.docx && cd render && rm -f mc.pdf && timeout 900 $(command -v soffice || echo soffice) --headless --convert-to pdf mc.docx >/dev/null 2>&1; cd .. && python3 pages.py
