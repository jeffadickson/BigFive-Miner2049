// Build "Miner 2049er Commented.docx" from content.md, the figures and the commented listing.
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, ImageRun, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, PageBreak, Header, Footer, PageNumber, LevelFormat, TabStopType,
  TabStopPosition, InternalHyperlink, Bookmark, PageOrientation, LineRuleType,
} = require('docx');

const DIR = __dirname;
const FIG = path.join(DIR, '..', 'fig');
const ASM = path.join(DIR, '..', '..', 'src', 'miner2049er.asm');
const BODY = 'Calibri', MONO = 'Consolas';
const NAVY = '1F3A5F', GREY = '5A6370', CODEBG = 'F3F5F8';
const pages = fs.existsSync(path.join(DIR, 'pages.json')) ? JSON.parse(fs.readFileSync(path.join(DIR, 'pages.json'))) : {};

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

// inline markup: **bold**, `code`
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith('**')) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), font: MONO, size: 19, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}

let bm = 0;
const tocEntries = [];
function heading(text, level) {
  const id = 'h' + (++bm);
  tocEntries.push({ text, level, id });
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3,
    pageBreakBefore: level === 1,
    children: [new Bookmark({ id, children: [new TextRun(text)] })],
  });
}

function image(file, caption, widthIn) {
  const p = path.join(FIG, file);
  const { w, h } = pngSize(p);
  const wpx = Math.round(widthIn * 96), hpx = Math.round(wpx * h / w);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60, line: 240, lineRule: LineRuleType.AUTO },
      children: [new ImageRun({ type: 'png', data: fs.readFileSync(p), transformation: { width: wpx, height: hpx } })] }),
    new Paragraph({ style: 'Caption', children: runs(caption) }),
  ];
}

function table(rows) {
  const ncol = rows[0].length;
  const total = 9360;
  // column widths by content length
  const lens = Array(ncol).fill(0);
  rows.forEach(r => r.forEach((c, i) => { lens[i] = Math.max(lens[i], Math.min(60, c.length)); }));
  const sum = lens.reduce((a, b) => a + b, 0);
  let widths = lens.map(l => Math.max(900, Math.round(total * l / sum)));
  const ws = widths.reduce((a, b) => a + b, 0);
  widths = widths.map(w => Math.round(w * total / ws));
  widths[ncol - 1] += total - widths.reduce((a, b) => a + b, 0);
  const border = { style: BorderStyle.SINGLE, size: 4, color: 'C9D1DB' };
  const borders = { top: border, bottom: border, left: border, right: border };
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, ri) => new TableRow({
      tableHeader: ri === 0,
      children: r.map((c, ci) => new TableCell({
        borders, width: { size: widths[ci], type: WidthType.DXA },
        shading: ri === 0 ? { type: ShadingType.CLEAR, fill: 'E3EAF3', color: 'auto' } : undefined,
        margins: { top: 50, bottom: 50, left: 100, right: 100 },
        children: [new Paragraph({ spacing: { after: 0 }, children: runs(c, ri === 0 ? { bold: true, size: 20 } : { size: 20 }) })],
      })),
    })),
  });
}

function codeBlock(lines) {
  return lines.map((l, i) => new Paragraph({ style: 'Code',
    spacing: { before: i === 0 ? 80 : 0, after: i === lines.length - 1 ? 140 : 0 },
    children: [new TextRun({ text: l.length ? l : ' ', font: MONO, size: 17 })] }));
}

// ---------------------------------------------------------------- body from content.md
function buildBody() {
  const src = fs.readFileSync(path.join(DIR, 'content.md'), 'utf8').split('\n');
  const out = [];
  let i = 0;
  while (i < src.length) {
    const l = src[i];
    if (l.startsWith('```')) {
      const block = []; i++;
      while (i < src.length && !src[i].startsWith('```')) block.push(src[i++]);
      i++; out.push(...codeBlock(block)); continue;
    }
    if (l.startsWith('# ')) { out.push(heading(l.slice(2), 1)); i++; continue; }
    if (l.startsWith('## ')) { out.push(heading(l.slice(3), 2)); i++; continue; }
    if (l.startsWith('### ')) { out.push(heading(l.slice(4), 3)); i++; continue; }
    if (l.startsWith('!img ')) {
      const [f, cap, w] = l.slice(5).split('|');
      out.push(...image(f.trim(), cap.trim(), parseFloat(w))); i++; continue;
    }
    if (l.startsWith('|')) {
      const rows = [];
      while (i < src.length && src[i].startsWith('|')) {
        rows.push(src[i].replace(/^\||\|$/g, '').split('|').map(s => s.trim())); i++;
      }
      out.push(table(rows)); out.push(new Paragraph({ spacing: { after: 60 }, children: [] })); continue;
    }
    if (l.startsWith('- ')) {
      out.push(new Paragraph({ numbering: { reference: 'bul', level: 0 }, spacing: { after: 60 }, children: runs(l.slice(2)) }));
      i++; continue;
    }
    if (/^\d+\. /.test(l)) {
      out.push(new Paragraph({ numbering: { reference: 'num' + numRef, level: 0 }, spacing: { after: 60 }, children: runs(l.replace(/^\d+\. /, '')) }));
      i++;
      if (i >= src.length || !/^\d+\. /.test(src[i])) numRef++;
      continue;
    }
    if (l.trim() === '') { i++; continue; }
    out.push(new Paragraph({ children: runs(l) })); i++;
  }
  return out;
}
let numRef = 0;

// ---------------------------------------------------------------- listing appendix
function listing() {
  const lines = fs.readFileSync(ASM, 'utf8').replace(/\n$/, '').split('\n');
  const out = [];
  for (const l of lines) {
    const children = [];
    const isComment = l.startsWith(';');
    if (isComment) {
      const rule = /^;[-=]{20,}/.test(l);
      children.push(new TextRun({ text: l, font: MONO, size: 14, color: rule ? '9AA5B1' : '3E5C3A', italics: !rule }));
    } else {
      // label / instruction / comment
      let code = l, cmt = '';
      const ci = l.indexOf(';');
      if (ci >= 0) { code = l.slice(0, ci); cmt = l.slice(ci); }
      const m = code.match(/^([A-Za-z_][A-Za-z0-9_]*:)(\s*)(.*)$/);
      if (m) {
        children.push(new TextRun({ text: m[1], font: MONO, size: 14, bold: true, color: NAVY }));
        children.push(new TextRun({ text: m[2] + m[3], font: MONO, size: 14 }));
      } else {
        const j = code.match(/^(\s+)(jsr|jmp)(\s+)(\S+)(.*)$/);
        if (j) {
          children.push(new TextRun({ text: j[1], font: MONO, size: 14 }));
          children.push(new TextRun({ text: j[2], font: MONO, size: 14, bold: true }));
          children.push(new TextRun({ text: j[3], font: MONO, size: 14 }));
          children.push(new TextRun({ text: j[4], font: MONO, size: 14, bold: true, color: '8A3B12' }));
          children.push(new TextRun({ text: j[5], font: MONO, size: 14 }));
        } else children.push(new TextRun({ text: code.length ? code : ' ', font: MONO, size: 14 }));
      }
      if (cmt) children.push(new TextRun({ text: cmt, font: MONO, size: 14, color: '3E5C3A' }));
    }
    out.push(new Paragraph({ style: 'Listing', children }));
  }
  return out;
}

// ---------------------------------------------------------------- title page and contents
function titlePage() {
  const p = path.join(FIG, 'credits_end.png');
  const { w, h } = pngSize(p);
  const wpx = Math.round(6.2 * 96), hpx = Math.round(wpx * h / w);
  return [
    new Paragraph({ spacing: { before: 600, after: 200 }, alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: 'Miner 2049er Commented', bold: true, size: 64, color: NAVY, font: BODY })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 },
      children: [new TextRun({ text: 'A commented disassembly of Bill Hogue’s 1982 cartridge for the Atari 400/800', size: 28, color: GREY })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120, line: 240, lineRule: LineRuleType.AUTO },
      children: [new ImageRun({ type: 'png', data: fs.readFileSync(p), transformation: { width: wpx, height: hpx } })] }),
    new Paragraph({ style: 'Caption', children: [new TextRun('The game’s own credits screen, at the end of its opening demo.')] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 500 },
      children: [new TextRun({ text: 'Big Five Software, 1982  ·  16K cartridge  ·  6502 machine language', size: 22, color: GREY })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 },
      children: [new TextRun({ text: 'October 2026', size: 22, color: GREY })] }),
  ];
}

function contents(entries) {
  const out = [new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun('Contents')] })];
  for (const e of entries) {
    if (e.level > 2) continue;
    const pg = pages[e.text] !== undefined ? String(pages[e.text]) : '';
    out.push(new Paragraph({
      spacing: { after: e.level === 1 ? 60 : 20, before: e.level === 1 ? 100 : 0 },
      indent: { left: e.level === 1 ? 0 : 400 },
      tabStops: [{ type: TabStopType.RIGHT, position: 9360, leader: 'dot' }],
      children: [new InternalHyperlink({ anchor: e.id, children: [
        new TextRun({ text: e.text, bold: e.level === 1, size: e.level === 1 ? 22 : 20 }),
        new TextRun({ text: '\t' + pg, size: e.level === 1 ? 22 : 20 })] })],
    }));
  }
  return out;
}

// ---------------------------------------------------------------- assemble
const body = buildBody();
const appendix = [heading('Appendix A: the complete listing', 1),
  new Paragraph({ children: runs('This is miner2049er.asm in full. Labels are shown in bold; for `jsr` and `jmp` the target is highlighted, and its comment says what the called routine does. Routine headers are set between rules. Assembled with ca65 and linked with the cart.cfg shown in the file header, it reproduces the original 16,384-byte ROM exactly.') }),
  ...listing()];
const toc = contents(tocEntries);

const numbering = { config: [
  { reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
  ...Array.from({ length: 20 }, (_, k) => ({ reference: 'num' + k, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.',
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 340 } } } }] })),
] };

const header = new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
  children: [new TextRun({ text: 'Miner 2049er Commented', size: 16, color: GREY })] })] });
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
  children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: GREY })] })] });
const LETTER = { width: 12240, height: 15840 };

const doc = new Document({
  title: 'Miner 2049er Commented', creator: 'Jeff Dickson',
  description: 'Commented disassembly of Miner 2049er (Atari 400/800, Big Five Software, 1982)',
  styles: {
    default: { document: { run: { font: BODY, size: 22 }, paragraph: { spacing: { after: 120, line: 276, lineRule: LineRuleType.AUTO } } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 36, bold: true, color: NAVY, font: BODY }, paragraph: { spacing: { before: 120, after: 220 }, outlineLevel: 0, keepNext: true } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 28, bold: true, color: NAVY, font: BODY }, paragraph: { spacing: { before: 300, after: 120 }, outlineLevel: 1, keepNext: true } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 24, bold: true, color: '2E4A6E', font: BODY }, paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 2, keepNext: true } },
      { id: 'Code', name: 'Code', basedOn: 'Normal',
        run: { font: MONO, size: 17 }, paragraph: { spacing: { after: 0, line: 240 }, indent: { left: 120, right: 120 },
          shading: { type: ShadingType.CLEAR, fill: CODEBG, color: 'auto' } } },
      { id: 'Listing', name: 'Listing', basedOn: 'Normal',
        run: { font: MONO, size: 14 }, paragraph: { spacing: { after: 0, line: 200 } } },
      { id: 'Caption', name: 'Caption', basedOn: 'Normal',
        run: { size: 18, italics: true, color: '4A5563' }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 240 } } },
    ],
  },
  numbering,
  sections: [
    { properties: { page: { size: LETTER, margin: { top: 1260, bottom: 1260, left: 1440, right: 1440 } } },
      children: [...titlePage()] },
    { properties: { page: { size: LETTER, margin: { top: 1260, bottom: 1260, left: 1440, right: 1440 } } },
      headers: { default: header }, footers: { default: footer },
      children: [...toc, ...body] },
    { properties: { page: { size: LETTER, margin: { top: 1000, bottom: 1000, left: 1000, right: 900 } } },
      headers: { default: header }, footers: { default: footer },
      children: appendix },
  ],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(path.join(DIR, 'Miner 2049er Commented.docx'), buf);
  fs.writeFileSync(path.join(DIR, 'toc.json'), JSON.stringify(tocEntries.filter(e => e.level <= 2)));
  console.log('written', tocEntries.length, 'headings');
});
