MIME_CATEGORIES: dict[str, list[str]] = {
    "Image": [
        "image/jpeg", "image/png", "image/gif", "image/bmp",
        "image/svg+xml", "image/webp", "image/tiff",
        "image/avif", "image/heic", "image/heif", "image/x-icon",
        "image/vnd.adobe.photoshop"
    ],
    "Document": [
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain", "text/markdown", "application/vnd.oasis.opendocument.text",
        "application/x-abiword", "application/xhtml+xml", "application/rtf",
        "application/ld+json"
    ],
    "Spreadsheet": [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv", "application/vnd.oasis.opendocument.spreadsheet",
        "text/tab-separated-values"
    ],
    "Video": [
        "video/mp4", "video/x-matroska", "video/quicktime",
        "video/x-msvideo", "video/webm",
        "video/3gpp", "video/3gpp2", "video/ogg", "video/x-flv", "video/mp2t"
    ],
    "Music": [
        "audio/mpeg", "audio/wav", "audio/x-flac", "audio/flac",
        "audio/ogg", "audio/webm", "audio/aac", "audio/opus",
        "audio/mp4", "audio/midi", "audio/x-midi", "audio/3gpp"
    ],
    "Archive": [
        "application/zip", "application/x-zip-compressed",
        "application/x-rar-compressed", "application/vnd.rar",
        "application/x-tar", "application/gzip", "application/x-7z-compressed",
        "application/x-bzip2", "application/x-xz",
        "application/java-archive",
        "application/vnd.ms-cab-compressed",
        "application/x-iso9660-image",
        "application/zstd"
    ],
    "Script": [
        "text/x-python", "application/x-sh", "application/x-bat",
        "application/javascript", "application/x-javascript", "text/javascript",
        "text/typescript", "application/typescript",
        "text/x-ruby", "text/x-c++src", "text/x-csrc",
        "text/x-java-source", "text/html", "text/css",
        "application/x-httpd-php", "text/x-php", "application/x-perl"
    ],
    "Executable": [
        "application/vnd.microsoft.portable-executable",
        "application/x-msdownload", "application/x-msinstaller",
        "application/vnd.android.package-archive",
        "application/x-dosexec", "application/x-mach-binary",
        "application/x-executable", "application/x-appimage",
        "application/x-apple-diskimage"
    ],
    "Presentation": [
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.slideshow"
    ],
    "Misc": []
}

EXTENSION_TO_MIME: dict[str, list[str]] = {
    # Images
    ".jpg": ["image/jpeg"], ".jpeg": ["image/jpeg"], ".jpe": ["image/jpeg"],
    ".png": ["image/png"], ".gif": ["image/gif"], ".bmp": ["image/bmp"],
    ".svg": ["image/svg+xml"], ".svgz": ["image/svg+xml"], ".webp": ["image/webp"],
    ".tif": ["image/tiff"], ".tiff": ["image/tiff"],
    ".heic": ["image/heic"], ".heif": ["image/heif"],
    ".ico": ["image/x-icon"], ".avif": ["image/avif"],
    ".psd": ["image/vnd.adobe.photoshop"], ".ai": ["application/postscript"],
    ".eps": ["application/postscript"],

    # Documents / Text
    ".pdf": ["application/pdf"], ".rtf": ["application/rtf"],
    ".doc": ["application/msword"],
    ".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    ".odt": ["application/vnd.oasis.opendocument.text"],
    ".abw": ["application/x-abiword"],
    ".txt": ["text/plain"], ".md": ["text/markdown"], ".rst": ["text/x-rst"],
    ".tex": ["text/x-tex"], ".log": ["text/plain"],
    ".xhtml": ["application/xhtml+xml"],
    ".json": ["application/json"], ".jsonld": ["application/ld+json"],
    ".ipynb": ["application/x-ipynb+json"],
    ".yaml": ["application/yaml", "text/yaml"], ".yml": ["application/yaml", "text/yaml"],
    ".toml": ["application/toml"], ".ini": ["text/plain"],
    ".xml": ["application/xml", "text/xml"],
    ".ics": ["text/calendar"],

    # Spreadsheets / Data tables
    ".xls": ["application/vnd.ms-excel"],
    ".xlsx": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
    ".ods": ["application/vnd.oasis.opendocument.spreadsheet"],
    ".csv": ["text/csv"], ".tsv": ["text/tab-separated-values"],

    # Presentations
    ".ppt": ["application/vnd.ms-powerpoint"],
    ".pptx": ["application/vnd.openxmlformats-officedocument.presentationml.presentation"],
    ".pptm": ["application/vnd.ms-powerpoint.presentation.macroEnabled.12"],
    ".pps": ["application/vnd.ms-powerpoint"],
    ".ppsx": ["application/vnd.openxmlformats-officedocument.presentationml.slideshow"],
    ".odp": ["application/vnd.oasis.opendocument.presentation"],

    # Archives / Packages
    ".zip": ["application/zip"],
    ".rar": ["application/vnd.rar", "application/x-rar-compressed"],
    ".7z": ["application/x-7z-compressed"],
    ".tar": ["application/x-tar"],
    ".gz": ["application/gzip"],
    ".bz": ["application/x-bzip"], ".bz2": ["application/x-bzip2"],
    ".xz": ["application/x-xz"],
    ".tar.gz": ["application/gzip"], ".tgz": ["application/gzip"],
    ".tar.bz2": ["application/x-bzip2"], ".tbz2": ["application/x-bzip2"],
    ".tar.xz": ["application/x-xz"], ".txz": ["application/x-xz"],
    ".zst": ["application/zstd"],
    ".iso": ["application/x-iso9660-image"],
    ".jar": ["application/java-archive"], ".war": ["application/java-archive"], ".ear": ["application/java-archive"],
    ".cab": ["application/vnd.ms-cab-compressed"],
    ".deb": ["application/vnd.debian.binary-package"], ".udeb": ["application/vnd.debian.binary-package"],
    ".rpm": ["application/x-rpm"],

    # Audio
    ".mp3": ["audio/mpeg"], ".wav": ["audio/wav"],
    ".flac": ["audio/flac", "audio/x-flac"],
    ".ogg": ["audio/ogg"], ".oga": ["audio/ogg"],
    ".opus": ["audio/opus"],
    ".m4a": ["audio/mp4"], ".aac": ["audio/aac"],
    ".mid": ["audio/midi", "audio/x-midi"], ".midi": ["audio/midi", "audio/x-midi"],
    ".weba": ["audio/webm"],

    # Video
    ".mp4": ["video/mp4"], ".m4v": ["video/x-m4v", "video/mp4"],
    ".mkv": ["video/x-matroska"], ".mov": ["video/quicktime"],
    ".avi": ["video/x-msvideo"], ".webm": ["video/webm"],
    ".flv": ["video/x-flv"], ".3gp": ["video/3gpp"], ".3g2": ["video/3gpp2"],
    ".ogv": ["video/ogg"], ".mpeg": ["video/mpeg"], ".mpg": ["video/mpeg"],
    ".ts": ["video/mp2t"],

    # Code / Scripts / Config
    ".py": ["text/x-python"], ".pyw": ["text/x-python"],
    ".sh": ["application/x-sh"], ".bat": ["application/x-bat"],
    ".ps1": ["application/x-powershell"],
    ".js": ["application/javascript"], ".mjs": ["application/javascript"],
    ".ts": ["application/typescript", "text/typescript"],
    ".c": ["text/x-c"], ".h": ["text/x-c"],
    ".cpp": ["text/x-c++src"], ".hpp": ["text/x-c++hdr"],
    ".java": ["text/x-java-source"], ".cs": ["text/x-csharp"], ".go": ["text/x-go"],
    ".rs": ["text/rust"], ".php": ["application/x-httpd-php", "text/x-php"],
    ".rb": ["text/x-ruby"], ".kt": ["text/x-kotlin"], ".swift": ["text/x-swift"],
    ".pl": ["application/x-perl"], ".lua": ["text/x-lua"],
    ".html": ["text/html"], ".htm": ["text/html"],
    ".css": ["text/css"],
    ".sql": ["application/sql"],

    # Fonts
    ".ttf": ["font/ttf"], ".otf": ["font/otf"],
    ".ttc": ["font/collection"],
    ".woff": ["font/woff"], ".woff2": ["font/woff2"],
    ".eot": ["application/vnd.ms-fontobject"],

    # Executables / Installers / Images
    ".exe": ["application/x-msdownload"],
    ".msi": ["application/x-msi", "application/x-msdownload"],
    ".apk": ["application/vnd.android.package-archive"],
    ".dmg": ["application/x-apple-diskimage"],
    ".appimage": ["application/x-appimage"],
    ".bin": ["application/octet-stream"],
    ".so": ["application/x-sharedlib"],
    ".dll": ["application/x-msdownload"],

    # Databases / Data formats
    ".sqlite": ["application/x-sqlite3"], ".db": ["application/x-sqlite3"],
    ".mdb": ["application/x-msaccess"], ".accdb": ["application/x-msaccess"],
    ".parquet": ["application/vnd.apache.parquet"],

    # eBooks
    ".epub": ["application/epub+zip"],
    ".mobi": ["application/x-mobipocket-ebook"],

    # GIS / Geo
    ".geojson": ["application/geo+json"],
    ".kml": ["application/vnd.google-earth.kml+xml"],
    ".kmz": ["application/vnd.google-earth.kmz"],

    # 3D / CAD
    ".stl": ["model/stl"],
    ".gltf": ["model/gltf+json"], ".glb": ["model/gltf-binary"],
    ".dae": ["model/vnd.collada+xml"],
    ".fbx": ["application/octet-stream"]
}
