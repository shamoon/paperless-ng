import os

from django.apps import AppConfig
from odf import text
from odf.opendocument import load

from documents.parsers import DocumentParser


def odt_consumer_declaration(sender, **kwargs):
    return {
        "parser": OdtDocumentParser,
        "weight": 10,
        "mime_types": [
            "application/vnd.oasis.opendocument.text",
        ]
    }


class PaperlessOdtConfig(AppConfig):
    name = 'paperless_odt'

    def ready(self):

        from documents.signals import document_consumer_declaration

        document_consumer_declaration.connect(odt_consumer_declaration)

        AppConfig.ready(self)


class OdtDocumentParser(DocumentParser):

    def get_thumbnail(self):
        return os.path.join(os.path.dirname(__file__), "document.png")

    def get_text(self):
        doc = load(self.document_path)

        content = ""

        for e in doc.getElementsByType(text.P):
            content += str(e) + "\n"

        return content
