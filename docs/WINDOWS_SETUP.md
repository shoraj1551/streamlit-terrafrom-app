# Installing Microsoft Visual C++ Build Tools

## Quick Installation Steps

### Option A: Minimal Installation (Recommended)
1. Download the Build Tools installer:
   https://visualstudio.microsoft.com/visual-cpp-build-tools/

2. Run the installer and select:
   - ✅ **Desktop development with C++**
   - Under "Installation details" on the right, ensure these are checked:
     - MSVC v143 - VS 2022 C++ x64/x86 build tools
     - Windows 10/11 SDK

3. Click "Install" (requires ~6GB disk space)

4. After installation, restart your terminal/PowerShell

5. Run the installation command:
   ```powershell
   pip install psycopg2-binary==2.9.9
   ```

### Option B: Full Visual Studio (If you need IDE)
1. Download Visual Studio Community (free):
   https://visualstudio.microsoft.com/downloads/

2. During installation, select:
   - ✅ **Desktop development with C++**

3. Complete installation and restart terminal

### Verification
After installation, verify with:
```powershell
pip install psycopg2-binary==2.9.9
```

If successful, you should see:
```
Successfully installed psycopg2-binary-2.9.9
```

## Alternative: Use Pre-built Wheel
If you don't want to install C++ Build Tools, you can use a pre-built wheel:

```powershell
# For Python 3.13 on Windows
pip install psycopg2-binary --only-binary :all:
```

## Next Steps After Installation
Once psycopg2-binary is installed, I'll continue with:
1. Setting up Alembic migrations
2. Creating migration scripts
3. Updating deployment_db.py to use PostgreSQL
4. Testing the database connection

---

**Please install the C++ Build Tools and let me know when ready to continue!**
