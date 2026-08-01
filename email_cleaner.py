from bs4 import BeautifulSoup
import re


def clean_email_body(body):

    if not body:
        return ""

    # Remove HTML
    soup = BeautifulSoup(body, "html.parser")

    # Remove scripts/styles
    for element in soup(["script", "style"]):
        element.decompose()

    text = soup.get_text(separator=" ")

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()