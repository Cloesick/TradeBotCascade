# 🐍 Virtual Environment Setup Guide

## ✅ Virtual Environment Created!

Your `.venv` folder has been created and configured.

---

## 🔧 VS Code Configuration

The following settings are already configured in `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
  "python.terminal.activateEnvironment": true,
  "python.envFile": "${workspaceFolder}/backend/.env"
}
```

---

## 🚀 Quick Start

### **1. Reload VS Code Window**

Press `Ctrl+Shift+P` and type:
```
Developer: Reload Window
```

This will make VS Code recognize the new virtual environment.

---

### **2. Select Python Interpreter**

Press `Ctrl+Shift+P` and type:
```
Python: Select Interpreter
```

Choose:
```
Python 3.13.13 ('.venv': venv) .\\.venv\Scripts\python.exe
```

---

### **3. Verify Installation**

Open a new terminal in VS Code (it should auto-activate `.venv`):

```powershell
# Should show (.venv) prefix
python --version
# Should show: Python 3.13.13

# Check installed packages
pip list
```

---

## 📦 Dependencies Installed

All packages from `requirements.txt` are being installed:

### **Core:**
- FastAPI
- Uvicorn
- Pandas
- NumPy

### **Financial:**
- Alpha Vantage
- TA-Lib
- Scikit-learn
- SciPy

### **Deep Learning:**
- PyTorch (CPU version)
- Statsmodels (optional)

### **Security:**
- python-jose (JWT)
- passlib (bcrypt)
- python-multipart

---

## 🔄 Manual Activation (if needed)

### **PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

### **Command Prompt:**
```cmd
.venv\Scripts\activate.bat
```

### **Git Bash:**
```bash
source .venv/Scripts/activate
```

---

## 🛠️ Troubleshooting

### **Issue: "Execution Policy" Error**

If you get an error about execution policy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again.

---

### **Issue: VS Code Not Detecting .venv**

1. **Reload Window**: `Ctrl+Shift+P` → "Developer: Reload Window"
2. **Select Interpreter**: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. **Restart VS Code** completely

---

### **Issue: Dependencies Not Installing**

```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

---

## 📁 Virtual Environment Structure

```
.venv/
├── Scripts/
│   ├── python.exe          # Python interpreter
│   ├── pip.exe             # Package manager
│   ├── Activate.ps1        # PowerShell activation
│   └── activate.bat        # CMD activation
├── Lib/
│   └── site-packages/      # Installed packages
└── pyvenv.cfg              # Configuration
```

---

## ✅ Verification Checklist

After reloading VS Code:

- [ ] Terminal shows `(.venv)` prefix
- [ ] `python --version` shows Python 3.13.13
- [ ] `pip list` shows all packages
- [ ] No red squiggly lines in Python files
- [ ] IntelliSense works for imports
- [ ] Can run backend server

---

## 🚀 Run Backend Server

With virtual environment activated:

```powershell
# Navigate to backend
cd backend

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or use VS Code's integrated terminal (auto-activates .venv):

```powershell
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🎯 Next Steps

1. **Reload VS Code Window** (`Ctrl+Shift+P` → "Developer: Reload Window")
2. **Select Python Interpreter** (`.venv` should appear)
3. **Open New Terminal** (should auto-activate)
4. **Verify**: `python --version` and `pip list`
5. **Run Backend**: `cd backend && uvicorn main:app --reload`

---

## 📝 Notes

- ✅ Virtual environment is **isolated** from system Python
- ✅ Dependencies are **project-specific**
- ✅ `.venv` folder is **gitignored** (already in `.gitignore`)
- ✅ Each project should have its own virtual environment
- ✅ VS Code automatically activates `.venv` in new terminals

---

## 🔐 Environment Variables

Don't forget to set up your `.env` file in the `backend/` folder:

```bash
# backend/.env
ALPHA_VANTAGE_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
```

---

## 🎉 Success!

Your virtual environment is ready to use!

**Status:** ✅ CONFIGURED  
**Python Version:** 3.13.13  
**Location:** `.venv/Scripts/python.exe`  
**Dependencies:** Installing...  

**Just reload VS Code and you're good to go!** 🚀
