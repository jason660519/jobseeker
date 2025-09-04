# Desktop Application Project Setup Guide

## Overview

Complete guide for building the JobSpy Desktop application with Electron, Python integration, and license validation system.

## Project Architecture

```
jobspy-desktop/
├── package.json                    # Node.js dependencies and scripts
├── main.js                         # Electron main process
├── preload.js                      # Security bridge script
├── src/
│   ├── renderer/                   # Frontend UI (React)
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── styles/
│   ├── python/                     # Python backend integration
│   │   ├── job_scraper.py
│   │   ├── license_validator.py
│   │   └── requirements.txt
│   └── shared/                     # Shared utilities
│       ├── constants.js
│       ├── license.js
│       └── storage.js
├── assets/                         # Icons and resources
├── build/                          # Build configuration
└── dist/                          # Distribution packages
```

## Prerequisites

### System Requirements
- **Node.js**: 18.0.0 or higher
- **Python**: 3.10 or higher
- **npm**: 8.0.0 or higher
- **Git**: Latest version

### Development Tools
```bash
# Install global tools
npm install -g electron
npm install -g electron-builder
npm install -g concurrently

# Verify installations
node --version    # Should show v18+
python --version  # Should show 3.10+
electron --version
```

## Project Initialization

### 1. Create Project Structure

```bash
# Create main project directory
mkdir jobspy-desktop
cd jobspy-desktop

# Initialize npm project
npm init -y

# Install core dependencies
npm install electron electron-builder python-shell
npm install react react-dom react-router-dom
npm install axios styled-components lucide-react

# Install development dependencies
npm install --save-dev concurrently wait-on
npm install --save-dev @electron/rebuild
npm install --save-dev webpack webpack-cli babel-loader
```

### 2. Package.json Configuration

```json
{
  "name": "jobspy-desktop",
  "productName": "JobSpy Pro",
  "version": "1.0.0",
  "description": "Professional job search tool with local processing",
  "main": "main.js",
  "homepage": "./",
  "scripts": {
    "electron": "electron .",
    "electron-dev": "concurrently \"npm run dev\" \"wait-on http://localhost:3000 && electron .\"",
    "dev": "webpack serve --mode development",
    "build": "webpack --mode production",
    "dist": "npm run build && electron-builder",
    "dist-win": "npm run build && electron-builder --win",
    "dist-mac": "npm run build && electron-builder --mac",
    "dist-linux": "npm run build && electron-builder --linux",
    "pack": "electron-builder --dir",
    "postinstall": "electron-builder install-app-deps"
  },
  "build": {
    "appId": "com.jobspy.desktop",
    "productName": "JobSpy Pro",
    "directories": {
      "output": "dist",
      "buildResources": "assets"
    },
    "files": [
      "build/**/*",
      "main.js",
      "preload.js",
      "src/python/**/*",
      "node_modules/**/*"
    ],
    "extraResources": [
      {
        "from": "src/python",
        "to": "python",
        "filter": ["**/*"]
      }
    ],
    "win": {
      "target": "nsis",
      "icon": "assets/icon.ico",
      "publisherName": "JobSpy Inc.",
      "verifyUpdateCodeSignature": false
    },
    "mac": {
      "target": "dmg",
      "icon": "assets/icon.icns",
      "category": "public.app-category.business"
    },
    "linux": {
      "target": "AppImage",
      "icon": "assets/icon.png",
      "category": "Office"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true
    },
    "publish": {
      "provider": "github",
      "owner": "yourusername",
      "repo": "jobspy-desktop"
    }
  },
  "keywords": ["job search", "desktop", "electron", "local processing"],
  "author": "JobSpy Team",
  "license": "Commercial"
}
```

### 3. Electron Main Process (main.js)

```javascript
const { app, BrowserWindow, ipcMain, dialog, shell, Menu } = require('electron');
const { PythonShell } = require('python-shell');
const path = require('path');
const fs = require('fs');
const isDev = process.env.NODE_ENV === 'development';

// Keep a global reference of the window object
let mainWindow;
let splashWindow;

// License validation
const LicenseManager = require('./src/shared/license');
const licenseManager = new LicenseManager();

function createSplashWindow() {
    splashWindow = new BrowserWindow({
        width: 400,
        height: 300,
        frame: false,
        alwaysOnTop: true,
        transparent: true,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    splashWindow.loadFile('assets/splash.html');
    
    splashWindow.on('closed', () => {
        splashWindow = null;
    });
}

async function createWindow() {
    // Validate license before opening main window
    const licenseValid = await licenseManager.validateLicense();
    
    if (!licenseValid && !isDev) {
        // Show license activation dialog
        const result = await dialog.showMessageBox({
            type: 'warning',
            title: 'License Required',
            message: 'JobSpy Pro requires a valid license to continue.',
            buttons: ['Enter License Key', 'Use Free Version', 'Exit'],
            defaultId: 0
        });

        if (result.response === 0) {
            // Show license input dialog
            await showLicenseDialog();
        } else if (result.response === 1) {
            // Continue with free version limitations
            licenseManager.setFreeMode(true);
        } else {
            // Exit application
            app.quit();
            return;
        }
    }

    // Create the browser window
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1000,
        minHeight: 700,
        show: false,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
            webSecurity: true
        },
        icon: path.join(__dirname, 'assets/icon.png'),
        titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default'
    });

    // Load the app
    if (isDev) {
        mainWindow.loadURL('http://localhost:3000');
        mainWindow.webContents.openDevTools();
    } else {
        mainWindow.loadFile('build/index.html');
    }

    // Show window when ready to prevent visual flash
    mainWindow.once('ready-to-show', () => {
        if (splashWindow) {
            splashWindow.close();
        }
        mainWindow.show();
        
        // Focus on main window
        if (isDev) {
            mainWindow.webContents.openDevTools();
        }
    });

    // Handle window closed
    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Handle external links
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    // Set up application menu
    createApplicationMenu();
}

function createApplicationMenu() {
    const template = [
        {
            label: 'File',
            submenu: [
                {
                    label: 'New Search',
                    accelerator: 'CmdOrCtrl+N',
                    click: () => {
                        mainWindow.webContents.send('menu-new-search');
                    }
                },
                {
                    label: 'Export Results',
                    accelerator: 'CmdOrCtrl+E',
                    click: () => {
                        mainWindow.webContents.send('menu-export');
                    }
                },
                { type: 'separator' },
                {
                    label: process.platform === 'darwin' ? 'Quit JobSpy Pro' : 'Exit',
                    accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
                    click: () => {
                        app.quit();
                    }
                }
            ]
        },
        {
            label: 'Edit',
            submenu: [
                { role: 'undo' },
                { role: 'redo' },
                { type: 'separator' },
                { role: 'cut' },
                { role: 'copy' },
                { role: 'paste' },
                { role: 'selectall' }
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'forceReload' },
                { role: 'toggleDevTools' },
                { type: 'separator' },
                { role: 'resetZoom' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
                { type: 'separator' },
                { role: 'togglefullscreen' }
            ]
        },
        {
            label: 'Help',
            submenu: [
                {
                    label: 'About JobSpy Pro',
                    click: () => {
                        showAboutDialog();
                    }
                },
                {
                    label: 'License Information',
                    click: () => {
                        showLicenseDialog();
                    }
                },
                {
                    label: 'Support',
                    click: () => {
                        shell.openExternal('https://jobspy.com/support');
                    }
                }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

async function showLicenseDialog() {
    const result = await dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'License Management',
        message: 'Manage your JobSpy Pro license',
        buttons: ['Activate License', 'Check Status', 'Cancel'],
        defaultId: 0
    });

    if (result.response === 0) {
        // Show license activation window
        mainWindow.webContents.send('show-license-activation');
    } else if (result.response === 1) {
        // Check license status
        const status = await licenseManager.getLicenseStatus();
        dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: 'License Status',
            message: `License Status: ${status.valid ? 'Valid' : 'Invalid'}\nExpires: ${status.expires || 'Never'}\nFeatures: ${status.features.join(', ')}`
        });
    }
}

function showAboutDialog() {
    dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'About JobSpy Pro',
        message: `JobSpy Pro v${app.getVersion()}`,
        detail: 'Professional job search tool with local processing.\n\nBuilt with Electron and Python.\nCopyright © 2024 JobSpy Inc.'
    });
}

// App event handlers
app.whenReady().then(() => {
    createSplashWindow();
    setTimeout(createWindow, 2000); // Show splash for 2 seconds
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
    contents.on('new-window', (event, navigationUrl) => {
        event.preventDefault();
        shell.openExternal(navigationUrl);
    });
});

// IPC Handlers
ipcMain.handle('get-app-info', async () => {
    return {
        version: app.getVersion(),
        name: app.getName(),
        platform: process.platform,
        arch: process.arch,
        electronVersion: process.versions.electron,
        nodeVersion: process.versions.node,
        isDev: isDev
    };
});

ipcMain.handle('validate-license', async (event, licenseKey) => {
    return await licenseManager.activateLicense(licenseKey);
});

ipcMain.handle('get-license-status', async () => {
    return await licenseManager.getLicenseStatus();
});

ipcMain.handle('search-jobs', async (event, searchParams) => {
    return new Promise((resolve, reject) => {
        const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
        const scriptPath = isDev 
            ? path.join(__dirname, 'src/python')
            : path.join(process.resourcesPath, 'python');

        const options = {
            mode: 'json',
            pythonPath: pythonPath,
            scriptPath: scriptPath,
            args: [JSON.stringify(searchParams)]
        };

        PythonShell.run('job_scraper.py', options, (err, results) => {
            if (err) {
                console.error('Python execution error:', err);
                reject({
                    success: false,
                    error: err.message,
                    details: err.toString()
                });
            } else {
                try {
                    const result = results[0];
                    resolve(result);
                } catch (parseError) {
                    reject({
                        success: false,
                        error: 'Failed to parse Python response',
                        details: parseError.toString()
                    });
                }
            }
        });
    });
});

ipcMain.handle('export-data', async (event, { data, format, filename }) => {
    try {
        const { filePath } = await dialog.showSaveDialog(mainWindow, {
            defaultPath: filename,
            filters: [
                { name: 'CSV files', extensions: ['csv'] },
                { name: 'JSON files', extensions: ['json'] },
                { name: 'All files', extensions: ['*'] }
            ]
        });

        if (filePath) {
            let content;
            if (format === 'csv') {
                content = convertToCSV(data);
            } else {
                content = JSON.stringify(data, null, 2);
            }

            fs.writeFileSync(filePath, content);
            return { success: true, filePath };
        }

        return { success: false, error: 'Export cancelled' };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

// Utility functions
function convertToCSV(data) {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
    
    data.forEach(row => {
        const values = headers.map(header => {
            const value = row[header] || '';
            return typeof value === 'string' && (value.includes(',') || value.includes('"'))
                ? `"${value.replace(/"/g, '""')}"`
                : value;
        });
        csvRows.push(values.join(','));
    });
    
    return csvRows.join('\n');
}

// Handle app updates (if using auto-updater)
if (!isDev) {
    const { autoUpdater } = require('electron-updater');
    
    autoUpdater.checkForUpdatesAndNotify();
    
    autoUpdater.on('update-available', () => {
        dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: 'Update Available',
            message: 'A new version is available. It will be downloaded in the background.',
            buttons: ['OK']
        });
    });
    
    autoUpdater.on('update-downloaded', () => {
        dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: 'Update Ready',
            message: 'Update downloaded. Application will restart to apply the update.',
            buttons: ['Restart Now', 'Later']
        }).then((result) => {
            if (result.response === 0) {
                autoUpdater.quitAndInstall();
            }
        });
    });
}
```

### 4. Security Preload Script (preload.js)

```javascript
const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    // App information
    getAppInfo: () => ipcRenderer.invoke('get-app-info'),
    
    // License management
    validateLicense: (licenseKey) => ipcRenderer.invoke('validate-license', licenseKey),
    getLicenseStatus: () => ipcRenderer.invoke('get-license-status'),
    
    // Job search operations
    searchJobs: (params) => ipcRenderer.invoke('search-jobs', params),
    
    // File operations
    exportData: (data, format, filename) => 
        ipcRenderer.invoke('export-data', { data, format, filename }),
    
    // Menu event listeners
    onMenuAction: (callback) => {
        ipcRenderer.on('menu-new-search', callback);
        ipcRenderer.on('menu-export', callback);
        ipcRenderer.on('show-license-activation', callback);
    },
    
    // Platform detection
    platform: process.platform,
    
    // Version information
    versions: {
        node: process.versions.node,
        chrome: process.versions.chrome,
        electron: process.versions.electron
    }
});

// Security: Remove access to Node.js APIs in renderer process
delete window.require;
delete window.exports;
delete window.module;
```

## Python Integration

### 5. Job Scraper (src/python/job_scraper.py)

```python
#!/usr/bin/env python3
"""
JobSpy Desktop Integration
Provides JSON API interface for Electron frontend
"""

import sys
import json
import os
import traceback
from datetime import datetime
from pathlib import Path

# Add JobSpy to Python path
project_root = Path(__file__).parent.parent.parent.parent / 'JobSpy'
if project_root.exists():
    sys.path.insert(0, str(project_root))

try:
    from jobseeker import scrape_jobs
    import pandas as pd
    JOBSPY_AVAILABLE = True
except ImportError as e:
    JOBSPY_AVAILABLE = False
    IMPORT_ERROR = str(e)

def validate_license():
    """Check if this is a licensed version"""
    try:
        from license_validator import LicenseValidator
        validator = LicenseValidator()
        return validator.is_valid()
    except ImportError:
        return False  # Free version

def get_feature_limits():
    """Get feature limitations based on license"""
    if validate_license():
        return {
            'max_results': 1000,
            'max_sites': 10,
            'export_enabled': True,
            'history_enabled': True
        }
    else:
        return {
            'max_results': 20,
            'max_sites': 1,
            'export_enabled': False,
            'history_enabled': False
        }

def search_jobs_desktop(params):
    """Execute job search with license validation"""
    try:
        limits = get_feature_limits()
        
        # Apply license limitations
        if params.get('results_wanted', 20) > limits['max_results']:
            return {
                'success': False,
                'error': 'License limitation exceeded',
                'message': f'Free version limited to {limits["max_results"]} results. Upgrade to Pro for unlimited searches.',
                'upgrade_required': True
            }
        
        if not JOBSPY_AVAILABLE:
            return {
                'success': False,
                'error': 'JobSpy not available',
                'details': f'Import error: {IMPORT_ERROR}',
                'suggestion': 'Please ensure JobSpy is installed: pip install -e /path/to/JobSpy'
            }
        
        # Extract parameters
        site_name = params.get('site_name', 'indeed')
        search_term = params.get('search_term', '').strip()
        location = params.get('location', '').strip()
        results_wanted = min(int(params.get('results_wanted', 20)), limits['max_results'])
        
        # Determine country
        country = 'taiwan' if any(keyword in location.lower() 
                                for keyword in ['taiwan', 'taipei', '台灣', '台北']) else 'usa'
        
        print(f"Starting job search: {site_name}, term='{search_term}', location='{location}', count={results_wanted}")
        
        # Execute JobSpy search
        start_time = datetime.now()
        
        df = scrape_jobs(
            site_name=site_name,
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            country_indeed=country,
            verbose=1
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Process results
        if df.empty:
            return {
                'success': True,
                'jobs': [],
                'count': 0,
                'message': 'No jobs found matching your criteria',
                'execution_time': f'{execution_time:.2f}s',
                'license_info': {
                    'is_pro': validate_license(),
                    'limits': limits
                }
            }
        
        # Convert to JSON format
        jobs = df.to_dict('records')
        
        # Clean job data
        cleaned_jobs = []
        for job in jobs:
            cleaned_job = {
                'title': str(job.get('title', 'N/A')),
                'company': str(job.get('company', 'N/A')),
                'location': str(job.get('location', 'N/A')),
                'description': str(job.get('description', 'No description available'))[:500],
                'salary': str(job.get('salary', 'Not specified')),
                'job_type': str(job.get('job_type', 'Not specified')),
                'date_posted': str(job.get('date_posted', 'Unknown')),
                'job_url': str(job.get('job_url', '')),
                'site': str(job.get('site', site_name)),
                'scraped_at': datetime.now().isoformat()
            }
            cleaned_jobs.append(cleaned_job)
        
        return {
            'success': True,
            'jobs': cleaned_jobs,
            'count': len(cleaned_jobs),
            'message': f'Successfully found {len(cleaned_jobs)} jobs',
            'execution_time': f'{execution_time:.2f}s',
            'platform': site_name,
            'license_info': {
                'is_pro': validate_license(),
                'limits': limits
            }
        }
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in search_jobs_desktop: {error_details}")
        
        return {
            'success': False,
            'error': str(e),
            'details': error_details
        }

def main():
    """Main entry point"""
    try:
        if len(sys.argv) < 2:
            result = {
                'success': False,
                'error': 'No parameters provided',
                'usage': 'python job_scraper.py <json_params>'
            }
            print(json.dumps(result))
            return
        
        params_json = sys.argv[1]
        params = json.loads(params_json)
        
        result = search_jobs_desktop(params)
        print(json.dumps(result))
        
    except json.JSONDecodeError as e:
        error_result = {
            'success': False,
            'error': 'Invalid JSON parameters',
            'details': str(e)
        }
        print(json.dumps(error_result))
    
    except Exception as e:
        error_result = {
            'success': False,
            'error': 'Unexpected error',
            'details': traceback.format_exc()
        }
        print(json.dumps(error_result))

if __name__ == '__main__':
    main()
```

## Development Workflow

### 6. Development Scripts

```bash
# Start development environment
npm run electron-dev

# Build for production
npm run build

# Package for current platform
npm run pack

# Create distributable packages
npm run dist

# Platform-specific builds
npm run dist-win
npm run dist-mac
npm run dist-linux
```

### 7. Testing Setup

```bash
# Install testing dependencies
npm install --save-dev jest electron-builder
npm install --save-dev spectron  # For E2E testing

# Add test scripts to package.json
"test": "jest",
"test:e2e": "jest --config=jest.e2e.config.js"
```

## Security Considerations

### 8. Application Security

1. **Code Signing**
   - Windows: Code signing certificate
   - macOS: Developer ID certificate
   - Linux: GPG signatures

2. **Update Security**
   - Secure update server
   - Signature verification
   - Rollback capabilities

3. **License Protection**
   - Hardware fingerprinting
   - Server-side validation
   - Anti-tampering measures

## Next Steps

1. **Follow the setup guide step by step**
2. **Test the basic application structure**
3. **Integrate with your existing JobSpy codebase**
4. **Implement license validation system**
5. **Add premium features and UI**
6. **Set up build and distribution pipeline**

This desktop application provides the foundation for a professional, licensable product that leverages local computing power while maintaining revenue generation through licensing and premium features.