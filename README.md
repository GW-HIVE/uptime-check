# Service Uptime Notification Script

This script can be run on through a cron job to send email notifications when a service is down. The script is content agnostic and everything is setup through a JSON file.

## Usage:

```
usage: main.py [-h] -p PATH

options:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  Path to the config file, defaults to "./config.json".
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
            "query_args": "Query string arguments if a get call (optional).",
            "accept": ["List of acceptable HTTP status codes (i.e. [200, 304])"]
        }
    }
}
```