![Lint & Test](https://github.com/lemonsaurus/blackbox/workflows/Lint%20&%20Test/badge.svg)
![Docker Build](https://github.com/lemonsaurus/blackbox/workflows/Docker%20Build/badge.svg)

![blackbox](img/blackbox_banner.png)
A simple service which magically backs up all your databases to all your favorite cloud storage providers, and then notifies you.

Simply create a config file, fill in some connection strings for your favorite services, and schedule `blackbox` to run however often you want using something like `cron`, or a Kubernetes CronJob.

# Setup
This service can either be set up as a cron job (on UNIX systems), as a Kubernetes CronJob, or scheduled in your favorite alternative scheduler.

## Quick start
Requires Python 3.9 or newer

```sh
# Install the CLI tool
pip install blackbox-cli

# Create a configuration file
blacbox --init
```

### Setting up as a cron job

All you need to do to set it up as a cron job is clone this repo, create a config file (see below), and trigger `blackbox` to run automatically however often you want.

```sh
crontab -e

#run backup every hour
0 */1 * * * blackbox --config path/to/blackbox.yml
```

### Setting it up as a Kubernetes CronJob

To set this up as a Kubernetes CronJob, you'll want three manifests and a secret.

Before we start, you'll probably want to create a Secret where you expose environment variables containing stuff like passwords for your databases, credentials for your storage, and webhooks as environment variables. We'll be interpolating those into the config file.

Next, we'll need a ConfigMap for the `blackbox.yaml` config file. See the Configuration section below for more information on what to put inside this file.
```yaml
# blackbox-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: blackbox-config
data:
  blackbox.yaml: |
    databases:
      - mongodb://{{ MONGO_INITDB_ROOT_USERNAME }}:{{ MONGO_INITDB_ROOT_PASSWORD }}@mongodb.default.svc.cluster.local:27017
      - postgres://{{ POSTGRES_USER }}:{{ POSTGRES_PASSWORD }}@postgres.default.svc.cluster.local:5432

    storage:
      - s3://blackbox:my.s3.com?aws_access_key_id={{ AWS_ACCESS_KEY_ID }}&aws_secret_access_key={{ AWS_SECRET_ACCESS_KEY }}

    notifiers:
      - {{ DISCORD_WEBHOOK }}

    retention_days: 7
```

Next, we'll need to configure the `BLACKBOX_CONFIG_PATH`, which tells Blackbox where to find the config file. This doesn't need to be a secret, so we'll just put that into a regular ConfigMap.
```yaml
# env-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: blackbox-env
data:
  # Set the config file location
  BLACKBOX_CONFIG_PATH: "/blackbox/config_file/blackbox.yaml"
```

Finally, we need the CronJob itself. This one is configured to run once a day, at midnight.
```yaml
# cronjob.yaml
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: blackbox
spec:
  schedule: "@daily"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: blackbox
            image: lemonsaurus/blackbox
            imagePullPolicy: Always
            envFrom:
              - secretRef:
                  name: blackbox-secrets
              - configMapRef:
                  name: blackbox-env
            volumeMounts:
              # Take care not to mount this in the root folder!
              # That will replace everything in the root folder with
              # the contents of this volume, which sucks.
              - mountPath: /blackbox/config_file
                name: blackbox-config
          volumes:
            - name: blackbox-config
              configMap:
                name: blackbox-config
          restartPolicy: OnFailure
      backoffLimit: 3
```

# Configuration
`blackbox` configuration is easy. You simply create a yaml file, `blackbox.yaml`, which contains something like this:

```yaml
databases:
  - mongodb://username:password@host:port
  - postgres://username:password@host:port
  - redis://password@host:port

storage:
  - s3://bucket:s3.endpoint.com?aws_access_key_id=1234&aws_secret_access_key=lemondance
  - dropbox://abyhhdhhfdbgdDjurajlgcfs?upload_directory=/testing/

notifiers:
  - https://discord.com/api/webhooks/797541821394714674/lzRM9DFggtfHZXGJTz3yE-MrYJ-4O-0AbdQg3uV2x4vFbu7HTHY2Njq8cx8oyMg0T3Wk
  - https://hooks.slack.com/services/XXXXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXXXXXXX

retention_days: 7
```

Blackbox will look for this file in the root folder by default, however you can provide an alternative config file path by creating an environment variable called `BLACKBOX_CONFIG_PATH`, and set it to the absolute path of the file.

```sh
export BLACKBOX_CONFIG_PATH=/var/my/favorite/fruit/blackbox.yaml
```

## Environment Variables
The `blackbox.yaml` will ✨ **magically interpolate** ✨ any environment variables that exist in the environment where `blackbox` is running. This is very useful if you want to keep your secrets in environment variables, instead of keeping them in the config file in plaintext.

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
**Blackbox** can work with different storage providers to save your logs and backups - usually so that you can automatically store them in the cloud. Right now we support **S3** and **Dropbox**.

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

### Dropbox
The Dropbox storage handler needs a user access token in order to work. To get one, do the following:

- Create a Dropbox account (if you don't already have one).
- Go to https://dropbox.com/developers
- Create a new application with App Folder access. **Do not give it full access**, as this may have dangerous, destructive consequences if configured incorrectly.

You can also define a custom location (root is App Folder) using the
`upload_directory` optional parameter. This **should** begin with slash
and **must** end with slash. Default is root.

The configuration connections strings may look like the following:

```
dropbox://<access-token>
dropbox://<access-token>?upload_directory=/foobar/
```

## Notifiers
`blackbox` also implements different _notifiers_, which is how it reports the result of one of its jobs to you. Right now we only support **Discord**, but if you need a specific notifier, feel free to open an issue.

### Discord
To set this up, simply add a valid Discord webhook URL to the `notifiers` list.

These usually look something like `https://discord.com/api/webhooks/797541821394714674/lzRM9DFggtfHZXGJTz3yE-MrYJ-4O-0AbdQg3uV2x4vFbu7HTHY2Njq8cx8oyMg0T3Wk`, but we also support `ptb.discord.com` and `canary.discord.com` webhooks.

![blackbox](img/blackbox_discord.png)
![blackbox](img/blackbox_discord_2.png)

### Slack
To set this up, simply add a valid Slack incoming webhook URL to the `notifiers` list.
These look like `https://hooks.slack.com/services/XXXXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXXXXXXX`.

Slack notifier have 2 styles: legacy attachment (default) and modern Block Kit version.
To enable Block Kit version, add `?use_block_kit=1` to end of webhook URL.

Default:

![blackbox](img/blackbox_slack_default_success.png)
![blackbox](img/blackbox_slack_default_fail.png)

Modern:

![blackbox](img/blackbox_slack_modern_success.png)
![blackbox](img/blackbox_slack_modern_fail.png)

## Rotation
By default, `blackbox` will automatically remove all backup files older than 7 days in the folder you configure for your storage provider. To determine if something is a backup file or not, it will use a regex pattern that corresponds with the default file it saves, for example `blackbox-postgres-backup-11-12-2020.sql`.

You can configure the number of days before rotating by altering the `retention_days` parameter in `blackbox.yaml`.
