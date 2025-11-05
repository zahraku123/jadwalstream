/**
 * JadwalStream License Management System
 * Google Apps Script for License Generation and Validation
 * 
 * Setup:
 * 1. Create new Google Sheet with name "JadwalStream_Licenses"
 * 2. Go to Extensions > Apps Script
 * 3. Copy this code to Code.gs
 * 4. Deploy as Web App
 * 5. Set access to "Anyone" or specific users
 */

// Configuration
const SHEET_NAME = 'Licenses';
const API_KEY = 'YOUR_SECRET_API_KEY_HERE'; // Change this!

/**
 * Initialize spreadsheet with headers
 */
function initializeSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
  }
  
  // Set headers
  const headers = [
    'License Key',
    'Email',
    'HWID',
    'Status',
    'Created Date',
    'Activated Date',
    'Expiry Date',
    'Duration (Days)',
    'Last Check',
    'Notes'
  ];
  
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
  sheet.setFrozenRows(1);
  
  // Auto-resize columns
  for (let i = 1; i <= headers.length; i++) {
    sheet.autoResizeColumn(i);
  }
  
  Logger.log('Sheet initialized successfully');
}

/**
 * Generate random license key
 */
function generateLicenseKey() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let key = '';
  
  for (let i = 0; i < 4; i++) {
    let part = '';
    for (let j = 0; j < 5; j++) {
      part += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    key += (i > 0 ? '-' : '') + part;
  }
  
  return key;
}

/**
 * Admin: Generate new license
 * Can be called from sheet or via API
 */
function generateLicense(email, durationDays, notes) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET_NAME);
  
  if (!sheet) {
    initializeSheet();
    return generateLicense(email, durationDays, notes);
  }
  
  // Generate license key
  const licenseKey = generateLicenseKey();
  const createdDate = new Date();
  
  // Add to sheet
  const rowData = [
    licenseKey,
    email || '',
    '',  // HWID (empty until activated)
    'pending',  // Status
    Utilities.formatDate(createdDate, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss'),
    '',  // Activated Date
    '',  // Expiry Date
    durationDays || 365,
    '',  // Last Check
    notes || ''
  ];
  
  sheet.appendRow(rowData);
  
  Logger.log('License generated: ' + licenseKey);
  return {
    success: true,
    license_key: licenseKey,
    email: email,
    duration_days: durationDays,
    message: 'License generated successfully'
  };
}

/**
 * User: Activate license with HWID
 */
function activateLicense(licenseKey, hwid) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET_NAME);
  
  if (!sheet) {
    return {
      success: false,
      message: 'License system not initialized'
    };
  }
  
  const data = sheet.getDataRange().getValues();
  
  // Find license
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const rowLicenseKey = row[0];
    
    if (rowLicenseKey === licenseKey) {
      const currentHWID = row[2];
      const status = row[3];
      const durationDays = row[7] || 365;
      
      // Check if revoked
      if (status === 'revoked') {
        return {
          success: false,
          message: 'License has been revoked. Contact admin.'
        };
      }
      
      // Check if already activated with different HWID
      if (currentHWID && currentHWID !== hwid) {
        return {
          success: false,
          message: 'License is already activated on another device. Contact admin to reset.'
        };
      }
      
      // Activate license
      const now = new Date();
      const expiryDate = new Date(now.getTime() + (durationDays * 24 * 60 * 60 * 1000));
      
      const rowNum = i + 1;
      sheet.getRange(rowNum, 3).setValue(hwid);  // HWID
      sheet.getRange(rowNum, 4).setValue('active');  // Status
      sheet.getRange(rowNum, 6).setValue(Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss'));  // Activated Date
      sheet.getRange(rowNum, 7).setValue(Utilities.formatDate(expiryDate, Session.getScriptTimeZone(), 'yyyy-MM-dd'));  // Expiry Date
      sheet.getRange(rowNum, 9).setValue(Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss'));  // Last Check
      
      return {
        success: true,
        message: 'License activated successfully',
        license_key: licenseKey,
        hwid: hwid,
        status: 'active',
        activated_date: Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss'),
        expiry_date: Utilities.formatDate(expiryDate, Session.getScriptTimeZone(), 'yyyy-MM-dd'),
        days_remaining: durationDays
      };
    }
  }
  
  return {
    success: false,
    message: 'License key not found. Please check your license key.'
  };
}

/**
 * User: Validate license
 */
function validateLicense(hwid) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET_NAME);
  
  if (!sheet) {
    return {
      success: false,
      message: 'License system not initialized'
    };
  }
  
  const data = sheet.getDataRange().getValues();
  const now = new Date();
  
  // Find license by HWID
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const currentHWID = row[2];
    
    if (currentHWID === hwid) {
      const licenseKey = row[0];
      const status = row[3];
      const expiryDateStr = row[6];
      
      // Check if revoked
      if (status === 'revoked') {
        return {
          success: false,
          message: 'License has been revoked',
          status: 'revoked'
        };
      }
      
      // Parse expiry date
      if (!expiryDateStr) {
        return {
          success: false,
          message: 'License not activated properly'
        };
      }
      
      const expiryDate = new Date(expiryDateStr);
      const daysRemaining = Math.ceil((expiryDate - now) / (1000 * 60 * 60 * 24));
      
      // Update last check
      const rowNum = i + 1;
      sheet.getRange(rowNum, 9).setValue(Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss'));
      
      // Check if expired
      if (daysRemaining < 0) {
        sheet.getRange(rowNum, 4).setValue('expired');
        return {
          success: false,
          message: 'License has expired',
          status: 'expired',
          expired_days: Math.abs(daysRemaining)
        };
      }
      
      return {
        success: true,
        message: 'License is valid',
        license_key: licenseKey,
        hwid: hwid,
        status: 'active',
        expiry_date: Utilities.formatDate(expiryDate, Session.getScriptTimeZone(), 'yyyy-MM-dd'),
        days_remaining: daysRemaining
      };
    }
  }
  
  return {
    success: false,
    message: 'No active license found for this device'
  };
}

/**
 * Admin: Revoke license
 */
function revokeLicense(licenseKey) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET_NAME);
  
  if (!sheet) {
    return { success: false, message: 'Sheet not found' };
  }
  
  const data = sheet.getDataRange().getValues();
  
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === licenseKey) {
      const rowNum = i + 1;
      sheet.getRange(rowNum, 4).setValue('revoked');
      return {
        success: true,
        message: 'License revoked successfully'
      };
    }
  }
  
  return { success: false, message: 'License not found' };
}

/**
 * Admin: Reset HWID (allow reactivation on different device)
 */
function resetHWID(licenseKey) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET_NAME);
  
  if (!sheet) {
    return { success: false, message: 'Sheet not found' };
  }
  
  const data = sheet.getDataRange().getValues();
  
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === licenseKey) {
      const rowNum = i + 1;
      sheet.getRange(rowNum, 3).setValue('');  // Clear HWID
      sheet.getRange(rowNum, 4).setValue('pending');  // Reset status
      sheet.getRange(rowNum, 6).setValue('');  // Clear activated date
      return {
        success: true,
        message: 'HWID reset successfully. License can be activated on new device.'
      };
    }
  }
  
  return { success: false, message: 'License not found' };
}

/**
 * Web App Handler - Main entry point
 */
function doPost(e) {
  try {
    const params = JSON.parse(e.postData.contents);
    const action = params.action;
    const apiKey = params.api_key;
    
    // Verify API key for sensitive operations
    if (action === 'generate' || action === 'revoke' || action === 'reset_hwid') {
      if (apiKey !== API_KEY) {
        return ContentService.createTextOutput(JSON.stringify({
          success: false,
          message: 'Invalid API key'
        })).setMimeType(ContentService.MimeType.JSON);
      }
    }
    
    let result;
    
    switch (action) {
      case 'generate':
        result = generateLicense(params.email, params.duration_days, params.notes);
        break;
        
      case 'activate':
        result = activateLicense(params.license_key, params.hwid);
        break;
        
      case 'validate':
        result = validateLicense(params.hwid);
        break;
        
      case 'revoke':
        result = revokeLicense(params.license_key);
        break;
        
      case 'reset_hwid':
        result = resetHWID(params.license_key);
        break;
        
      default:
        result = {
          success: false,
          message: 'Invalid action'
        };
    }
    
    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      message: 'Error: ' + error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Web App Handler - GET requests (for testing)
 */
function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: 'JadwalStream License System',
    version: '1.0',
    message: 'Use POST requests to interact with the API'
  })).setMimeType(ContentService.MimeType.JSON);
}

/**
 * Create menu for admin functions
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('License Manager')
    .addItem('Initialize Sheet', 'initializeSheet')
    .addItem('Generate License', 'showGenerateLicenseDialog')
    .addItem('Show Web App URL', 'showWebAppURL')
    .addToUi();
}

/**
 * Show dialog to generate license
 */
function showGenerateLicenseDialog() {
  const ui = SpreadsheetApp.getUi();
  const result = ui.prompt(
    'Generate License',
    'Enter email (optional) and duration in days (default: 365):\nFormat: email,days\nExample: user@example.com,365',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (result.getSelectedButton() === ui.Button.OK) {
    const input = result.getResponseText();
    const parts = input.split(',');
    const email = parts[0] ? parts[0].trim() : '';
    const days = parts[1] ? parseInt(parts[1].trim()) : 365;
    
    const license = generateLicense(email, days, 'Generated from UI');
    
    ui.alert(
      'License Generated',
      'License Key: ' + license.license_key + '\n' +
      'Email: ' + (email || 'N/A') + '\n' +
      'Duration: ' + days + ' days',
      ui.ButtonSet.OK
    );
  }
}

/**
 * Show Web App URL
 */
function showWebAppURL() {
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    'Web App URL',
    'After deploying as Web App, you will get a URL like:\n' +
    'https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec\n\n' +
    'Copy that URL and use it in license_validator.py',
    ui.ButtonSet.OK
  );
}
