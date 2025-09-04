# License Server Implementation Guide

## Overview

Complete license validation server to prevent piracy and manage JobSpy Pro licenses.

## Architecture

```
License Server
├── License Validation API
├── Hardware Fingerprinting
├── Admin Dashboard
└── Analytics Tracking
```

## Quick Setup

### 1. Project Structure
```
license-server/
├── src/
│   ├── controllers/licenseController.ts
│   ├── services/licenseService.ts
│   ├── routes/license.ts
│   └── app.ts
├── config/database.sql
├── package.json
└── .env
```

### 2. Database Schema (config/database.sql)
```sql
CREATE DATABASE jobspy_licenses;

-- License types
CREATE TABLE license_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    max_activations INTEGER DEFAULT 1,
    features JSONB,
    price DECIMAL(10,2)
);

INSERT INTO license_types (name, max_activations, features, price) VALUES
('FREE', 1, '{"max_results": 20, "export": false}', 0.00),
('PRO', 3, '{"max_results": 1000, "export": true}', 29.99),
('ENTERPRISE', 50, '{"max_results": -1, "api_access": true}', 199.00);

-- Licenses
CREATE TABLE licenses (
    id SERIAL PRIMARY KEY,
    license_key VARCHAR(255) UNIQUE NOT NULL,
    license_type_id INTEGER REFERENCES license_types(id),
    status VARCHAR(50) DEFAULT 'active',
    activations_used INTEGER DEFAULT 0,
    max_activations INTEGER DEFAULT 1,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hardware fingerprints
CREATE TABLE hardware_fingerprints (
    id SERIAL PRIMARY KEY,
    license_id INTEGER REFERENCES licenses(id),
    hardware_hash VARCHAR(255) NOT NULL,
    platform VARCHAR(50),
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(license_id, hardware_hash)
);

-- Validation logs
CREATE TABLE license_validations (
    id SERIAL PRIMARY KEY,
    license_id INTEGER REFERENCES licenses(id),
    hardware_hash VARCHAR(255),
    ip_address INET,
    result VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Core License Service (src/services/licenseService.ts)
```typescript
import crypto from 'crypto';
import { Pool } from 'pg';

export class LicenseService {
    private db: Pool;

    constructor(db: Pool) {
        this.db = db;
    }

    // Generate license key with checksum
    generateLicenseKey(licenseTypeId: number, userId: number): string {
        const timestamp = Date.now().toString(36);
        const random = crypto.randomBytes(8).toString('hex');
        const checksum = this.calculateChecksum(`${licenseTypeId}-${userId}-${timestamp}`);
        
        return [timestamp, licenseTypeId.toString(36), userId.toString(36), random, checksum]
            .join('-').toUpperCase();
    }

    // Validate license activation
    async validateLicense(licenseKey: string, hardwareHash: string, ipAddress: string) {
        try {
            // Get license info
            const licenseResult = await this.db.query(`
                SELECT l.*, lt.features, lt.max_activations
                FROM licenses l
                JOIN license_types lt ON l.license_type_id = lt.id
                WHERE l.license_key = $1 AND l.status = 'active'
            `, [licenseKey]);

            if (licenseResult.rows.length === 0) {
                await this.logValidation(null, hardwareHash, ipAddress, 'not_found');
                return { valid: false, error: 'License not found or inactive' };
            }

            const license = licenseResult.rows[0];

            // Check expiration
            if (license.expires_at && new Date(license.expires_at) < new Date()) {
                await this.logValidation(license.id, hardwareHash, ipAddress, 'expired');
                return { valid: false, error: 'License expired' };
            }

            // Check hardware fingerprint
            const hardwareCheck = await this.checkHardwareLimit(license.id, hardwareHash, license.max_activations);
            
            if (!hardwareCheck.allowed) {
                await this.logValidation(license.id, hardwareHash, ipAddress, 'hardware_limit');
                return { 
                    valid: false, 
                    error: `Activation limit exceeded (${hardwareCheck.count}/${license.max_activations})` 
                };
            }

            // Update hardware fingerprint
            await this.updateHardwareFingerprint(license.id, hardwareHash);

            await this.logValidation(license.id, hardwareHash, ipAddress, 'success');

            return {
                valid: true,
                features: license.features,
                expiresAt: license.expires_at,
                licenseType: license.license_type_id
            };

        } catch (error) {
            console.error('License validation error:', error);
            return { valid: false, error: 'Internal server error' };
        }
    }

    // Create new license
    async createLicense(userId: number, licenseTypeId: number): Promise<string> {
        const licenseKey = this.generateLicenseKey(licenseTypeId, userId);
        
        await this.db.query(`
            INSERT INTO licenses (license_key, license_type_id, max_activations)
            SELECT $1, $2, lt.max_activations 
            FROM license_types lt WHERE lt.id = $2
        `, [licenseKey, licenseTypeId]);

        return licenseKey;
    }

    // Check hardware activation limits
    private async checkHardwareLimit(licenseId: number, hardwareHash: string, maxActivations: number) {
        // Check if hardware already exists
        const existing = await this.db.query(
            'SELECT id FROM hardware_fingerprints WHERE license_id = $1 AND hardware_hash = $2',
            [licenseId, hardwareHash]
        );

        if (existing.rows.length > 0) {
            return { allowed: true, count: existing.rows.length };
        }

        // Check total activations
        const countResult = await this.db.query(
            'SELECT COUNT(*) as count FROM hardware_fingerprints WHERE license_id = $1',
            [licenseId]
        );

        const currentCount = parseInt(countResult.rows[0].count);
        return { 
            allowed: currentCount < maxActivations, 
            count: currentCount 
        };
    }

    // Update hardware fingerprint
    private async updateHardwareFingerprint(licenseId: number, hardwareHash: string) {
        await this.db.query(`
            INSERT INTO hardware_fingerprints (license_id, hardware_hash, last_seen)
            VALUES ($1, $2, CURRENT_TIMESTAMP)
            ON CONFLICT (license_id, hardware_hash)
            DO UPDATE SET last_seen = CURRENT_TIMESTAMP
        `, [licenseId, hardwareHash]);

        // Update activation count
        await this.db.query(`
            UPDATE licenses 
            SET activations_used = (
                SELECT COUNT(*) FROM hardware_fingerprints WHERE license_id = $1
            )
            WHERE id = $1
        `, [licenseId]);
    }

    // Log validation attempts
    private async logValidation(licenseId: number | null, hardwareHash: string, ipAddress: string, result: string) {
        await this.db.query(`
            INSERT INTO license_validations (license_id, hardware_hash, ip_address, result)
            VALUES ($1, $2, $3, $4)
        `, [licenseId, hardwareHash, ipAddress, result]);
    }

    // Calculate checksum for license validation
    private calculateChecksum(data: string): string {
        return crypto.createHash('md5').update(data).digest('hex').substring(0, 4).toUpperCase();
    }
}
```

### 4. License Controller (src/controllers/licenseController.ts)
```typescript
import { Request, Response } from 'express';
import { LicenseService } from '../services/licenseService';

export class LicenseController {
    private licenseService: LicenseService;

    constructor(licenseService: LicenseService) {
        this.licenseService = licenseService;
    }

    // Validate license endpoint
    async validateLicense(req: Request, res: Response) {
        try {
            const { licenseKey, hardwareId } = req.body;

            if (!licenseKey || !hardwareId) {
                return res.status(400).json({
                    valid: false,
                    error: 'License key and hardware ID required'
                });
            }

            // Create hardware hash
            const crypto = require('crypto');
            const hardwareHash = crypto.createHash('sha256').update(hardwareId).digest('hex');
            const ipAddress = req.ip || req.connection.remoteAddress;

            const result = await this.licenseService.validateLicense(licenseKey, hardwareHash, ipAddress);

            res.status(result.valid ? 200 : 400).json(result);

        } catch (error) {
            console.error('Validation error:', error);
            res.status(500).json({
                valid: false,
                error: 'Internal server error'
            });
        }
    }

    // Generate license (admin only)
    async generateLicense(req: Request, res: Response) {
        try {
            const { userId, licenseTypeId } = req.body;

            const licenseKey = await this.licenseService.createLicense(userId, licenseTypeId);

            res.json({
                success: true,
                licenseKey
            });

        } catch (error) {
            console.error('Generation error:', error);
            res.status(500).json({
                error: 'Failed to generate license'
            });
        }
    }
}
```

### 5. Main Application (src/app.ts)
```typescript
import express from 'express';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import { Pool } from 'pg';
import { LicenseService } from './services/licenseService';
import { LicenseController } from './controllers/licenseController';

const app = express();

// Database connection
const db = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'jobspy_licenses',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD
});

// Middleware
app.use(cors());
app.use(express.json());

// Rate limiting
const limiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 10 // limit each IP to 10 requests per minute
});
app.use('/api/license/validate', limiter);

// Initialize services
const licenseService = new LicenseService(db);
const licenseController = new LicenseController(licenseService);

// Routes
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

app.post('/api/license/validate', (req, res) => {
    licenseController.validateLicense(req, res);
});

app.post('/api/admin/generate-license', (req, res) => {
    licenseController.generateLicense(req, res);
});

// Start server
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
    console.log(`License server running on port ${PORT}`);
});
```

### 6. Package.json
```json
{
  "name": "jobspy-license-server",
  "version": "1.0.0",
  "scripts": {
    "start": "node dist/app.js",
    "dev": "ts-node src/app.ts",
    "build": "tsc",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "express-rate-limit": "^6.7.0",
    "pg": "^8.11.0",
    "typescript": "^5.0.0",
    "ts-node": "^10.9.0"
  },
  "devDependencies": {
    "@types/express": "^4.17.17",
    "@types/node": "^20.0.0",
    "@types/pg": "^8.10.0"
  }
}
```

### 7. Environment Variables (.env)
```env
NODE_ENV=production
PORT=3001

# Database
DB_HOST=your-postgres-host
DB_PORT=5432
DB_NAME=jobspy_licenses
DB_USER=postgres
DB_PASSWORD=your-password

# Security
JWT_SECRET=your-secret-key
```

## Deployment

### 8. Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway create jobspy-license-server
railway add postgresql
railway up

# Set environment variables
railway variables set NODE_ENV=production
railway variables set DB_HOST=${{Postgres.PGHOST}}
railway variables set DB_PASSWORD=${{Postgres.PGPASSWORD}}
```

## Usage

### 9. Client Integration
```javascript
// In desktop app license validation
class LicenseManager {
    async validateLicense(licenseKey) {
        const hardwareId = this.getHardwareFingerprint();
        
        const response = await fetch('https://your-license-server.up.railway.app/api/license/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ licenseKey, hardwareId })
        });

        return await response.json();
    }

    getHardwareFingerprint() {
        const os = require('os');
        const crypto = require('crypto');
        
        const identifiers = [
            os.hostname(),
            os.cpus()[0].model,
            os.totalmem().toString()
        ];

        return crypto.createHash('sha256')
            .update(identifiers.join('|'))
            .digest('hex');
    }
}
```

## Security Features

- **Hardware Fingerprinting**: Device-specific activation
- **Rate Limiting**: Prevents brute force attacks
- **License Key Validation**: Checksum verification
- **Activation Limits**: Controls concurrent usage
- **Audit Logging**: Tracks all validation attempts

This license server provides robust protection against piracy while enabling legitimate users to activate and use JobSpy Pro across their authorized devices.