const fs = require('fs');
const path = require('path');

async function globalSetup(config) {
  console.log('🚀 Setting up test environment...');
  
  // Ensure test directories exist - updated paths for new structure
  const testDirs = [
    '../../data/test-results',
    '../../data/test-results/html-report',
    '../../data/test-results/artifacts',
    '../../data/screenshots',
    '../../data/logs'
  ];
  
  testDirs.forEach(dir => {
    const fullPath = path.resolve(__dirname, dir);
    if (!fs.existsSync(fullPath)) {
      fs.mkdirSync(fullPath, { recursive: true });
      console.log(`   ✓ Created directory: ${dir}`);
    }
  });
  
  // Create test start timestamp
  const startTime = new Date().toISOString();
  const logPath = path.resolve(__dirname, '../../data/logs/test-session-start.txt');
  fs.writeFileSync(logPath, startTime);
  
  console.log(`   ✓ Test session started at: ${startTime}`);
  console.log('   ✓ Global setup completed');
}

module.exports = globalSetup; 