@echo off
REM Script to dump MariaDB database from Docker container
REM Creates a timestamped backup file

set TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_FILE=backup_%TIMESTAMP%.sql

echo Creating database backup...
docker-compose exec -T db mariadb-dump -uadmin_db -punify_admin unify_db > %BACKUP_FILE%

if %ERRORLEVEL% EQU 0 (
    echo ✓ Database backup created successfully: %BACKUP_FILE%
) else (
    echo ✗ Error creating backup
)

pause
