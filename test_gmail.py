
import socket
import smtplib
import ssl

host = "smtp.gmail.com"

for port in [465, 587]:

    print("\nTesting port:", port)

    try:
        if port == 465:
            server = smtplib.SMTP_SSL(
                host,
                port,
                timeout=20,
                context=ssl.create_default_context()
            )
        else:
            server = smtplib.SMTP(
                host,
                port,
                timeout=20
            )

        print("Connected to server")
        print("Server response:", server.ehlo())

        if port == 587:
            print("Starting TLS...")
            print("TLS response:", server.starttls())

        server.quit()
        print("SMTP CONNECTION SUCCESSFUL")

    except Exception as error:
        print("FAILED:", type(error).__name__, str(error))
