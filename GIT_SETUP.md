# Git Setup Instructions

## Step 1: Install Git

If Git is not installed, download and install it from:
**https://git-scm.com/download/win**

During installation, make sure to:
- ✅ Add Git to PATH
- ✅ Use Git from the command line and also from 3rd-party software

After installation, **restart your terminal/PowerShell**.

## Step 2: Verify Git Installation

Open PowerShell and run:
```powershell
git --version
```

You should see something like: `git version 2.x.x`

## Step 3: Configure Git (First Time Only)

If this is your first time using Git, configure your name and email:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Step 4: Initialize Repository and Push

Once Git is installed, run these commands in PowerShell from the project directory:

```powershell
# Navigate to project directory
cd C:\Users\mkuma\OneDrive\Desktop\DecisionLens

# Initialize git repository
git init

# Add all files (respects .gitignore)
git add .

# Create initial commit
git commit -m "Initial commit: X-Ray decision transparency library with dashboard

- Domain-agnostic SDK for multi-step pipeline tracing
- SQLite storage with pluggable store interface
- FastAPI dashboard with rich visualization
- Demo competitor selection pipeline
- Production-ready error handling and JSON parsing
- Comprehensive documentation"

# Add your remote repository (replace with your actual repo URL)
# Example for GitHub:
git remote add origin https://github.com/yourusername/DecisionLens.git

# Or for GitLab:
# git remote add origin https://gitlab.com/yourusername/DecisionLens.git

# Push to remote repository
git branch -M main
git push -u origin main
```

## Step 5: For Future Updates

After making changes, use these commands:

```powershell
# Check what changed
git status

# Stage changes
git add .

# Commit changes
git commit -m "Your commit message describing the changes"

# Push to remote
git push
```

## Common Git Commands

```powershell
# View changes
git status
git diff

# View commit history
git log --oneline

# Create a new branch
git checkout -b feature-name

# Switch branches
git checkout main

# Merge branch
git merge feature-name
```

## Troubleshooting

**If you get "git is not recognized":**
- Restart your terminal after installing Git
- Make sure Git was added to PATH during installation
- Try using Git Bash instead of PowerShell

**If you get authentication errors:**
- For GitHub: Use a Personal Access Token instead of password
- Generate token: GitHub → Settings → Developer settings → Personal access tokens
- Use token as password when pushing

**If you need to update remote URL:**
```powershell
git remote set-url origin https://github.com/yourusername/DecisionLens.git
```

