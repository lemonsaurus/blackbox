![blackbox](img/blackbox_banner.png)
A simple service which magically backs up all your databases to all your favorite cloud storage providers, and then notifies you.

Simply create a config file, fill in some connection strings for your favorite services, and schedule `blackbox` to run however often you want using something like `cron`.

# Setup
This service can either be set up as a cron job (on UNIX systems), as a Kubernetes CronJob, or scheduled in your favorite alternative scheduler.

### Setting up as a cron job
All you need to do to set it up as a cron job is clone this repo, create a config file (see below), and trigger `main.py` to run automatically however often you want.
```yaml
# example cron file
```

### Setting it up as a Kubernetes CronJob
Here's an example manifest you can use if you want to run this in a Kubernetes cluster.
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
  - s3://my-s3-bucket.com/my/folder?user=daniel&password=n0tf4nny

loggers:
  - logs://username:password@host:port?command="docker logs api"

notifiers:
  - https://discord.com/api/webhooks/797541821394714674/lzRM9DFggtfHZXGJTz3yE-MrYJ-4O-0AbdQg3uV2x4vFbu7HTHY2Njq8cx8oyMg0T3Wk

retention_days: 7
```

## Databases
Right now, this app supports **MongoDB** and **PostgreSQL 12**. If you need support for an additional database, consider opening a pull request to add a new database handler.

**Note: It is currently not possible to configure more than one of each database.**

### MongoDB
- Add a connstring to the `databases` list with this format: `mongodb://username:password@host:port`.
- To restore from the backup, use `mongorestore --gzip --archive=/path/to/backup.archive`

### Postgres
- Add a connstring to the `databases` list with this format: `postgresql://username:password@host:port`.
- To restore from the backup, use `psql -f /path/to/backup.sql`

## Storage providers
**Blackbox** can work with different storage providers to save your logs and backups - usually so that you can automatically store them in the cloud. Right now we only support **S3**, but we will probably add additional providers in the future.

**Note: It is currently not possible to configure more than one of each storage type.**

### S3
We support any S3 object storage bucket, whether it's from **AWS**, **Linode**, **DigitalOcean**, **Scaleway**, or another S3-compatible object storage provider.

**Blackbox** will respect the `retention_days` configuration setting and delete older files from the S3 storage. Please note that if you have a bucket expiration policy on your storage, **blackbox** will not do anything to disable it. So, for example, if your bucket expiration policy is 12 hours and blackbox is set to 7 `retention_days`, then your backups are all gonna be deleted after 12 hours unless you disable your policy.  

#### Connection string
`s3://[host][path]?user=[user]&password=[password]` 
- If the bucket is public, no user or password needs to be provided
- `path` is always optional
- For example, for a password protected bucket where you save stuff in subfolders, the connstring might be `s3://my-s3-bucket.com/my/folder?user=daniel&password=n0tf4nny`
- For a public bucket where everything is dumped into root, it might simply be `s3://my-s3-bucket.com`

## Notifiers
`blackbox` also implements different _notifiers_, which is how it reports the result of one of its jobs to you. Right now we only support **Discord**, but if you need a specific notifier, feel free to open an issue.

![blackbox](img/blackbox_discord.png)
![blackbox](img/blackbox_discord_2.png)

### Discord
To set this up, simply add a valid Discord webhook URL to the `notifiers` list. 

These usually look something like `https://discord.com/api/webhooks/797541821394714674/lzRM9DFggtfHZXGJTz3yE-MrYJ-4O-0AbdQg3uV2x4vFbu7HTHY2Njq8cx8oyMg0T3Wk`, but we also support `ptb.discord.com` and `canary.discord.com` webhooks.

##  Rotation
By default, `blackbox` will automatically remove all backup files older than 7 days in the folder you configure for your storage provider. To determine if something is a backup file or not, it will use a regex pattern that corresponds with the default file it saves, for example `blackbox-postgres-backup-11-12-2020.sql`.

You can configure the number of days before rotating by altering the `retention_days` parameter in `config.yaml`.

## Loggers
**NOTE: This feature has not been released yet**

A logger is a connstring used to fetch a log. For example, with `logs://user:password@host:port?command="docker logs api"`, blackbox will ssh to `host:port` using the provided username and password, and then run the command `docker logs api`. It will store the output from this command to a file named something like `blackbox_logs_docker_logs_api_01_01_2021.log`, and then upload it to all your configured storage providers.

We only support a single generic connstring format for logging, and that's this one where you provide your own command. You **must** always provide a command, but the other parameters are optional. For example, `logs://?command="kubectl logs server"` is a valid connstring which will run the command on the local machine.

**# TODO: Maybe an image here showcasing the log output**
