const fs = require('fs');
function fixEscapes(path) {
    let code = fs.readFileSync(path, 'utf8');
    code = code.replace(/"Generate Story Graph"/g, '&quot;Generate Story Graph&quot;');
    fs.writeFileSync(path, code);
}
fixEscapes('src/app/projects/[id]/story-graph/page.tsx');
