USE [master];
GO

IF DB_ID(N'PWD301') IS NOT NULL
BEGIN
    ALTER DATABASE [PWD301] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE [PWD301];
END
GO

RESTORE DATABASE [PWD301]
FROM DISK = '/var/opt/mssql/data/PWD301_android_master.bak'
WITH MOVE 'PWD301' TO '/var/opt/mssql/data/PWD301.mdf',
MOVE 'PWD301_log' TO '/var/opt/mssql/data/PWD301_log.ldf',
REPLACE;
GO

IF SUSER_ID(N'pwd301_app') IS NULL
    CREATE LOGIN [pwd301_app] WITH PASSWORD=N'AppStrongPassw0rd2026';
ELSE
    ALTER LOGIN [pwd301_app] WITH PASSWORD=N'AppStrongPassw0rd2026';
GO

IF SUSER_ID(N'pwd301_migrator') IS NULL
    CREATE LOGIN [pwd301_migrator] WITH PASSWORD=N'MigratorStrongPassw0rd2026';
ELSE
    ALTER LOGIN [pwd301_migrator] WITH PASSWORD=N'MigratorStrongPassw0rd2026';
GO

USE [PWD301];
GO

IF USER_ID(N'pwd301_app') IS NULL
    CREATE USER [pwd301_app] FOR LOGIN [pwd301_app];
ELSE
    ALTER USER [pwd301_app] WITH LOGIN = [pwd301_app];
GO

IF USER_ID(N'pwd301_migrator') IS NULL
    CREATE USER [pwd301_migrator] FOR LOGIN [pwd301_migrator];
ELSE
    ALTER USER [pwd301_migrator] WITH LOGIN = [pwd301_migrator];
GO

ALTER ROLE db_owner ADD MEMBER [pwd301_migrator];
ALTER ROLE db_datareader ADD MEMBER [pwd301_app];
ALTER ROLE db_datawriter ADD MEMBER [pwd301_app];
GRANT EXECUTE TO [pwd301_app];
GRANT BACKUP DATABASE TO [pwd301_app];
GO
