## Project Setup

#### Step 1: clone repo
```bash
git clone https://github.com/YOUR_USERNAME/rights2roof.git
cd rights2roof
```

#### Step 2: install dependencies (this auto-uses uv.lock versions)
```bash
uv sync
```


### Step 3: Run Server (Test FastAPI)
```bash
uv run uvicorn app.services.slack_webhook:app --reload
```

### Step 4: create feature branch
```bash
git checkout -b feature/123-add-login
```



## Git Commands
#### stage and commit
```bash
git add .

- `git status` — Check your current branch and see changes.
- `git pull origin main` — Pull the latest changes from the main branch - to ensure your copy is up to date.
- `git checkout` -b your-branch-name — Create and switch to a new branch.
- `git add filename` — Add specific file(s) (e.g., hello_world.py) to the staging area.
- `git commit -am "your commit message"` — Commit changes with a message (the -a option stages all modified files, the -m allows you to add the commit message directly).
- - `git push origin branch-name` — Push your branch and committed changes to the remote repository.
`git checkout branch-name` — Switch to another branch (e.g., back to main) after merging.
- `git pull` — Pull the latest changes after a merge, to update your local repository.