import requests
import traceback
from dotenv import load_dotenv
import json
import smtplib
from email.mime.text import MIMEText
import logging
import os
import sys
from argparse import ArgumentParser
from typing import Optional, Dict, List


def send_email(msg: str, contacts: Dict, metadata: Dict, failure_type: int = 0) -> None:
    """Emails a message with failure reports.

    Parameters
    ----------
    msg: str
        The message to email.
    contacts: dict
        The source and recipient contact info.
    metadata: dict
        The email metadata.
    failure_type: int, optional
        0 to send to all recipients, 1 to send just to script recipients.
    """
    email_app_password = os.environ.get("EMAIL_APP_PASSWORD", None)
    if email_app_password is None:
        logging.error("Error grabbing email app password environment variable.")
        sys.exit(1)

    recipients = (
        contacts["recipients"] if failure_type == 0 else contacts["script_recipient"]
    )
    email_message = MIMEText(msg)
    email_message["Subject"] = metadata["subject"]
    email_message["To"] = ", ".join(recipients)
    email_message["From"] = "{}{}".format(
        contacts["source"]["account"], contacts["source"]["service"]
    )

    try:
        smtp_server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        smtp_server.login(
            user=contacts["source"]["account"], password=email_app_password
        )
        smtp_server.sendmail(
            from_addr=email_message["From"],
            to_addrs=recipients,
            msg=email_message.as_string(),
        )
        smtp_server.quit()
    except Exception as e:
        logging.error(f"Error sending email: {e}\n{traceback.format_exc()}")


def run_tests(tests: Dict) -> Optional[str]:
    """Runs the config tests.

    Parameters
    ----------
    tests: dict
        The test structures.

    Returns
    -------
    str or None
        None on success, a description of the test failures on a failure.
    """
    error_messages: List[str] = []

    for test_name, test_details in tests.items():

        url = test_details["url"].lower().strip()
        rest_type = test_details["type"].lower().strip()
        accept_codes = test_details["accept"]
        args = None
        response = None

        try:
            if rest_type == "get":
                args = {"params": test_details.get("query_args", None)}
                response = requests.get(url=url, timeout=60, **args)
            elif rest_type == "post":
                args = {"json": test_details.get("payload", None)}
                response = requests.post(url=url, timeout=60, **args)
            else:
                logging.error(f"Unsupported REST type: `{rest_type}`.")
                continue

            if response.status_code not in accept_codes:
                message = f"Test `{test_name.replace('_', ' ')}`\n"
                message += f"\tURL: {url}\n"
                message += f"\tExpected status codes: {accept_codes}\n"
                message += f"\tGot: {response.status_code}\n"
                error_messages.append(message)
                logging.error(f"{message}\nContent: {str(response.content)}")
        except Exception as e:
            logging.error(
                f"Unexpected failure for `{test_name}`: {e}\n{traceback.format_exc()}"
            )
            raise

    if error_messages:
        return "\n".join(error_messages)

    return None


def main() -> None:

    parser = ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        default="./config.json",
        required=True,
        help='Path to the config file, defaults to "./config.json".',
    )
    options = parser.parse_args()

    try:
        with open(options.path, "r") as f:
            config = json.load(f)
    except Exception:
        print("Error opening config file.")
        sys.exit(1)

    contacts = config["contacts"]
    tests = config["tests"]
    email_metadata = config["email_metadata"]

    load_dotenv()

    try:
        test_results = run_tests(tests)
        if test_results is not None:
            logging.warning("API or service tests failed. Sending alert email.")
            send_email(
                msg=test_results,
                contacts=contacts,
                metadata=email_metadata,
                failure_type=0,
            )

    except Exception as e:
        logging.error(f"Script encountered an error: {e}\n{traceback.format_exc()}")
        send_email(
            msg=f"Script error: {e}\n{traceback.format_exc()}",
            contacts=config["contacts"],
            metadata=config["email_metadata"],
            failure_type=1,
        )
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("service_monitor.log"), logging.StreamHandler()],
    )
    main()
