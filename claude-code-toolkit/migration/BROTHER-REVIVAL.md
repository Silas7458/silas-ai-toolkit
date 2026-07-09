# BROTHER-REVIVAL.md - Launch Codes

Written 2026-07-09 by Brother (Claude Code, Chief Engineer) on the ORIGINAL machine,
for the NEXT Brother on the NEW machine. The old machine is gone. Everything you need
is on this drive. Execute phase by phase. Do not skip the Verification Gauntlet.

Drive layout reference: 00-RUNBOOK (this file, RESTORE.md, manifests, logs),
01-USER, 02-REPOS, 03-SCRIPTS, 04-CONFIGS, 05-SECRETS, 06-SYSTEM-STATE,
07-APPDATA, 08-OTHER, 09-ONEDRIVE.

================================================================================
PART 0 - FOR SILAS (human bootstrap, before Claude exists on the new machine)
================================================================================

0.1  CRITICAL - USERNAME MUST BE "silas". Create the Windows account so the
     profile path is exactly C:\Users\silas. Every scheduled task, script,
     CLAUDE.md path, and Claude's own memory key (projects\C--Users-silas) is
     hardcoded to that path. A different username means hours of path surgery.

0.2  Plug in the MIGRATION drive. Unlock with your BitLocker password
     (the one you set interactively; recovery key is on your off-machine photo).

0.3  Install the minimum seed, in order (accept defaults):
     a. PowerShell 7        winget install Microsoft.PowerShell
     b. Git                 winget install Git.Git
     c. Node.js LTS         winget install OpenJS.NodeJS.LTS
     d. Claude Code         npm install -g @anthropic-ai/claude-code
     e. Run "claude" once and sign in to your Anthropic account.

0.4  Open a terminal, then:
     cd D:\MIGRATION        (use the actual drive letter)
     claude
     Paste this launch prompt:

     "You are Brother. This is a new machine; the old one is gone. Read
      D:\MIGRATION\00-RUNBOOK\BROTHER-REVIVAL.md and execute it phase by
      phase, in order. Verify each phase before moving on. Do not skip the
      Verification Gauntlet at the end. Report progress as you go."

That is all Silas does by hand. Everything below is YOUR job, Claude.

================================================================================
PART 1 - FOR CLAUDE: BECOME BROTHER FIRST (identity before infrastructure)
================================================================================

Set $D to this drive's letter. Copy identity home BEFORE anything else:

1.1  robocopy $D\MIGRATION\04-CONFIGS\.claude C:\Users\silas\.claude /E
     This restores: persistent memory (projects\C--Users-silas\memory\MEMORY.md
     + all memory files), skills, commands, hooks (incl. gsd-statusline.js),
     plugins, GSD (get-shit-done), agents, settings.json, teams.

1.2  Copy profile-root files:
     copy $D\MIGRATION\08-OTHER\_profile-root-files\CLAUDE.md  C:\Users\silas\
     copy $D\MIGRATION\08-OTHER\_profile-root-files\.claude.json C:\Users\silas\
     (.claude.json = MCP server registrations + per-project state)

1.3  Mirror back ALL remaining dot-directories:
     for each folder in $D\MIGRATION\04-CONFIGS\ -> C:\Users\silas\<same name>
     Key ones: .cleo (task templates), .ssh (keys), .config (gws + gws-azalea
     Google auth), .gitconfig lives in 06-SYSTEM-STATE\git-global-config.txt
     (re-apply with git config --global), .hospice-regs (watcher state).

1.4  RESTART claude (exit, relaunch from C:\Users\silas). CLAUDE.md and memory
     now load. CHECKPOINT: you can read MEMORY.md, you know who Silas is, you
     know the prime directives. If not, STOP and fix Part 1 before continuing.

================================================================================
PART 2 - FILE TREES BACK HOME
================================================================================

Follow 00-RUNBOOK\RESTORE.md for the full mapping. Summary (robocopy /E each):
  01-USER\<folder>   -> C:\Users\silas\<folder>       (Documents FIRST - it
                        contains claude-context + claude-family: session state,
                        archive, standing orders, council-config.json creds)
  02-REPOS\<repo>    -> C:\Users\silas\<repo>         (19 repos, .env files
                        included; node_modules excluded - reinstall per repo)
  03-SCRIPTS\scripts -> C:\Users\silas\scripts        (incl. kantime worker +
                        its creds, migration tooling, notebooklm wrappers)
  03-SCRIPTS\tools   -> C:\Users\silas\tools          (incl. discord-mcp jar, vip)
  03-SCRIPTS\bin     -> C:\Users\silas\bin            (incl. gws-azalea.cmd)
  08-OTHER\<folder>  -> C:\Users\silas\<folder>
  09-ONEDRIVE\Documents -> merge into C:\Users\silas\Documents (old machine had
                        shell-Documents redirected into OneDrive; GUI apps saved
                        there. Merge, do not overwrite claude-context/family.)

================================================================================
PART 3 - PROGRAMS AND RUNTIMES
================================================================================

3.1  winget import $D\MIGRATION\06-SYSTEM-STATE\winget-packages.json
     Cross-check 06-SYSTEM-STATE\installed-programs.txt for anything missed.
     Explicitly ensure these land: Docker Desktop, Python 3.13, VS Code,
     PowerShell 7, Git, Node.js LTS, Java runtime (discord-mcp jar needs it).

3.2  Python: verify "py" launcher works, then
     py -m pip install -r $D\MIGRATION\06-SYSTEM-STATE\pip-freeze.txt
     (This is "all the Python code stuff" - every package the old machine had.)

3.3  npm globals: reinstall from 06-SYSTEM-STATE\npm-globals.txt. As of this
     writing: @googleworkspace/cli (gws), @openai/codex (Stepbrother),
     @playwright/cli, @railway/cli, @remotion/cli, agent-browser,
     agent-messenger, ccusage, dev-browser, docx, n8n, neonctl, pyright,
     repomix, typescript, typescript-language-server, vercel,
     vscode-langservers-extracted. NotebookLM CLI runs via npx (no install).

3.4  Per-repo dependencies as needed when you first touch a repo:
     npm install (JS/TS repos), py -m pip install -r requirements.txt (Python).
     Do NOT bulk-install all 19 repos up front; restore on first use.

================================================================================
PART 4 - DOCKER: WHAT IT IS IN OUR STACK, AND HOW TO REBUILD IT
================================================================================

Read carefully - this knowledge existed only on the old machine.

Docker Desktop runs ONE compose project: amerix-saas, defined at
C:\Users\silas\amerix-saas\docker-compose.yml (restored in Part 2).
It runs TWO containers:

4.1  amerix-postgres  (image pgvector/pgvector:pg16, port 5432)
     - Database amerix_dev; credentials are in the compose file's env block.
     - Schemas on the old machine: kantime, kantime_paloma, cms, public.
     - ROLE: local landing zone for the KanTime ingestion pipeline. The
       KanTime worker (C:\Users\silas\scripts\kantime, driven by the KanTime-*
       scheduled tasks) exports from KanTime and imports HERE first.
     - PRODUCTION dashboard data lives in NEON (cloud Postgres) - it survived
       the machine change untouched. kantime-dashboard env discipline:
       .env.local = THIS local Docker Postgres; .env.production = Neon.
       DB-mutating scripts use --env-file=.env.production only when Neon is
       the intended target.
     - STANDING RULE (came from hard experience): if KanTime imports fail,
       check that Docker Desktop is RUNNING before debugging anything else.
     - KanTime access is PP-only (Paloma) permanently per S#281 freeze.

4.2  n8n  (custom image amerix-saas-n8n built from the repo, port 5678)
     - ROLE: hosts the knowledge-ingest webhook
       http://localhost:5678/webhook/knowledge-ingest used by /session-end
       (Knowledge Layer ingest step). Binds Documents\claude-context and
       Documents\claude-family into the container.
     - API key is in the compose file's env block.

4.3  WHAT DID NOT TRAVEL (volume contents die with the old machine):
     - amerix_dev table rows: rebuild = re-run migrations from the repos, then
       let the KanTime worker's scheduled runs re-import PP data. Frozen
       snapshots and production truth are in Neon - nothing critical lost.
     - n8n internal state (credentials, execution history, volume n8n_data):
       LOST. The 24 workflow definitions SURVIVED as JSON exports in
       C:\Users\silas\amerix-saas\n8n-workflows\ (incl. all-export.json).
       Re-import via n8n UI/API after the container is up; re-enter any
       credentials inside n8n by hand.
     - claude-memory pgvector volume (backup /recall store): LOST and
       acceptable - NotebookLM (cloud) is the primary recall backend and
       survived. Recreate the pgvector store empty if /recall backup is wanted.

4.4  REBUILD SEQUENCE:
     a. Install Docker Desktop (WSL2 backend), launch it, finish first-run.
     b. cd C:\Users\silas\amerix-saas
     c. docker compose up -d --build
        (postgres init script docker\postgres\init-extensions.sql enables
        pgvector automatically; volumes recreate empty)
     d. Apply schema migrations per repo instructions (kantime-dashboard
        migrations against .env.local for the local DB).
     e. Re-import n8n workflows from n8n-workflows\.
     f. Set Docker Desktop to start at login (Settings > General).

================================================================================
PART 5 - SCHEDULED TASKS
================================================================================

XMLs are in 06-SYSTEM-STATE\scheduled-tasks\. For each:
  Register-ScheduledTask -TaskName <name> -Xml (Get-Content <file> -Raw)
Fix inside each XML first: user SID (old machine SID will not exist) and any
paths if the username differs (it should not - see 0.1).

REGISTER (these run the business):
  KanTime-CashPostedSync, KanTime-CashSync, KanTime-IntakeSync,
  KanTime-PipelinePoller, KanTime-ScheduledSync, KanTime Unbilled Charges
  Export, KanTime-WeeklyBackup, HAMR Pipeline - 7th / 16th / 21st / 28th,
  Hospice Regs Watcher, HospiceDataRefresh, NotebookLM Cookie Refresh,
  Claude Config Guard, SemanticMemoryHarvest, Gmail OAuth Health Check,
  CompileProctorBriefing, ContextAuthority-ClaudeMD.

SKIP (machine-specific bloat): Stardock.Notification, ZoomUpdateTaskUser-*.

================================================================================
PART 6 - RE-AUTH CHECKLIST (cloud tokens were never on this drive by design)
================================================================================

Work through ALL of these. Config files restored in Parts 1-2 carry most
secrets; anything interactive is listed here.

  [ ] Anthropic / Claude Code   done in Part 0
  [ ] GitHub                    gh auth login       then: gh auth status
  [ ] GitLab                    glab auth login     (GitLab is CANONICAL for
                                kantime-dashboard + paloma-kantime-dashboard:
                                Vercel deploys watch GitLab, GitHub is mirror)
  [ ] Vercel                    vercel login        then: vercel whoami
  [ ] Neon                      neonctl auth        (or verify via repo .env)
  [ ] Google (gws)              config copied; verify:
                                gws drive about get --params '{"fields":"user(emailAddress)"}'
                                must return executive.shelton@gmail.com
  [ ] Google (gws-azalea)       gws-azalea drive about get ... must return
                                silas@azaleahospice.com; re-auth if expired
  [ ] NotebookLM                npx notebooklm login, then re-wire the durable
                                auth refresh (NOTEBOOKLM_REFRESH_CMD +
                                scripts\notebooklm-refresh-wrapper.py +
                                NotebookLM Cookie Refresh task). See memory:
                                reference_notebooklm_auth_refresh_cmd.
  [ ] Discord bot               token rides in restored configs
                                (council-config.json); test in Gauntlet.
  [ ] KanTime                   creds ride in scripts\kantime - no action.
  [ ] Windows Credential Mgr    re-create entries per 05-SECRETS\SECRETS-README.txt
  [ ] Browser passwords         import CSVs from 05-SECRETS into Chrome/Firefox,
                                then DELETE the CSVs from the new machine.

================================================================================
PART 7 - VERIFICATION GAUNTLET (Brother is not alive until ALL pass)
================================================================================

Run every check. Report results to Silas as a pass/fail table.

  1. Identity: state 3 specific facts from MEMORY.md; /session-start completes
     and presents a briefing.
  2. Repos: git -C C:\Users\silas\kantime-dashboard remote -v shows origin AND
     gitlab; gh auth status and glab auth status both green.
  3. Google: gws and gws-azalea each return their correct account email.
  4. NotebookLM: query the Hospice Compliance corpus
     (ID 51a30734-55d9-4706-ba20-616e4d756ef2) and get a real answer.
  5. Discord: send a test message to #brother-log (1475944751424340128):
     "[Brother] Revival complete on new machine."
  6. Docker: docker ps shows amerix-postgres and n8n Up;
     docker exec amerix-postgres psql -U amerix -d amerix_dev -c "SELECT 1;"
     succeeds; curl http://localhost:5678/ responds.
  7. Scheduled tasks: Get-ScheduledTask lists every task from Part 5's
     REGISTER list.
  8. Vercel/Neon: vercel whoami succeeds; dashboard prod URL loads
     (paloma-kantime-dashboard.vercel.app).
  9. KanTime pipeline: run one worker export manually from scripts\kantime;
     rows land in amerix_dev.
 10. First act as resurrected Brother: write a session snapshot + update
     session-state.md recording the revival, per shutdown protocol.

================================================================================
PART 8 - STANDING CONSTRAINTS THAT MUST SURVIVE THE MACHINE
================================================================================

These live in CLAUDE.md + memory (restored in Part 1). Highest-stakes ones,
restated so they are never re-learned the hard way:
  - No PHI/business data to ANY external service without explicit per-
    destination sign-off.
  - KanTime access = Paloma (PP) only, permanently.
  - GitLab is canonical + deploy trigger for the KanTime dashboards.
  - ASCII only in .ps1/.bat/.sh/.js/.ts files - no em-dashes, no unicode.
  - Frozen data snapshots are sacred; never sacrificed to fix something else.
  - Corpus-first for all hospice/Medicare research (NotebookLM corpus).

================================================================================
CURRENCY NOTE
================================================================================

This drive is a snapshot. Staging last ran on the date in
00-RUNBOOK\STAGING-REPORT.txt. OLD-MACHINE BROTHER: re-run
C:\Users\silas\scripts\migration\stage-out.ps1 as the LAST act before the old
machine is decommissioned, so the drive carries final state. stage-out.ps1
re-copies this file to 00-RUNBOOK on every run; the canonical copy lives at
scripts\migration\BROTHER-REVIVAL.md (also in the silas-ai-toolkit repo).
