const fs = require('fs');
const path = require('path');

async function globalTeardown(config) {
  console.log('🧹 Cleaning up test environment...');
  
  // Record test end time
  const endTime = new Date().toISOString();
  const endLogPath = path.resolve(__dirname, '../../data/logs/test-session-end.txt');
  fs.writeFileSync(endLogPath, endTime);
  
  // Calculate test duration if start time exists
  const startLogPath = path.resolve(__dirname, '../../data/logs/test-session-start.txt');
  if (fs.existsSync(startLogPath)) {
    const startTime = fs.readFileSync(startLogPath, 'utf8');
    const duration = new Date(endTime) - new Date(startTime);
    const durationMinutes = Math.round(duration / 1000 / 60);
    
    console.log(`   ✓ Test session duration: ${durationMinutes} minutes`);
  }
  
  // Generate test summary
  const summary = {
    session_end: endTime,
    test_artifacts_location: 'data/test-results/',
    screenshots_location: 'data/screenshots/',
    logs_location: 'data/logs/',
    html_report: 'data/test-results/html-report/index.html'
  };
  
  const summaryPath = path.resolve(__dirname, '../../data/logs/test-session-summary.json');
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
  
  console.log('   ✓ Test artifacts preserved');
  console.log('   ✓ Global teardown completed');
  console.log('\n📊 Test Results Available:');
  console.log('   • HTML Report: data/test-results/html-report/index.html');
  console.log('   • Screenshots: data/screenshots/');
  console.log('   • Logs: data/logs/');
}

module.exports = globalTeardown; 