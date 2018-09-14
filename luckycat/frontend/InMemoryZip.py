import io
import zipfile


class InMemoryZip(object):
    '''
    Original from http://stackoverflow.com/questions/2463770/python-in-memory-zip-library
    '''

    def __init__(self):
        self.in_memory_data = io.BytesIO()
        self.in_memory_zip = zipfile.ZipFile(
            self.in_memory_data, "w", zipfile.ZIP_DEFLATED, False)
        self.in_memory_zip.debug = 3

    def append(self, filename_in_zip, file_contents):
        '''Appends a file with name filename_in_zip and contents of
        file_contents to the in-memory zip.'''
        self.in_memory_zip.writestr(filename_in_zip, file_contents)
        return self

    def writetofile(self, filename):
        '''Writes the in-memory zip to a file.'''
        for zfile in self.in_memory_zip.filelist:
            zfile.create_system = 0
        self.in_memory_zip.close()
        with open(filename, 'wb') as f:
            f.write(self.in_memory_data.getvalue())

    def getvalue(self):
        return self.in_memory_data.getvalue()
