import re

REF_LINKS = {
    "#sending-files": "sending-files",
}
DOCS_URL = "https://core.telegram.org/bots/api"
ANCHOR_HEADER_PATTERN = re.compile(r"^h([34])$")
READ_MORE_PATTERN = re.compile(
    r" ((More info on|More about)([\W\w]+»)|»)", flags=re.MULTILINE & re.IGNORECASE
)
SYMBOLS_MAP = {"“": "'", "”": "'"}
