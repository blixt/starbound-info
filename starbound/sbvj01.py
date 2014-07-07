from . import sbon
from . import filebase


class FileSBVJ01(filebase.File):
    def __init__(self, path):
        super(FileSBVJ01, self).__init__(path)
        self.data = None

    def initialize(self):
        """Reads the file contents into a data dict.

        """
        super(FileSBVJ01, self).initialize()

        assert self.read(6) == b'SBVJ01', 'Invalid file format'
        self.identifier, self.version, self.data = sbon.read_document(self._stream)

        # Technically, we could already close the file at this point. Need to
        # think about this.
