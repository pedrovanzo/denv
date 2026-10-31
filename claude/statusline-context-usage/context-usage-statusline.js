#!/usr/bin/env node
// context-usage-statusline — prints "X.Xk (Y.Y%)" context usage, like the
// stock Claude Code statusline. Reads the statusLine JSON on stdin for
// transcript_path, then reads only the tail of that transcript to find the
// most recent token usage entry.

const fs = require('fs');

const CONTEXT_WINDOW = 1000000; // Sonnet 5 / Opus / Fable context window (Haiku 4.5 is 200k)
const TAIL_CAP = 65536; // never read more than this from the transcript

let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { raw += chunk; });
process.stdin.on('end', () => {
  try {
    const input = JSON.parse(raw);
    const transcriptPath = input.transcript_path;
    if (!transcriptPath || typeof transcriptPath !== 'string') return;

    const stat = fs.statSync(transcriptPath);
    const start = Math.max(0, stat.size - TAIL_CAP);
    const length = stat.size - start;
    const fd = fs.openSync(transcriptPath, 'r');
    const buf = Buffer.alloc(length);
    fs.readSync(fd, buf, 0, length, start);
    fs.closeSync(fd);

    const lines = buf.toString('utf8').split('\n').filter(Boolean);
    let usage = null;
    for (let i = lines.length - 1; i >= 0; i--) {
      let entry;
      try { entry = JSON.parse(lines[i]); } catch { continue; }
      const u = entry && entry.message && entry.message.usage;
      if (u && typeof u.input_tokens === 'number') { usage = u; break; }
    }
    if (!usage) return;

    const tokens = (usage.input_tokens || 0)
      + (usage.cache_creation_input_tokens || 0)
      + (usage.cache_read_input_tokens || 0);
    const pct = (tokens / CONTEXT_WINDOW) * 100;
    const kTokens = (tokens / 1000).toFixed(1) + 'k';

    process.stdout.write(`\x1b[38;5;220m${kTokens} (${pct.toFixed(1)}%)\x1b[0m`);
  } catch {
    // silent — statusline should never crash the terminal
  }
});
