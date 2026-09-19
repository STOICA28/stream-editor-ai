---
id: RUNBOOK-BACKUP-001
status: canonical
title: Database and Media Backup & Restore
---

# Backup & Restore Runbook

## Overview
StreamEditor AI stores state in PostgreSQL/SQLite and media in DATA_DIR.
Both must be backed up consistently to avoid orphaned artifacts.

## Backup Process
1. **Quiesce Jobs**: Scale down workers to 0 to prevent writes.
   \\\ash
   docker-compose scale worker=0
   \\\
2. **Database Backup**:
   \\\ash
   # PostgreSQL
   pg_dump -U streameditor_user streameditor_db > backup_db_date +%Y%m%d.sql
   
   # SQLite
   sqlite3 data/test.db ".backup 'backup_db_date +%Y%m%d.db'"
   \\\
3. **Media Backup**:
   \\\ash
   tar -czvf backup_media_date +%Y%m%d.tar.gz data/projects/
   \\\

## Restore Process
1. **Restore DB**:
   \\\ash
   psql -U streameditor_user streameditor_db < backup_db_*.sql
   \\\
2. **Restore Media**:
   \\\ash
   tar -xzvf backup_media_*.tar.gz -C data/projects/
   \\\
3. **Verify Integrity**:
   Run the integrity checker script to ensure all file paths exist in the DB.
