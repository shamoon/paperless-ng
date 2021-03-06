import json
import os
import shutil
import time

from django.core import serializers
from django.core.management.base import BaseCommand, CommandError

from documents.models import Document, Correspondent, Tag, DocumentType
from documents.settings import EXPORTER_FILE_NAME, EXPORTER_THUMBNAIL_NAME, \
    EXPORTER_ARCHIVE_NAME
from paperless.db import GnuPG
from ...mixins import Renderable


class Command(Renderable, BaseCommand):

    help = """
        Decrypt and rename all files in our collection into a given target
        directory.  And include a manifest file containing document data for
        easy import.
    """.replace("    ", "")

    def add_arguments(self, parser):
        parser.add_argument("target")

    def __init__(self, *args, **kwargs):
        BaseCommand.__init__(self, *args, **kwargs)
        self.target = None

    def handle(self, *args, **options):

        self.target = options["target"]

        if not os.path.exists(self.target):
            raise CommandError("That path doesn't exist")

        if not os.access(self.target, os.W_OK):
            raise CommandError("That path doesn't appear to be writable")

        self.dump()

    def dump(self):

        documents = Document.objects.all()
        document_map = {d.pk: d for d in documents}
        manifest = json.loads(serializers.serialize("json", documents))

        for index, document_dict in enumerate(manifest):

            # Force output to unencrypted as that will be the current state.
            # The importer will make the decision to encrypt or not.
            manifest[index]["fields"]["storage_type"] = Document.STORAGE_TYPE_UNENCRYPTED  # NOQA: E501

            document = document_map[document_dict["pk"]]

            unique_filename = f"{document.pk:07}_{document.file_name}"
            file_target = os.path.join(self.target, unique_filename)

            thumbnail_name = unique_filename + "-thumbnail.png"
            thumbnail_target = os.path.join(self.target, thumbnail_name)

            document_dict[EXPORTER_FILE_NAME] = unique_filename
            document_dict[EXPORTER_THUMBNAIL_NAME] = thumbnail_name

            if os.path.exists(document.archive_path):
                archive_name = \
                    f"{document.pk:07}_archive_{document.archive_file_name}"
                archive_target = os.path.join(self.target, archive_name)
                document_dict[EXPORTER_ARCHIVE_NAME] = archive_name
            else:
                archive_target = None

            print(f"Exporting: {file_target}")

            t = int(time.mktime(document.created.timetuple()))
            if document.storage_type == Document.STORAGE_TYPE_GPG:

                with open(file_target, "wb") as f:
                    f.write(GnuPG.decrypted(document.source_file))
                    os.utime(file_target, times=(t, t))

                with open(thumbnail_target, "wb") as f:
                    f.write(GnuPG.decrypted(document.thumbnail_file))
                    os.utime(thumbnail_target, times=(t, t))

                if archive_target:
                    with open(archive_target, "wb") as f:
                        f.write(GnuPG.decrypted(document.archive_path))
                        os.utime(archive_target, times=(t, t))
            else:

                shutil.copy(document.source_path, file_target)
                shutil.copy(document.thumbnail_path, thumbnail_target)

                if archive_target:
                    shutil.copy(document.archive_path, archive_target)

        manifest += json.loads(
            serializers.serialize("json", Correspondent.objects.all()))

        manifest += json.loads(serializers.serialize(
            "json", Tag.objects.all()))

        manifest += json.loads(serializers.serialize(
            "json", DocumentType.objects.all()))

        with open(os.path.join(self.target, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2)
