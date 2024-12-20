import requests
import traceback
from dotenv import load_dotenv
import json
import smtplib
from email.mime.text import MIMEText
import logging
import os
import time
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


def run_tests(
    tests: Dict, debug: bool = False, max_retries: int = 3, retry_delay: int = 5
) -> Optional[str]:
    """Runs the config tests.

    Parameters
    ----------
    tests: dict
        The test structures.
    debug: bool, optional
        Whether to also log success messages.
    max_retries: int, optional
        Maximum number of retry attempts for failed requests.
    retry_delay: int, optional
        Seconds to sleep between retries.

    Returns
    -------
    str or None
        None on success, a description of the test failures on a failure.
    """
    error_messages: List[str] = []

    for test_name, test_details in tests.items():

        url = test_details["url"].strip()
        rest_type = test_details["type"].lower().strip()
        accept_codes = test_details["accept"]
        args = None
        response = None

        for attempt in range(max_retries):
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

                if response.status_code in accept_codes:
                    if debug:
                        message = f"Successfully completed test: {test_name} (on attempt {attempt + 1})\n"
                        message += f"\tExpected one of: {accept_codes} | Got: {response.status_code}\n"
                        message += f"Text: {str(response.text)}"
                        logging.info(message)
                    break

                if attempt < max_retries - 1:
                    logging.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {test_name}. "
                        f"Status code: {response.status_code}. Retrying in {retry_delay} seconds..."
                    )
                    time.sleep(retry_delay)

            except Exception as e:
                if attempt < max_retries - 1:
                    logging.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {test_name} "
                        f"with error: {str(e)}. Retrying in {retry_delay} seconds..."
                        f"\n{traceback.format_exc()}"
                    )
                else:
                    logging.error(
                        f"All retry attempts failed for `{test_name}`: {e}\n{traceback.format_exc()}"
                    )
                    raise

        if response is None or response.status_code not in accept_codes:
            message = f"Test `{test_name.replace('_', ' ')}` failed after {max_retries} attempts\n"
            message += f"\tURL: {url}\n"
            message += f"\tExpected status codes: {accept_codes}\n"
            message += f"\tGot: {response.status_code if response else 'No response'}"
            error_messages.append(message)
            logging.error(
                f"{message}\nText: {str(response.text) if response else 'No text'}"
            )

    if error_messages:
        return "\n".join(error_messages)

    return None


def main() -> None:

    parser = ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        default="./config.json",
        required=False,
        help='Path to the config file, defaults to "./config.json".',
    )
    parser.add_argument(
        "--debug", action="store_true", help="Whether to also log successes"
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
        test_results = run_tests(tests=tests, debug=options.debug)
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
