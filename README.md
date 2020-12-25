# black-box
A service designed to be run by `cron` or **Kubernetes CronJob** which backs up all your databases to all your favorite cloud storage providers.

A cheap and simple solution to backing up all your stuff.

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
`black-box` can be configured in a number of ways. To set it up, simply edit the `config.yaml` file in the root folder.

####  Rotation
By default, `black-box` will automatically remove all backup files older than 7 days in the folder you configure for your storage provider. To determine if something is a backup file or not, it will use a regex pattern that corresponds with the default file it saves, for example `black-box-postgres-backup-11-12-2020.sql`.

You can configure the number of days before rotating by altering the `rotation_days` parameter in `config.yaml`. 

# Databases
Right now, we support **Redis**, **MongoDB**, and **PostgreSQL**. If you need support for an additional database, consider opening a pull request to add a new database handler.

#### Redis 
- Set `redis_enabled` to `true` in `config.yaml`. 
- Ensure that the `BLACKBOX_REDIS_USER`, `BLACKBOX_REDIS_PASSWORD`, `BLACKBOX_REDIS_HOST` and `BLACKBOX_REDIS_PORT` environment variables are set. 

#### MongoDB
- Set `mongo_enabled` to `true` in `config.yaml`. 
- Ensure that the `BLACKBOX_MONGO_USER`, `BLACKBOX_MONGO_PASSWORD`, `BLACKBOX_MONGO_HOST` and `BLACKBOX_MONGO_PORT` environment variables are set.

#### Postgres
- Set `postgres_enabled` to `true` in `config.yaml`. 
- Ensure that the `BLACKBOX_POSTGRES_USER`, `BLACKBOX_POSTGRES_PASSWORD`, `BLACKBOX_POSTGRES_HOST` and `BLACKBOX_POSTGRES_PORT` environment variables are set. 

# Storage providers
`black-box` can work with different storage providers to save your backups - usually so that you can automatically store them in the cloud. Right now we only support **Google Drive**, but we will probably add additional providers in the future.

#### Google Drive
- Set `gdrive_enabled` to `true` in `config.yaml`
- Ensure that the `BLACKBOX_GDRIVE_API_TOKEN` environment variable is set.