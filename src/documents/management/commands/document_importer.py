import json
import os
import shutil

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from documents.models import Document
from documents.settings import EXPORTER_FILE_NAME, EXPORTER_THUMBNAIL_NAME, \
    EXPORTER_ARCHIVE_NAME
from ...file_handling import generate_filename, create_source_path_directory
from ...mixins import Renderable


class Command(Renderable, BaseCommand):

    help = """
        Using a manifest.json file, load the data from there, and import the
        documents it refers to.
    """.replace("    ", "")

    def add_arguments(self, parser):
        parser.add_argument("source")

    def __init__(self, *args, **kwargs):
        BaseCommand.__init__(self, *args, **kwargs)
        self.source = None
        self.manifest = None

    def handle(self, *args, **options):

        self.source = options["source"]

        if not os.path.exists(self.source):
            raise CommandError("That path doesn't exist")

        if not os.access(self.source, os.R_OK):
            raise CommandError("That path doesn't appear to be readable")

        manifest_path = os.path.join(self.source, "manifest.json")
        self._check_manifest_exists(manifest_path)

        with open(manifest_path) as f:
            self.manifest = json.load(f)

        self._check_manifest()

        # Fill up the database with whatever is in the manifest
        call_command("loaddata", manifest_path)

        self._import_files_from_manifest()

    @staticmethod
    def _check_manifest_exists(path):
        if not os.path.exists(path):
            raise CommandError(
                "That directory doesn't appear to contain a manifest.json "
                "file."
            )

    def _check_manifest(self):

        for record in self.manifest:

            if not record["model"] == "documents.document":
                continue

            if EXPORTER_FILE_NAME not in record:
                raise CommandError(
                    'The manifest file contains a record which does not '
                    'refer to an actual document file.'
                )

            doc_file = record[EXPORTER_FILE_NAME]
            if not os.path.exists(os.path.join(self.source, doc_file)):
                raise CommandError(
                    'The manifest file refers to "{}" which does not '
                    'appear to be in the source directory.'.format(doc_file)
                )

            if EXPORTER_ARCHIVE_NAME in record:
                archive_file = record[EXPORTER_ARCHIVE_NAME]
                if not os.path.exists(os.path.join(self.source, archive_file)):
                    raise CommandError(
                        f"The manifest file refers to {archive_file} which "
                        f"does not appear to be in the source directory."
                    )

    def _import_files_from_manifest(self):

        os.makedirs(settings.ORIGINALS_DIR, exist_ok=True)
        os.makedirs(settings.THUMBNAIL_DIR, exist_ok=True)
        os.makedirs(settings.ARCHIVE_DIR, exist_ok=True)

        for record in self.manifest:

            if not record["model"] == "documents.document":
                continue

            document = Document.objects.get(pk=record["pk"])

            doc_file = record[EXPORTER_FILE_NAME]
            document_path = os.path.join(self.source, doc_file)

            thumb_file = record[EXPORTER_THUMBNAIL_NAME]
            thumbnail_path = os.path.join(self.source, thumb_file)

            if EXPORTER_ARCHIVE_NAME in record:
                archive_file = record[EXPORTER_ARCHIVE_NAME]
                archive_path = os.path.join(self.source, archive_file)
            else:
                archive_path = None

            document.storage_type = Document.STORAGE_TYPE_UNENCRYPTED

            document.filename = generate_filename(document)

            if os.path.isfile(document.source_path):
                raise FileExistsError(document.source_path)

            create_source_path_directory(document.source_path)

            print(f"Moving {document_path} to {document.source_path}")
            shutil.copy(document_path, document.source_path)
            shutil.copy(thumbnail_path, document.thumbnail_path)
            if archive_path:
                shutil.copy(archive_path, document.archive_path)

            document.save()
