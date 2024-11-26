# Service Uptime Notification Script

This script can be run on a cron job to send email notifications when a service is down. The script is content agnostic and everything is setup through a JSON file, making it flexible enough for any project.

## Usage:

```
usage: main.py [-h] [-p PATH] [--debug]

options:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  Path to the config file, defaults to "./config.json".
  --debug               Whether to also log successes
```

## Prerequisites

You'll need to setup an email account for the notifications to come from. Recommend a Gmail account. If using a Gmail account, you will need to get an app password, see [here](https://support.google.com/mail/answer/185833?hl=en). Create a `.env` file and set the app password like so:

```
EMAIL_APP_PASSWORD=""
```

## Config File Schema

#### Contacts

```json
{
  "contacts": {
    "source": {
      "account": "The email handle (i.e. 'biomarkerpartnership')",
      "service": "The email service (i.e. '@gmail.com')"
    },
    "recipients": [
      "List of email addresses to notify if a service is detected as down."
    ],
    "script_recipients": [
      "List of email addresses to notify is the script fails for another reason."
    ]
  }
}
```

#### Email Metadata

```json
{
    "email_metadata": {
        "subject": "The email subject line."
    }
}
```

#### Tests

```json
{
    "tests": {
        "test_1_name": {
            "url": "URL to test",
            "type": "REST API call type (i.e. `get`, `post`)",
            "payload": "The JSON payload if a post call (optional).",
            "query_args": "Object of query string arguments if a get call (optional).",
            "accept": ["List of acceptable HTTP status codes (i.e. [200, 304])"]
        }
    }
}
```

Note: Currently only `get` and `post` calls are supported. If another REST call type is needed, can add support for with just 3 or 4 lines of code after [line 97](https://github.com/GW-HIVE/uptime-check/blob/e743140edb3214e7f7188f8da5da2802f7ae0fe7/main.py#L97).

## Cron Job

To setup the script to run on an interval, you can use cron. To setup a cron job, use `crontab -e` (depending on the VM, might need sudo access).

This will setup the script to run at the start of every hour:

```
0 * * * * python3 /path/to/script
```

See [here](https://crontab.guru/every-1-hour) for testing crontab configurations. To check active cron jobs, can use `crontab -l`.
