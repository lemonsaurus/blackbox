![blackbox](img/blackbox_banner.png)
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
`blackbox` can be configured in a number of ways. To set it up, create a `config.yaml` file in the root folder. Here's an example of what it should contain:
```yaml
databases:
  - mongodb://username:password@host:port
  - postgres://username:password@host:port

storage:
  - gdrive://username:token

loggers:
  - logs://username:password@host:port?command="docker logs api"

notifiers:
  - discord://webhook-uri

rotation_days: 7
```

## Databases
Right now, this app supports **MongoDB** and **PostgreSQL 12**. If you need support for an additional database, consider opening a pull request to add a new database handler.

**Note: It is currently not possible to configure more than one of each database.**

#### MongoDB
- Add a connstring to the `databases` list with this format: `mongodb://username:password@host:port`.
- To restore from the backup, use `mongorestore --gzip --archive=/path/to/backup.archive`

#### Postgres
- Add a connstring to the `databases` list with this format: `postgresql://username:password@host:port`.
- To restore from the backup, use `psql -f /path/to/backup.sql`

## Loggers
A logger is a connstring used to fetch a log. For example, with `logs://user:password@host:port?command="docker logs api"`, blackbox will ssh to `host:port` using the provided username and password, and then run the command `docker logs api`. It will store the output from this command to a file named something like `blackbox_logs_docker_logs_api_01_01_2021.log`, and then upload it to all your configured storage providers.

We only support a single generic connstring format for logging, and that's this one where you provide your own command. You **must** always provide a command, but the other parameters are optional. For example, `logs://?command="kubectl logs server"` is a valid connstring which will run the command on the local machine.

**# TODO: Maybe an image here showcasing the log output**

## Storage providers
`blackbox` can work with different storage providers to save your logs and backups - usually so that you can automatically store them in the cloud. Right now we only support **Google Drive**, but we will probably add additional providers in the future.

**Note: It is currently not possible to configure more than one of each storage type.**

#### Google Drive
- Add a connstring to the `storage` list with this format: `gdrive://user:token`

## Notifiers
`blackbox` also implements different _notifiers_, which is how it reports the result of one of its jobs to you. Right now we only support **Discord**, but if you need a specific notifier, feel free to open an issue.

**# TODO: Add an image showing off the Discord webhook here**

#### Discord
- Add a connstring to the `notifiers` list with this format:
  `discord://<webhook-uri>`

##  Rotation
By default, `blackbox` will automatically remove all backup files older than 7 days in the folder you configure for your storage provider. To determine if something is a backup file or not, it will use a regex pattern that corresponds with the default file it saves, for example `blackbox-postgres-backup-11-12-2020.sql`.

You can configure the number of days before rotating by altering the `rotation_days` parameter in `config.yaml`.
