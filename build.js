// SmartOrchard 构建脚本
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const frontendDir = path.join(__dirname, 'frontend');
const log = fs.createWriteStream('/tmp/build.log', { flags: 'a' });
const logf = (msg) => { console.log(msg); log.write(msg + '\n'); };

process.chdir(frontendDir);
logf('WORKDIR: ' + process.cwd());
logf('Installing...');

try {
  execSync('npm install --loglevel verbose', { stdio: 'inherit' });
  logf('Installed OK');
} catch(e) {
  logf('npm install FAILED: ' + e.message);
  process.exit(1);
}

logf('Building...');
try {
  execSync('npm run build', { stdio: 'inherit' });
  logf('Build OK');
} catch(e) {
  logf('build FAILED: ' + e.message);
  process.exit(1);
}
logf('DONE');
