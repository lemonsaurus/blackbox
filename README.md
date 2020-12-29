# black-box
A service designed to be run by `cron` or **Kubernetes CronJob** which backs up all your databases to all your favorite cloud storage providers.

A cheap and simple solution to backing up all your stuff.

**NOTE: This is not ready to receive contributions yet!**

# Setup
This service can either be set up as a cron job (on UNIX systems), or as a Kubernetes CronJob. You can probably set it up on just about any system by applying some altered version of one of these approaches, if you're clever about it.

### Setting up as a cron job
All you need to do to set it up as a cron job is clone this repo and then trigger this script every day at some convenient time.
```cron
# example cron file
```

### Setting it up as a Kubernetes CronJob
Here's an example manifest you can use for this.
```yaml
# example CronJob manifest
```

# Configuration
`black-box` can be configured in a number of ways. To set it up, create a `config.yaml` file in the root folder. Here's an example of what it should contain:
```yaml
# MongoDB
mongodb_enabled: false
mongodb_connstring: mongodb://username:password@host:port

# Postgres
postgres_enabled: true
postgres_connstring: postgres://username:password@host:port

# Storage providers
gdrive_enabled: false

# Database rotation
rotation_days: 7
```

####  Rotation
By default, `black-box` will automatically remove all backup files older than 7 days in the folder you configure for your storage provider. To determine if something is a backup file or not, it will use a regex pattern that corresponds with the default file it saves, for example `black-box-postgres-backup-11-12-2020.sql`.

You can configure the number of days before rotating by altering the `rotation_days` parameter in `config.yaml`. 

# Databases
Right now, this app supports **MongoDB** and **PostgreSQL**. If you need support for an additional database, consider opening a pull request to add a new database handler.

#### MongoDB
- Set `mongo_enabled` to `true` in `config.yaml`. 
- Set a `mongo_connstring` in `config.yaml`. The correct format is `mongodb://username:password@host:port`.

#### Postgres
- Set `postgres_enabled` to `true` in `config.yaml`. 
- Set a `postgres_connstring` in `config.yaml`. The correct format is `postgresql://username:password@host:port`.

# Storage providers
`black-box` can work with different storage providers to save your backups - usually so that you can automatically store them in the cloud. Right now we only support **Google Drive**, but we will probably add additional providers in the future.

#### Google Drive
- Set `gdrive_enabled` to `true` in `config.yaml`
- Ensure that the `BLACKBOX_GDRIVE_API_TOKEN` environment variable is set.
