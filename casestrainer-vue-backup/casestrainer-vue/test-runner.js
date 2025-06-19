#!/usr/bin/env node

const { execSync, spawn } = require('child_process');
const readline = require('readline');
const fs = require('fs');
const path = require('path');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

const log = (message, color = '') => {
  console.log(`${color}${message}${colors.reset}`);
};

const logStep = (message) => {
  log(`\n${colors.cyan}▶ ${message}...${colors.reset}`);
};

const logSuccess = (message) => {
  log(`✓ ${message}`, colors.green);
};

const logError = (message) => {
  log(`✗ ${message}`, colors.red);
};

const runCommand = (command, options = {}) => {
  const { cwd = process.cwd(), exitOnError = true } = options;
  
  try {
    log(`Running: ${colors.dim}${command}${colors.reset}`);
    const result = execSync(command, { 
      cwd, 
      stdio: 'inherit',
      ...options
    });
    return { success: true, output: result };
  } catch (error) {
    if (exitOnError) {
      logError(`Command failed: ${command}`);
      process.exit(1);
    }
    return { success: false, error };
  }
};

const checkBackend = () => {
  logStep('Checking if backend server is running');
  try {
    execSync('curl -s http://localhost:5000/casestrainer/api/health', { stdio: 'pipe' });
    logSuccess('Backend server is running');
    return true;
  } catch (error) {
    logError('Backend server is not running or not accessible at http://localhost:5000/casestrainer/api/health');
    return false;
  }
};

const installDependencies = () => {
  logStep('Checking dependencies');
  if (!fs.existsSync('node_modules')) {
    log('Installing npm dependencies...');
    runCommand('npm install');
  } else {
    logSuccess('All dependencies are installed');
  }
};

const runTests = (mode = 'open') => {
  logStep('Starting Cypress tests');
  
  const command = mode === 'open' 
    ? 'npm run test:validator:open' 
    : 'npm run test:validator';
  
  runCommand(command);
};

const main = async () => {
  log(`\n${colors.bright}${colors.blue}CaseStrainer Test Runner${colors.reset}\n`);
  
  // Check Node.js version
  const nodeVersion = process.version;
  log(`Using Node.js ${nodeVersion}`);
  
  // Install dependencies if needed
  installDependencies();
  
  // Check if backend is running
  const isBackendRunning = checkBackend();
  
  if (!isBackendRunning) {
    log('\nPlease start the backend server first using:');
    log('  python src/app_final_vue.py\n', colors.yellow);
    process.exit(1);
  }
  
  // Ask user what to do
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
  
  const question = (query) => new Promise(resolve => rl.question(query, resolve));
  
  try {
    const answer = await question('Choose an option:\n1. Run tests in interactive mode (Cypress UI)\n2. Run tests in headless mode\n3. Exit\n\nEnter your choice (1-3): ');
    
    switch (answer.trim()) {
      case '1':
        runTests('open');
        break;
      case '2':
        runTests('headless');
        break;
      case '3':
      default:
        log('Exiting...');
        process.exit(0);
    }
  } catch (error) {
    logError('An error occurred: ' + error.message);
    process.exit(1);
  } finally {
    rl.close();
  }
};

main();
