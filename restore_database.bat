@echo off
REM Script to restore MariaDB database from SQL dump file
REM Usage: restore_database.bat <dump_file.sql>

if "%1"=="" (
    echo Usage: restore_database.bat ^<dump_file.sql^>
    pause
    exit /b 1
)

if not exist "%1" (
    echo Error: File %1 not found
    pause
    exit /b 1
)

echo Restoring database from %1...
docker-compose exec -T db mariadb -uadmin_db -punify_admin unify_db < %1

if %ERRORLEVEL% EQU 0 (
    echo ✓ Database restored successfully
) else (
    echo ✗ Error restoring database
)

pause
