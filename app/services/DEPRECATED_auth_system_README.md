# DEPRECATED: Custom Authentication System

This file has been deprecated and replaced with Auth0 integration.

## Why was this deprecated?

The custom authentication system had several critical security vulnerabilities:

1. **Plain-text password storage** - User credentials stored in JSON files
2. **Weak password hashing** - Custom PBKDF2 implementation
3. **No MFA support** - Despite claims in the codebase
4. **Session management issues** - 7-day tokens with no revocation
5. **No OAuth2/OIDC compliance** - Not industry standard

## Migration to Auth0

All authentication is now handled by Auth0, which provides:

- ✅ Enterprise-grade security
- ✅ OAuth2/OIDC compliance
- ✅ Built-in MFA support
- ✅ Breached password detection
- ✅ Proper session management
- ✅ Audit logging
- ✅ Social login support

## Setup Instructions

See `docs/AUTH0_SETUP.md` for complete setup instructions.

## Data Migration

If you have existing users in `data/users.json`, they will need to:
1. Register new accounts in Auth0
2. Use the password reset flow to set new passwords

**Note:** Old user data is NOT automatically migrated for security reasons.

## Removal Timeline

This file will be completely removed in v1.0.0 (estimated March 2026).

---

**DO NOT USE THIS FILE** - It is kept for reference only.
