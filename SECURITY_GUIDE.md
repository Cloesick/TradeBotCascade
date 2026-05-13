# 🔐 Security & Authentication Guide

## Overview

TradeBotCascade implements enterprise-grade security with:
- ✅ JWT-based authentication
- ✅ Role-based access control (RBAC)
- ✅ Password hashing with bcrypt
- ✅ API key authentication
- ✅ Account lockout protection
- ✅ Secure token management

---

## 🎭 User Roles

### **1. VIEWER** (Default)
**Permissions:**
- ✅ View portfolio summary
- ✅ View positions
- ✅ Get ML predictions
- ✅ View stock data
- ✅ View technical analysis
- ❌ Cannot trade
- ❌ Cannot train models
- ❌ Cannot modify portfolio

### **2. TRADER**
**Permissions:**
- ✅ All VIEWER permissions
- ✅ Add/close positions
- ✅ Train ML models
- ✅ Optimize portfolio
- ✅ Execute trades
- ❌ Cannot manage users

### **3. ADMIN**
**Permissions:**
- ✅ All TRADER permissions
- ✅ Manage users
- ✅ Change user roles
- ✅ Enable/disable accounts
- ✅ View all users

---

## 🔑 Authentication Methods

### **Method 1: JWT Tokens (Recommended for Web/Mobile)**

#### **Register New User**
```bash
POST /auth/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

**Response:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "viewer",
  "disabled": false,
  "created_at": "2026-05-13T08:22:00"
}
```

---

#### **Login**
```bash
POST /auth/login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Token Expiration:**
- Access Token: 30 minutes
- Refresh Token: 7 days

---

#### **Using Access Token**
```bash
GET /portfolio/summary
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**PowerShell Example:**
```powershell
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
$headers = @{
    "Authorization" = "Bearer $token"
}
Invoke-RestMethod -Uri "http://localhost:8000/portfolio/summary" -Headers $headers
```

**cURL Example:**
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     http://localhost:8000/portfolio/summary
```

---

#### **Refresh Token**
```bash
POST /auth/refresh?refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "access_token": "new_access_token...",
  "refresh_token": "new_refresh_token...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

### **Method 2: API Keys (Recommended for Bots/Scripts)**

#### **Create API Key**
```bash
POST /auth/api-key?key_name=my_trading_bot
Authorization: Bearer your_jwt_token
```

**Response:**
```json
{
  "success": true,
  "api_key": "tbk_xxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "message": "API key created successfully. Store it securely - it won't be shown again!"
}
```

⚠️ **Important:** API key is shown only once. Store it securely!

---

#### **Using API Key**
```bash
GET /portfolio/summary
X-API-Key: tbk_xxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**PowerShell Example:**
```powershell
$headers = @{
    "X-API-Key" = "tbk_xxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
Invoke-RestMethod -Uri "http://localhost:8000/portfolio/summary" -Headers $headers
```

**Python Example:**
```python
import requests

headers = {
    "X-API-Key": "tbk_xxxxxxxxxxxxxxxxxxxxxxxxxxx"
}

response = requests.get(
    "http://localhost:8000/portfolio/summary",
    headers=headers
)
```

---

## 🛡️ Security Features

### **1. Password Security**
- ✅ Bcrypt hashing (industry standard)
- ✅ Automatic salt generation
- ✅ Password strength validation
- ✅ No plain-text storage

### **2. Account Lockout**
- ✅ 5 failed login attempts → 30-minute lockout
- ✅ Automatic unlock after timeout
- ✅ Counter reset on successful login

**Lockout Response:**
```json
{
  "detail": "Account locked until 2026-05-13T09:00:00"
}
```

### **3. Token Security**
- ✅ JWT with HS256 algorithm
- ✅ Short-lived access tokens (30 min)
- ✅ Refresh tokens for renewal
- ✅ Token type validation
- ✅ Expiration checking

### **4. API Key Security**
- ✅ SHA-256 hashing
- ✅ Prefix format: `tbk_`
- ✅ 32-character random string
- ✅ One-time display
- ✅ Secure storage

---

## 📋 Endpoint Security Matrix

| Endpoint | Public | VIEWER | TRADER | ADMIN |
|----------|--------|--------|--------|-------|
| **Authentication** |
| `POST /auth/register` | ✅ | ✅ | ✅ | ✅ |
| `POST /auth/login` | ✅ | ✅ | ✅ | ✅ |
| `POST /auth/refresh` | ✅ | ✅ | ✅ | ✅ |
| `GET /auth/me` | ❌ | ✅ | ✅ | ✅ |
| `POST /auth/api-key` | ❌ | ✅ | ✅ | ✅ |
| `GET /auth/users` | ❌ | ❌ | ❌ | ✅ |
| `PUT /auth/users/{username}/role` | ❌ | ❌ | ❌ | ✅ |
| `PUT /auth/users/{username}/disable` | ❌ | ❌ | ❌ | ✅ |
| **Public Endpoints** |
| `GET /` | ✅ | ✅ | ✅ | ✅ |
| `GET /stock/{symbol}` | ✅ | ✅ | ✅ | ✅ |
| `GET /signals/{symbol}` | ✅ | ✅ | ✅ | ✅ |
| **Portfolio** |
| `GET /portfolio/summary` | ❌ | ✅ | ✅ | ✅ |
| `GET /portfolio/positions` | ❌ | ✅ | ✅ | ✅ |
| `POST /portfolio/position` | ❌ | ❌ | ✅ | ✅ |
| `DELETE /portfolio/position/{symbol}` | ❌ | ❌ | ✅ | ✅ |
| `POST /portfolio/optimize` | ❌ | ❌ | ✅ | ✅ |
| **Machine Learning** |
| `POST /ml/train/{symbol}` | ❌ | ❌ | ✅ | ✅ |
| `GET /ml/predict/{symbol}` | ❌ | ✅ | ✅ | ✅ |

---

## 👥 User Management (Admin Only)

### **List All Users**
```bash
GET /auth/users
Authorization: Bearer admin_token
```

**Response:**
```json
{
  "users": [
    {
      "username": "admin",
      "email": "admin@tradebotcascade.com",
      "role": "admin",
      "disabled": false
    },
    {
      "username": "johndoe",
      "email": "john@example.com",
      "role": "viewer",
      "disabled": false
    }
  ],
  "count": 2
}
```

---

### **Change User Role**
```bash
PUT /auth/users/johndoe/role?new_role=trader
Authorization: Bearer admin_token
```

**Response:**
```json
{
  "success": true,
  "message": "User johndoe role updated to trader"
}
```

---

### **Disable User Account**
```bash
PUT /auth/users/johndoe/disable?disabled=true
Authorization: Bearer admin_token
```

**Response:**
```json
{
  "success": true,
  "message": "User johndoe disabled"
}
```

---

## 🔐 Default Credentials

**Default Admin Account:**
- Username: `admin`
- Password: `Admin123!`
- Role: `admin`

⚠️ **IMPORTANT:** Change the default admin password immediately in production!

---

## 🚀 Quick Start Examples

### **Example 1: Register and Login**

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader1",
    "email": "trader1@example.com",
    "password": "SecurePass123!",
    "full_name": "Trader One"
  }'

# 2. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader1",
    "password": "SecurePass123!"
  }'

# 3. Use token
TOKEN="your_access_token_here"
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/auth/me
```

---

### **Example 2: Admin Workflow**

```bash
# 1. Login as admin
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123!"
  }'

# 2. Promote user to trader
ADMIN_TOKEN="admin_access_token"
curl -X PUT "http://localhost:8000/auth/users/trader1/role?new_role=trader" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 3. List all users
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     http://localhost:8000/auth/users
```

---

### **Example 3: Trading with API Key**

```bash
# 1. Login and get token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"trader1","password":"SecurePass123!"}' \
  | jq -r '.access_token')

# 2. Create API key
API_KEY=$(curl -X POST "http://localhost:8000/auth/api-key?key_name=my_bot" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.api_key')

# 3. Use API key for trading
curl -X POST "http://localhost:8000/portfolio/position?symbol=AAPL&shares=10&price=175.50" \
  -H "X-API-Key: $API_KEY"
```

---

## 🛠️ Production Deployment

### **Environment Variables**

Create `.env` file:
```bash
# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database (when implemented)
DATABASE_URL=postgresql://user:password@localhost/tradebotcascade

# API Keys
ALPHA_VANTAGE_API_KEY=your_api_key
```

---

### **Security Checklist**

- [ ] Change default admin password
- [ ] Set strong SECRET_KEY (32+ characters)
- [ ] Enable HTTPS/TLS
- [ ] Set up database for user persistence
- [ ] Enable rate limiting
- [ ] Set up logging and monitoring
- [ ] Configure CORS for production domains
- [ ] Implement session management
- [ ] Add 2FA (optional)
- [ ] Set up backup and recovery

---

## 🔍 Security Best Practices

### **For Users:**
1. ✅ Use strong, unique passwords
2. ✅ Store API keys securely (environment variables, secrets manager)
3. ✅ Never commit API keys to version control
4. ✅ Rotate API keys regularly
5. ✅ Use HTTPS in production
6. ✅ Log out when done

### **For Developers:**
1. ✅ Never log passwords or tokens
2. ✅ Use environment variables for secrets
3. ✅ Implement rate limiting
4. ✅ Validate all inputs
5. ✅ Keep dependencies updated
6. ✅ Use HTTPS/TLS in production
7. ✅ Implement proper error handling
8. ✅ Regular security audits

---

## 🚨 Troubleshooting

### **401 Unauthorized**
```json
{"detail": "Could not validate credentials"}
```
**Solutions:**
- Check if token is valid
- Check if token has expired
- Ensure "Bearer " prefix in Authorization header
- Verify API key format

### **403 Forbidden**
```json
{"detail": "Insufficient permissions. Required role: trader"}
```
**Solutions:**
- Check your user role
- Contact admin to upgrade role
- Use correct endpoint for your role

### **423 Locked**
```json
{"detail": "Account locked until 2026-05-13T09:00:00"}
```
**Solutions:**
- Wait for lockout period to expire
- Contact admin to unlock account
- Ensure correct password

---

## 📊 Security Metrics

**Current Implementation:**
- ✅ Password Hashing: Bcrypt
- ✅ Token Algorithm: HS256 (JWT)
- ✅ API Key Hashing: SHA-256
- ✅ Account Lockout: 5 attempts / 30 min
- ✅ Token Expiry: 30 min (access), 7 days (refresh)
- ✅ Role-Based Access: 3 levels
- ✅ Password Strength: Enforced

---

## 🎯 Next Steps

1. **Test Authentication:**
   ```bash
   # Register → Login → Access Protected Endpoint
   ```

2. **Create API Key:**
   ```bash
   # For automated trading bots
   ```

3. **Upgrade to TRADER:**
   ```bash
   # Contact admin or use admin account
   ```

4. **Start Trading:**
   ```bash
   # With proper authentication
   ```

---

**Security Version:** 1.0  
**Last Updated:** May 13, 2026  
**Status:** Production Ready ✅
