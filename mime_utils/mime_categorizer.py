import mimetypes
import magic
import os
from .mime_categories import MIME_CATEGORIES,EXTENSION_TO_MIME
#Borrowed from Decluttr
def get_mime_by_extension(filename):
        extension = os.path.splitext(filename)[-1].lower()
        return EXTENSION_TO_MIME.get(extension, "unknown")
    
def categorize_file(file_path: str) -> str:
        """Returns the file type of the file_path"""
        file_mime = mimetypes.guess_type(file_path)
        filename = os.path.basename(file_path)
        if not file_mime:#If python's mimetypes.guess_type() does NOT work
            mime_magic = magic.Magic(mime=True)
            file_mime = mime_magic.from_file(file_path)
            if not file_mime: #If magic still somehow fails, use custom extension mapping
                file_mime = get_mime_by_extension(filename=filename)

        print(file_mime)
        for category,mime_type in MIME_CATEGORIES.items():
            if file_mime[0] in mime_type:
                return category
        print(category)
        return "Misc"