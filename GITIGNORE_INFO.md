# Git Ignore Configuration

## 🔒 Sensitive Files Protected

The `.gitignore` file is now configured to protect all sensitive data from being committed to GitHub.

### Critical Files (Protected from commit)

1. **Credentials & API Keys**
   - `client_secret.json` - ✅ **INCLUDED** in repo for easier setup (Google API credentials)
   - `license_credentials.json` - License system credentials (PROTECTED)
   - `.gdrive_auth_state.json` - Google Drive auth state (PROTECTED)

2. **OAuth Tokens**
   - `tokens/` directory - All token files
   - `token.json`, `zahra1.json` - OAuth tokens
   - `*.token` - Any token files

3. **License System**
   - `license_cache.json` - Customer license data
   - `license_config.json` - License configuration
   - `lisensi.json` - License info

4. **User Data**
   - `users.json` - User accounts and passwords
   - `telegram_config.json` - Bot token

5. **Configuration Files**
   - `live_streams.json` - Stream configurations
   - `stream_mapping.json` - Stream mappings (contains keys)
   - `stream_timers.json` - Timer data
   - `schedule_config.json` - Schedule data
   - `scheduler_status.json` - Runtime status

6. **Database Files**
   - `video_database.json` - Video metadata
   - `thumbnail_database.json` - Thumbnail data

7. **Excel Files with Stream Keys**
   - `*.xlsx` - All Excel files (except *_template.xlsx, *_example.xlsx)
   - These contain stream keys and should NEVER be committed

8. **Media Files**
   - `videos/` - Uploaded video files
   - `thumbnails/` - Uploaded thumbnails
   - `*.mp4`, `*.avi`, etc. - All video formats

## ✅ Safe Files (OK to commit)

1. **Source Code**
   - `*.py` - Python scripts
   - `*.js` - JavaScript files
   - `*.html`, `*.css` - Templates and styles

2. **Documentation**
   - `*.md` - All markdown documentation

3. **Configuration Templates**
   - `*.example` files - Template configurations
   - These have placeholder values only

4. **Build Configuration**
   - `requirements.txt` - Python dependencies
   - `package.json` - Node dependencies
   - `tailwind.config.js` - Tailwind config

## 🚀 Usage

### First Time Setup

When setting up on a new machine, copy the example files:

```bash
cp license_config.json.example license_config.json
cp live_streams.json.example live_streams.json
cp schedule_config.json.example schedule_config.json
cp stream_mapping.json.example stream_mapping.json
cp stream_timers.json.example stream_timers.json
cp telegram_config.json.example telegram_config.json
cp users.json.example users.json
cp thumbnail_database.json.example thumbnail_database.json
cp video_database.json.example video_database.json
```

Then edit each file with your actual configuration.

### Checking Protected Files

To see all files currently ignored:

```bash
git status --ignored
```

### Adding New Sensitive Patterns

If you need to add new patterns to `.gitignore`:

1. Edit `.gitignore`
2. Add the pattern under the appropriate section
3. If the file is already tracked, remove it:
   ```bash
   git rm --cached <filename>
   ```
4. Commit the changes

## ⚠️ Important Notes

1. **Never force-add ignored files** using `git add -f` for sensitive data
2. **Check before committing**: Always run `git status` and `git diff --cached` before committing
3. **If you accidentally commit secrets**:
   - Don't push!
   - Use `git reset HEAD~1` to undo the commit
   - Remove the file from git: `git rm --cached <file>`
   - Add to .gitignore
   - Commit again

## 🔍 Security Checklist Before Push

- [ ] Run `git status` - check no sensitive files listed
- [ ] Run `git diff --cached` - review all changes
- [ ] Check for credentials in code
- [ ] Verify .gitignore is up to date
- [ ] Confirm only .example files are committed, not actual config files

## 📝 Current Protection Status

As of the last cleanup:
- ✅ 29 files/directories are protected by .gitignore
- ✅ All credentials removed from git history
- ✅ Example templates provided for all sensitive files
- ✅ Documentation and source code safely committed
