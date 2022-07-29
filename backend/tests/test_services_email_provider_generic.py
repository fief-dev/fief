from fief.services.email.generic import Generic


def get_msg(mock):
    smtp = mock.return_value
    server = smtp.__enter__.return_value
    return server.send_message.call_args[0][0]


def send_email(**kwargs):
    email_provider = Generic("localhost", "username", "password")

    email_provider.send_email(
        sender=kwargs.get("sender", ("sender@example.com", None)),
        recipient=kwargs.get("recipient", ("recipient@example.com", None)),
        subject=kwargs.get("subject", "Subject Line"),
        html=kwargs.get("html", "<h1>It Works!</h1>"),
        text=kwargs.get("text", "It Works!"),
    )


def test_send_email_sends_correct_email_content(smtplib_mock):
    send_email()
    msg = get_msg(smtplib_mock)
    assert msg["From"] == "sender@example.com"
    assert msg["To"] == "recipient@example.com"
    assert msg["Subject"] == "Subject Line"
    assert msg.get_body(["plain"]).get_content() == "It Works!\n"
    assert msg.get_body(["html"]).get_content() == "<h1>It Works!</h1>\n"


def test_send_email_formats_to_address(smtplib_mock):
    send_email(recipient=("recipient@example.com", "Jo"))
    msg = get_msg(smtplib_mock)
    assert msg["To"] == "Jo <recipient@example.com>"


def test_send_email_formats_from_address(smtplib_mock):
    send_email(sender=("sender@example.com", "Jo"))
    msg = get_msg(smtplib_mock)
    assert msg["From"] == "Jo <sender@example.com>"


def test_logs_into_server(smtplib_mock):
    send_email()
    smtp = smtplib_mock.return_value
    server = smtp.__enter__.return_value
    username, password = server.login.call_args[0]
    assert username == "username"
    assert password == "password"


def test_startstls(smtplib_mock):
    send_email()
    smtp = smtplib_mock.return_value
    server = smtp.__enter__.return_value
    server.starttls.assert_called()
