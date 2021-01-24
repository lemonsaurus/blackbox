![Lint & Test](https://github.com/lemonsaurus/blackbox/workflows/Lint%20&%20Test/badge.svg)
![Docker Build](https://github.com/lemonsaurus/blackbox/workflows/Docker%20Build/badge.svg)

![blackbox](img/blackbox_banner.png)
A simple service which magically backs up all your databases to all your favorite cloud storage providers, and then notifies you.

Simply create a config file, fill in some connection strings for your favorite services, and schedule `blackbox` to run however often you want using something like `cron`.

# Setup
This service can either be set up as a cron job (on UNIX systems), as a Kubernetes CronJob, or scheduled in your favorite alternative scheduler.

### Setting up as a cron job
All you need to do to set it up as a cron job is clone this repo, create a config file (see below), and trigger `main.py` to run automatically however often you want.
```yaml
# TODO: Example cron file
```

### Setting it up as a Kubernetes CronJob
Here's an example manifest you can use if you want to run this in a Kubernetes cluster.
```yaml
# TODO: Example CronJob manifest
```

# Configuration
`blackbox` can be configured in a number of ways. To set it up, create a `config.yaml` file in the root folder. Here's an example of what it should contain:
```yaml
databases:
  - mongodb://username:password@host:port
  - postgres://username:password@host:port
  - redis://password@host:port

storage:
  - s3://s3.eu-west-1.amazonaws.com:bucket.example.com?aws_access_key_id=1234&aws_secret_access_key=lemondance

notifiers:
  - https://discord.com/api/webhooks/797541821394714674/lzRM9DFggtfHZXGJTz3yE-MrYJ-4O-0AbdQg3uV2x4vFbu7HTHY2Njq8cx8oyMg0T3Wk

retention_days: 7
```

## Environment Variables

The `config.yaml` will ✨ **magically interpolate** ✨ any environment variables that exist in the environment where `blackbox` is running. This is very useful if you want to keep your secrets in environment variables, instead of keeping them in the config file in plaintext.

#### Example
Imagine your current config looks like this, but you want to move the username and password into environment variables.
```yaml
databases:
  - mongodb://lemonsaurus:security-is-overrated@mongo.lemonsaur.us:1234
```

So we'll create two environment variables like these:
```sh
export MONGO_USERNAME=lemonsaurus
export MONGO_PASSWORD=security-is-overrated
```

And now we can make use of these environment variables by using double curly brackets, like this:
```yaml
databases:
  - mongodb://{{ MONGO_USERNAME }}:{{ MONGO_PASSWORD }}@mongo.lemonsaur.us:1234
```

## Databases
Right now, this app supports **MongoDB**, **PostgreSQL 12** and **Redis**. If you need support for an additional database, consider opening a pull request to add a new database handler.

**Note: It is currently not possible to configure more than one of each database.**

### MongoDB
- Add a connstring to the `databases` list with this format: `mongodb://username:password@host:port`.
- To restore from the backup, use `mongorestore --gzip --archive=/path/to/backup.archive`

### Postgres
- Add a connstring to the `databases` list with this format: `postgresql://username:password@host:port`.
- To restore from the backup, use `psql -f /path/to/backup.sql`

### Redis
- Add a connstring to the `databases` list with this format: `redis://password@host:port`.

#### To restore from the backup
- Stop Redis server.
- Turn off `appendonly` mode in Redis configuration (set to `no`).
- Copy backup file to Redis working directory (`dir` in configuration) with name that is defined in configuration key `dbfilename`.
- Set backup permissions.
```
sudo chown redis:redis <path-to-redis-dump-file>
sudo chmod 660 <path-to-redis-dump-file>
```
- Start Redis server.

If you want to re-enable `appendonly`:
- Login with `redis-cli`.
- Run `BGREWRITEAOF`.
- Exit from Redis CLI (with `exit`).
- Stop Redis server.
- Set `appendonly` to `yes` in Redis configuration.
- Start Redis server.

## Storage providers
**Blackbox** can work with different storage providers to save your logs and backups - usually so that you can automatically store them in the cloud. Right now we only support **S3**, but we will probably add additional providers in the future.

**Note: It is currently not possible to configure more than one of each storage type.**

### S3
We support any S3 object storage bucket, whether it's from **AWS**, **Linode**, **DigitalOcean**, **Scaleway**, or another S3-compatible object storage provider.

**Blackbox** will respect the `retention_days` configuration setting and delete older files from the S3 storage. Please note that if you have a bucket expiration policy on your storage, **blackbox** will not do anything to disable it. So, for example, if your bucket expiration policy is 12 hours and blackbox is set to 7 `retention_days`, then your backups are all gonna be deleted after 12 hours unless you disable your policy.

#### Connection string
```json
s3://<s3 base endpoint>:<s3 bucket endpoint>?<parameter=value>&...

Valid strings:
- s3://s3.eu-west-1.amazonaws.com:bucket.example.com?aws_access_key_id=1234&aws_secret_access_key=lemondance
- s3://s3.eu-west-1.amazonaws.com:bucket.example.com
```

#### Credentials
To upload stuff to S3, you'll need credentials. Your **AWS credentials** can be provided in several ways. This is the order in which blackbox looks for them:
- First, we look for the optional parameters in the s3 connection string, called `aws_access_key_id` and `aws_secret_access_key`.
- If these are not found, we'll check if the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables are declared in the local environment where Blackbox is running.
- If we can't find these, we'll look for an `.aws/config` file in the local environment.
- NOTE: If the bucket is public, no credentials are necessary.

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
