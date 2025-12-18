# Auth0 Password Policy Configuration Guide

## Overview
This guide explains how to configure Auth0 password policies to meet enterprise security requirements.

## Accessing Password Policy Settings

1. Log in to your Auth0 Dashboard: https://manage.auth0.com
2. Navigate to **Security** → **Attack Protection**
3. Click on **Password Policy**

---

## Recommended Password Policy

### Password Strength
Configure the following settings:

**Minimum Length:** 12 characters
- Balances security with usability
- Prevents brute force attacks

**Character Requirements:**
- ✅ At least one lowercase letter (a-z)
- ✅ At least one uppercase letter (A-Z)
- ✅ At least one number (0-9)
- ✅ At least one special character (!@#$%^&*)

**Password Complexity:** Good
- Auth0 provides three levels: None, Fair, Good, Excellent
- "Good" is recommended for most applications

### Password History
**Enable Password History:** Yes
**Number of passwords to remember:** 5

This prevents users from reusing their last 5 passwords.

### Password Expiration (Optional)
**Enable Password Expiration:** Optional
**Days until expiration:** 90 days

> [!NOTE]
> NIST guidelines now recommend against forced password expiration unless there's evidence of compromise. Consider your compliance requirements.

---

## Breached Password Detection

### Enable Breached Password Detection
1. Navigate to **Security** → **Attack Protection**
2. Click on **Breached Password Detection**
3. Toggle **Enable** to ON

**Settings:**
- **Action on Breached Password:** Block
- **Notification:** Send email to user

This feature checks passwords against databases of known breached passwords (e.g., Have I Been Pwned).

---

## Multi-Factor Authentication (MFA)

### Enable MFA
1. Navigate to **Security** → **Multi-factor Auth**
2. Enable **One-time Password** (recommended)
3. Optional: Enable **SMS**, **Push Notifications**, or **Email**

**MFA Policy Options:**
- **Never:** MFA is optional
- **Always:** MFA required for all users (recommended for production)
- **Adaptive:** MFA required based on risk assessment

**Recommended:** Set to "Always" for production environments

---

## Suspicious IP Throttling

1. Navigate to **Security** → **Attack Protection**
2. Click on **Suspicious IP Throttling**
3. Toggle **Enable** to ON

**Settings:**
- **Allowlist:** Add trusted IP addresses (optional)
- **Block:** Automatically block suspicious IPs

---

## Bot Detection

1. Navigate to **Security** → **Attack Protection**
2. Click on **Bot Detection**
3. Toggle **Enable** to ON

This uses CAPTCHA to prevent automated attacks.

---

## Configuration via Management API

You can also configure password policies programmatically:

```javascript
// Example: Update password policy via Management API
const ManagementClient = require('auth0').ManagementClient;

const management = new ManagementClient({
  domain: 'your-tenant.auth0.com',
  clientId: 'YOUR_CLIENT_ID',
  clientSecret: 'YOUR_CLIENT_SECRET'
});

// Update connection password policy
management.updateConnection(
  { id: 'con_YOUR_CONNECTION_ID' },
  {
    options: {
      password_policy: 'good',
      password_history: {
        enable: true,
        size: 5
      },
      password_no_personal_info: {
        enable: true
      },
      password_dictionary: {
        enable: true,
        dictionary: ['password', '123456', 'qwerty']
      }
    }
  }
);
```

---

## Testing Password Policy

### Test Weak Passwords
Try creating an account with these passwords (they should be rejected):

- ❌ `password123` - Too common
- ❌ `12345678` - No letters
- ❌ `abcdefgh` - No numbers or special chars
- ❌ `Test123` - Too short (if min length is 12)

### Test Strong Passwords
These should be accepted:

- ✅ `MyP@ssw0rd2024!`
- ✅ `Secure#Pass123`
- ✅ `Tr0ub4dor&3`

---

## Compliance Requirements

### NIST 800-63B Guidelines
- ✅ Minimum 8 characters (we use 12)
- ✅ Check against breached password databases
- ✅ No composition rules required (but we add them for extra security)
- ✅ No mandatory password expiration

### PCI DSS Requirements
- ✅ Minimum 7 characters (we use 12)
- ✅ Alphanumeric and special characters
- ✅ Password history (5 passwords)
- ✅ 90-day expiration (optional)

### HIPAA Requirements
- ✅ Unique user identification
- ✅ Emergency access procedures
- ✅ Automatic logoff
- ✅ Encryption and decryption

---

## Monitoring and Alerts

### Set Up Alerts
1. Navigate to **Monitoring** → **Logs**
2. Create log streams for:
   - Failed login attempts
   - Breached password detections
   - MFA enrollment/usage
   - Password changes

### Recommended Alerts
- 5+ failed login attempts from same IP
- Breached password detected
- MFA disabled by user
- Password changed without MFA

---

## User Communication

### Email Templates
Customize email templates for:
1. **Password Reset:** `Security` → `Email Templates` → `Change Password`
2. **Breached Password:** `Security` → `Email Templates` → `Breached Password`
3. **MFA Enrollment:** `Security` → `Email Templates` → `MFA Enrollment`

### Sample Password Requirements Message
```
Your password must:
• Be at least 12 characters long
• Contain uppercase and lowercase letters
• Include at least one number
• Include at least one special character (!@#$%^&*)
• Not match your last 5 passwords
• Not be a commonly breached password
```

---

## Implementation Checklist

- [ ] Set minimum password length to 12 characters
- [ ] Enable all character requirements
- [ ] Set password complexity to "Good"
- [ ] Enable password history (5 passwords)
- [ ] Enable breached password detection
- [ ] Enable MFA (set to "Always" for production)
- [ ] Enable suspicious IP throttling
- [ ] Enable bot detection
- [ ] Customize email templates
- [ ] Set up monitoring and alerts
- [ ] Test password policy with various passwords
- [ ] Document policy for users

---

## Additional Resources

- [Auth0 Password Strength Documentation](https://auth0.com/docs/secure/attack-protection/password-strength)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [Have I Been Pwned API](https://haveibeenpwned.com/API/v3)

---

**Last Updated:** December 18, 2025
**Recommended Review:** Quarterly
