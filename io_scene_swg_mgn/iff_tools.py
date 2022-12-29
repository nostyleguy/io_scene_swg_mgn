# ##############################################################################
# This file is part of the Blender MGN Plugin.
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this plugin.  If not, see <http://www.gnu.org/licenses/>.
# Credits:
# original copyright 2011 Star^2 Design
# Sunrunner_Charina for creating the original blender plugin. (I think anyway)
# Duffstone for updating code to new Blender API, and added fuctions.
# Rabiator for testing and understanding the MGN format and functions.
# ##############################################################################
import struct, io, builtins, os, bpy

class InterchangeFile:
    '''
    Class wrapper for Interchange files
    '''
    def __init__(self):
        self._root = None
    def __getitem__(self, index):
        if self._root == None:
            raise AttributeError('InterchangeFile is empty, and contains no chunks')
        if not isinstance(index, (str, bytes)):
            raise TypeError('InterchangeFile only accepts string or bytes paths as keys')
        elif isinstance(index, bytes):
            index = str(index, 'ASCII')
            
        item_path = index.split('.')
        name, number = item_path.pop(0).split('_')
        if name == self._root.name:
            target = self._root
        else:
            raise KeyError(index + ' not found in InterchangeFile')
        while len(item_path) > 0:
            target = target[item_path.pop(0)]
        return target
    
    def __setitem__(self, index, value):
        if not isinstance(index, (str, bytes)):
            raise TypeError('InterchangeFile only accepts string or bytes paths as keys')
        elif isinstance(index, bytes):
            index = str(index, 'ASCII')

        if not isinstance(value, (FormChunk, DataChunk)):
            raise TypeError('Interchange nodes must be FormChunk or DataChunk')

        item_path = index.split('.')

        if len(item_path) == 1:
            try:
                self.add_root(value, force=True)
            except ValueError:
                raise AttributeError('Root chunk already set!')
            except TypeError:
                raise AttributeError('Root must be set to FormChunk type!')

        else:
            value_path = item_path.pop(-1)
            if value.name != value_path.split('_')[0]:
                raise ValueError("Names don't match!")

            target = self[item_path.pop(0)]
            while len(item_path) > 0:
                target = target[item_path.pop(0)]

            target[value_path] = value
                

    def dir(self):
        return self._root.dir()
    def add_root(self, root_chunk, force=False):
        if self._root != None and force==False:
            raise ValueError('Root chunk already set. If you want to overrite, use add_root(chunk, force=True)')
        elif isinstance(root_chunk, FormChunk):
            self._root = root_chunk
        else:
            raise TypeError('Root chunk must be of type FormChunk!')
    def save(self, filepath, overwrite):
        if overwrite:
            outfile = builtins.open(filepath, 'wb')
            self._root.save_to(outfile)
            outfile.close()
        else:
            try:
                outfile = builtins.open(filepath, 'xb')
                self._root.save_to(outfile)
                outfile.close()
            except FileExistsError:
                print("File Already Exists, Not saving")
                bpy.ops.object.dialog_operator('INVOKE_DEFAULT')

class DialogOperator(bpy.types.Operator):
    bl_idname = "object.dialog_operator"
    bl_label = "File already exists, No overwrite performed."

    def execute(self, context):
        message = "File Not Saved"
        self.report({'INFO'}, message)
        return {'FINISHED'}
        
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
        
bpy.utils.register_class(DialogOperator)
    
    
class FormChunk:
    def __init__(self, type_ID):
        self._parent = None
        self._name = type_ID
        self._children = {}
        self._child_order = []
    def calc_size(self, only_data = False):
        size = 4 ## Form chunk. Name ID part of data.
        for child in self._child_order:
            size += self._children[child].calc_size()
        if not only_data:
            size += 8
        return size
    def __getattr__(self, name):
        if name == 'name':
            return self._name
        else:
            errstr = "'FormChunk' object has no attribute '" + name + "'"
            raise AttributeError(errstr)
    def __getitem__(self, index):
        if not isinstance(index, (str, bytes)):
            raise TypeError('FormChunk only accepts string or bytes paths as keys')
        elif isinstance(index, bytes):
            index = str(index, 'ASCII')

        item_path = index.split('.')
        target_path = item_path.pop(0)
        if target_path in self._children.keys():
            target = self._children[target_path]
        else:
            raise KeyError(index + ' not found in FormChunk')
        while len(item_path) > 0:
            target = target[item_path.pop(0)]
        return target
    def __setitem__(self, index, value):
        if not isinstance(index, (str, bytes)):
            raise TypeError('FormChunk only accepts string or bytes paths as keys')
        elif isinstance(index, bytes):
            index = str(index, 'ASCII')

        if not isinstance(value, (FormChunk, DataChunk)):
            raise TypeError('FormChunk Children nodes must be FormChunk or DataChunk')

        item_path = index.split('.')
        if len(item_path) == 1:
            try:
                self._children[item_path[0]] == value
            except KeyError:
                self.add_chunk(value)

        else:
            value_path = item_path.pop(-1)
            if value.name != value_path.split('_')[0]:
                raise ValueError("Names don't match!")

            target = self[item_path.pop(0)]
            while len(item_path) > 0:
                target = target[item_path.pop(0)]

            target[value_path] = value
    def __delitem__(self, index):
        if not isinstance(index, (str, bytes)):
            raise TypeError('FormChunk only accepts string or bytes paths as keys')
        elif isinstance(index, bytes):
            index = str(index, 'ASCII')

        item_path = index.split('.')
        if len(item_path) == 1:
            try:
                del self._children[item_path[0]]
                self._child_order.remove(item_path[0])
            except KeyError:
                raise KeyError(index + ' not found in chunk')

        else:
            target = item_path.pop(0)
            path = ''.join([i + '.' for i in item_path])[:-1]
            del self._children[target][path]

    def dir(self):
        directory = [self._name]
        for child in self._child_order:
            if isinstance(self._children[child], FormChunk):
                child_dir = self._children[child].dir()
                root = child_dir[0][:4]
                instance = 0
                i_name = root + '_' + str(instance)
                while self._name + '.' + i_name in directory:
                    instance += 1
                    i_name = root + '_' + str(instance)

                child_dir = [i_name + i[4:] for i in child_dir]
                directory += [self._name + '.' + i for i in child_dir]
            else:
                c_name = self._children[child].name
                instance = 0
                i_name = c_name + '_' + str(instance)
                while self._name + '.' + i_name in directory:
                    instance += 1
                    i_name = root + '_' + str(instance)
                
                directory.append(self._name + '.' + i_name)
        return directory
    def add_chunk(self, value):
        value_name = value.name
        instance = 0
        while value_name + '_' + str(instance) in self._child_order:
            instance += 1
        self._child_order.append(value_name + '_' + str(instance))
        self._children[self._child_order[-1]] = value
    def save_to(self, stream):
        stream.write(b'FORM')
        self_size = self.calc_size(True)
        stream.write(struct.pack('>I', self_size))
        stream.write(bytes(self.name, 'ASCII'))
        for child in self._child_order:
            self._children[child].save_to(stream)
        
class DataChunk:
    def __init__(self, type_ID, source = None):
        self._parent = None
        if source == None:
            self._stream = io.BytesIO()
        elif isinstance(source, io.IOBase):
            self._stream = source
        self._name = type_ID
    def __del__(self):
        self._stream.close()
    def __getattr__(self, name):
        if name == 'name':
            return self._name
        else:
            errstr = "'DataChunk' object has no attribute '" + name + "'"
            raise AttributeError(errstr)
    def __setitem__(self, path, value):
        print(self._name, path, value)
        raise TypeError("'DataChunk' object does not support item assignment")

    ## buffer emulation
    def tell(self):
        return self._stream.tell()
    def seek(self, where, whence=0):
        return self._stream.seek(where, whence)
    def read(self, size=-1):
        return self._stream.read(size)
    def write(self, data):
        self._stream.write(data)
    ## other methods
    def calc_size(self, only_data = False):
        self._stream.seek(0, 2)
        if only_data:
            return self._stream.tell()
        else:
            return self._stream.tell() + 8
    def save_to(self, stream):
        stream.write(bytes(self.name, 'ASCII'))
        stream.write(struct.pack('>I', self.calc_size(True)))
        self._stream.seek(0)
        stream.write(self._stream.read())

def open(file_path, mode = 'rb'):
    ## open source stream and get size
    source_stream = builtins.open(file_path, mode)
    source_stream.seek(0, 2)
    file_size = source_stream.tell()
    source_stream.seek(0)

    ## get blank iff
    new_iff = InterchangeFile()

    dir_list = []

    nest_level = [file_size]
    path_nodes = []

    while source_stream.tell() < file_size: ## as long as file is not done reading
        while source_stream.tell() == nest_level[-1]: ## pop levels for keeping track of tree
            nest_level.pop(-1)
            path_nodes.pop(-1)

        ## Get new chunk
        offset = source_stream.tell()
        name = str(source_stream.read(4), 'ASCII')
        size = int.from_bytes(source_stream.read(4), 'big')
        if name == 'FORM':
            name = str(source_stream.read(4), 'ASCII')
            new_chunk = FormChunk(name)
        else:
            new_chunk = DataChunk(name)
            new_chunk.seek(0)
            new_chunk.write(source_stream.read(size))

        ## Get path to new chunk
        path = ''.join([node + '.' for node in path_nodes]) + name + '_0'
        instance = 0
        while path in dir_list:
            instance += 1
            path = ''.join([node + '.' for node in path_nodes]) + name + '_' + str(instance)

        ## Add path to master list
        dir_list.append(path)

        ## add chunk to iff
        new_iff[path] = new_chunk

        ## Add offset to end of chunk to nest list
        nest_level.append(offset + size + 8)

        ## Add pathname to path list
        path_nodes.append(name + '_' + str(instance))
    return new_iff
