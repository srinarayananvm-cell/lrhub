from django.core.mail.backends.console import EmailBackend

class NoWrapConsoleEmailBackend(EmailBackend):
    def write_message(self, message):
        # Print raw payload without quoted-printable wrapping
        print(message.message().as_string().replace("=\n", ""))
