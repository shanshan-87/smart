// SmartOrchard 构建脚本
// 负责构建前端 Vue 项目

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const frontendDir = path.join(__dirname, 'frontend');

console.log('📦 安装前端依赖...');
try {
  execSync('npm install', { cwd: frontendDir, stdio: 'inherit' });
  console.log('✅ 依赖安装完成');
} catch (e) {
  console.error('❌ 依赖安装失败:', e.message);
  process.exit(1);
}

console.log('🔨 构建前端...');
try {
  execSync('npm run build', { cwd: frontendDir, stdio: 'inherit' });
  console.log('✅ 构建完成！');
} catch (e) {
  console.error('❌ 构建失败:', e.message);
  process.exit(1);
}

// 确保 dist 目录存在
const distDir = path.join(frontendDir, 'dist');
if (!fs.existsSync(distDir)) {
  console.error('❌ dist 目录未生成！');
  process.exit(1);
}

console.log('✅ SmartOrchard 前端构建成功！');
