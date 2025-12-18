# Auth0 Setup Guide

## Prerequisites
- Auth0 account (free tier available at https://auth0.com)
- Application running locally or deployed

## Step 1: Create Auth0 Account
1. Go to https://auth0.com and sign up for a free account
2. Choose a tenant domain (e.g., `myapp.us.auth0.com`)
3. Complete the registration process

## Step 2: Create Application
1. In Auth0 Dashboard, go to **Applications** → **Applications**
2. Click **Create Application**
3. Name: `Terraform Deployment Platform`
4. Type: **Regular Web Application**
5. Click **Create**

## Step 3: Configure Application Settings
1. In your application settings, find the **Basic Information** section
2. Copy the following values:
   - **Domain**: `your-tenant.us.auth0.com`
   - **Client ID**: `abc123...`
   - **Client Secret**: `xyz789...` (click "Show" to reveal)

3. Scroll to **Application URIs** section
4. Set **Allowed Callback URLs**:
   ```
   http://localhost:8501,
   https://your-production-domain.com
   ```

5. Set **Allowed Logout URLs**:
   ```
   http://localhost:8501,
   https://your-production-domain.com
   ```

6. Set **Allowed Web Origins**:
   ```
   http://localhost:8501,
   https://your-production-domain.com
   ```

7. Click **Save Changes**

## Step 4: Configure Environment Variables
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update the Auth0 configuration in `.env`:
   ```bash
   AUTH0_DOMAIN=your-tenant.us.auth0.com
   AUTH0_CLIENT_ID=your-client-id
   AUTH0_CLIENT_SECRET=your-client-secret
   AUTH0_AUDIENCE=https://your-tenant.us.auth0.com/api/v2/
   AUTH0_REDIRECT_URI=http://localhost:8501
   ```

## Step 5: Configure Password Policy (Recommended)
1. In Auth0 Dashboard, go to **Security** → **Attack Protection**
2. Click **Breached Password Detection** → Enable
3. Go to **Security** → **Multi-factor Auth**
4. Enable **One-time Password** (recommended)

## Step 6: Test Authentication
1. Start the application:
   ```bash
   streamlit run app/main.py
   ```

2. Click "Login with Auth0"
3. You should be redirected to Auth0 login page
4. Create a test account or login with existing account
5. After successful login, you should be redirected back to the application

## Step 7: Configure User Roles (Optional)
1. In Auth0 Dashboard, go to **User Management** → **Roles**
2. Create roles:
   - **Admin**: Full access
   - **Deployer**: Can deploy infrastructure
   - **Viewer**: Read-only access

3. Assign roles to users in **User Management** → **Users**

## Troubleshooting

### Error: "Invalid state parameter"
- Clear browser cookies and try again
- Check that `AUTH0_REDIRECT_URI` matches exactly in both `.env` and Auth0 settings

### Error: "Unauthorized client"
- Verify `AUTH0_CLIENT_ID` and `AUTH0_CLIENT_SECRET` are correct
- Check that callback URL is configured in Auth0 settings

### Error: "Access denied"
- Check that user has verified email address
- Verify user is not blocked in Auth0 dashboard

## Security Best Practices
1. **Never commit `.env` file** - it contains secrets
2. **Use different Auth0 applications** for dev/staging/prod
3. **Enable MFA** for all admin users
4. **Regularly rotate** client secrets
5. **Monitor Auth0 logs** for suspicious activity
6. **Set up anomaly detection** in Auth0 dashboard

## Production Deployment
1. Create separate Auth0 application for production
2. Use environment-specific callback URLs
3. Store secrets in AWS Secrets Manager (not `.env` file)
4. Enable advanced security features:
   - Breached password detection
   - Suspicious IP throttling
   - Bot detection
5. Set up monitoring and alerts
