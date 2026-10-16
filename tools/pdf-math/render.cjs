'use strict';

// Deliberately use the complete v3 font bundle: no dynamic fonts or network loader.
const { mathjax } = require('mathjax-full/js/mathjax.js');
const { TeX } = require('mathjax-full/js/input/tex.js');
const { SVG } = require('mathjax-full/js/output/svg.js');
const { liteAdaptor } = require('mathjax-full/js/adaptors/liteAdaptor.js');
const { RegisterHTMLHandler } = require('mathjax-full/js/handlers/html.js');
require('mathjax-full/js/input/tex/ams/AmsConfiguration.js');

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const tex = new TeX({
  packages: ['base', 'ams'], maxMacros: 500, maxBuffer: 4096,
  formatError: (_jax, error) => { throw new Error(error.message); },
});
const document = mathjax.document('', { InputJax: tex, OutputJax: new SVG({ fontCache: 'none' }) });
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  input += chunk;
  if (Buffer.byteLength(input, 'utf8') > 524288) process.exit(1);
});
process.stdin.on('end', () => {
  try {
    const formulas = JSON.parse(input);
    if (!Array.isArray(formulas) || formulas.length > 256) throw new Error('Invalid formula batch');
    let outputBytes = 0;
    const result = formulas.map(formula => {
      if (typeof formula !== 'string' || formula.length > 4096) throw new Error('Formula too long');
      if (/\\(?:href|url|html\w*|require|includegraphics|input|include|write|openout|read|usepackage|class|style)\b/i.test(formula)) {
        throw new Error('External or active math content is not allowed');
      }
      const node = document.convert(formula, { display: false, em: 10, ex: 5, containerWidth: 600 });
      const svg = adaptor.outerHTML(adaptor.firstChild(node));
      outputBytes += Buffer.byteLength(svg, 'utf8');
      if (outputBytes > 8388608) throw new Error('Rendered formulas too large');
      return svg;
    });
    process.stdout.write(JSON.stringify(result));
  } catch (_error) {
    process.stderr.write('Math expression could not be rendered safely.');
    process.exitCode = 1;
  }
});
