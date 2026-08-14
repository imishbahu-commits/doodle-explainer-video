# Projects

Each subdirectory is a small, Git-friendly checkpoint that lets another chat
resume production. Create one with:

```bash
python3 scripts/project.py init "Video title" --template entire-history --duration 12
```

Commit project metadata, scripts, source ledgers, and manifests. Keep large
media out of Git; use stable HTTPS URLs or an external asset store.
