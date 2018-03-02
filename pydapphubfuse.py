#!/usr/bin/env python3
from fuse import FUSE, FuseOSError, Operations
import sys, errno, os, re, stat

# Don't try to prononce the name of the class
# I'm not liable for the daemons you might 
# summon if you do.
class PydAppHubFuse(Operations):
    def __init__(self, jsonroot):
        self.jsonroot = jsonroot

        # Config file cache
        self.cache = {}

        # Ensuring after open() the result doesn't change
        self.filecache = {}
        # TODO: rely on the set of keys of above instead
        self.lastfd = -1

        # dApp database collected from JSONs 
        # TODO STUB
        self.dapps = { 
            'ivan': { 
                'ports': [1111,2222],
                'desc': 'Ivan service'
            }, 
            'maria': { 
                'ports': [3333,4444],
                'desc': 'Maria service'
            }
        }

    # Classifies the incoming path value:
    #  - None = invalid path
    #  - True = valid directory
    #  - dapp name = valid dapp.conf, corresponding entry is returned
    def classify(self, path):
        # Root is a valid directory
        if path == '/':
            return True
        
        # Check if the directory corresponds to dapp pattern
        # TODO: what are valid dapp names and how they are named anyway?
        m = re.match("^/dapp@([A-Za-z-_]+).service.d(/.*)?$", path)
        if not m:
            return None
        dapp = m.group(1)

        # Check if we are dealing with a directory
        fname = m.group(2)
        if not fname:
            return True

        # Check if we have that dapp
        if dapp not in self.dapps:
            return None

        # Find the entry if the filename is correct
        if fname == '/dapp.conf':
            return dapp 

        return None

    # Same as above but automatically raises ENOENT
    def getobj(self, path):
        obj = self.classify(path)

        # Cut what's not ours
        if not obj:
            raise FuseOSError(errno.ENOENT)

        return obj

    # Generate config data
    def genconfig(self, dapp):
        d = self.dapps[dapp]

        conf = """[Unit]
Description={}
""".format(d['desc'])

        conf += '\n'.join('Wants=forward_port@%d.service' % port for port in d['ports'])

        conf += '\n'

        return conf

    # Get config file data for dapp
    def getconfig(self, dapp):
        # Check cache
        if dapp not in self.cache:
            self.cache[dapp] = self.genconfig(dapp)
        # Okay we need to generate
        return self.cache[dapp]

    def access(self, path, mode):
        obj = self.getobj(path)

        # Allow read/execute on / and valid dirs
        # read only on anything else
        isdir = type(obj) is not str
        if (mode & os.W_OK) or (isdir and mode & os.X_OK):
            raise FuseOSError(errno.EACCESS)

    # TODO: support reading by handle?

    def getattr(self, path, fh):
        obj = self.getobj(path)
        isdir = type(obj) is not str

        # TODO: meaningful values
        st_mode = (stat.S_IFDIR | 0o755) if isdir else (stat.S_IFREG | 0o644)
        st_size = 0 if isdir else len(self.getconfig(obj))
        res = { 
            'st_atime': 0,
            'st_ctime': 0,
            'st_gid':   0,  
            'st_mode':  st_mode,
            'st_mtime': 0,
            'st_nlink': 0,
            'st_size':  st_size,
            'st_uid':   0
        }

        return res

    def readdir(self, path, fh):
        obj = self.getobj(path)
        # Can't list files
        if type(obj) is dict:
            raise FuseOSError(errno.EBADF)
        dirents = ['.', '..']
        # Root lists valid units
        if path == '/':
            dirents.extend('dapp@%s.service.d' % dapp for dapp in self.dapps)
        # Else only one file
        else:
            dirents.append('dapp.conf')

        # Sufficiently recent python required
        yield from dirents

    # TODO: statfs
    # TODO: what if path doesn't mach definition?
    def open(self, path, flags):
        obj = self.getobj(path)
        # if type(obj) is not str: TODO then what???
        # TODO: not multithreading friendly
        self.lastfd += 1
        self.filecache[self.lastfd] = self.getconfig(obj)
        return self.lastfd

    # TODO: here and below invalid descriptor error
    def release(self, path, fh):
        del self.filecache[self.lastfd]

    def read(self, path, length, offset, fh):
        doc = self.filecache[fh]
        end = offset + min(len(doc) - offset, length)
        return doc[offset:end].encode('ascii')

    # Silently nod when asked to sync instead of ENOSYS error
    def fsync(self, *args, **kwargs):
        pass

# TODO: re-work in order to make systemd friendly

# Standalone operation
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: ./pydapphubfuse.py /path/to/json /mount/point")
    # TODO: study if we need nothreads here
    else:
        FUSE(PydAppHubFuse(sys.argv[2]), sys.argv[1], nothreads=True, foreground=True)