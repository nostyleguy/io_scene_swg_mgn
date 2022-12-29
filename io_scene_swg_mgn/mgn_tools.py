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
try:
    import iff_tools
except ImportError:
    from . import iff_tools
import builtins
import struct
import io

class Generic_String_List_Chunk(iff_tools.DataChunk):
    def __init__(self, type_ID):
        iff_tools.DataChunk.__init__(self, type_ID)
##        super(Generic_String_List_Chunk, self).__init__(type_ID)
        self._data = []
    def __len__(self):
        return len(self._data)
    def __getitem__(self, key):
        return self._data[key]
    def __setitem__(self, key, value):
        self._data = self._data[:key] + value + self._data[key+1:]
    def __delitem__(self, key):
        del self._data[key]
    def __contains__(self, value):
        return value in self._data
    def index(self, value):
        return self._data.index(value)
    def append(self, value):
        self._data.append(value)
    def load(self):
        self._stream.seek(0)
        self._data = [i.decode('ASCII') for i in self._stream.read().strip(b'\x00').split(b'\x00')]
        print("Generic String List Chunk [",self._name,'] Len: ', str(len(self._data)), ' Data: ', ':'.join(self._data))

    def save(self):
        self._stream.seek(0)
        raw_data = b''.join([bytes(i, 'ASCII') + b'\x00' for i in self._data])
        new_stream = io.BytesIO(raw_data)
        self._stream.close()
        self._stream = new_stream

class Generic_Vector_List_Chunk(iff_tools.DataChunk):
    def __init__(self, type_ID, magnitude=3, has_count = False):
        iff_tools.DataChunk.__init__(self, type_ID)
##        super(SKMG_Chunk, self).__init__(type_ID)
        self._magnitude = magnitude
        self._has_count = has_count
        self._name = type_ID
        self._data = []
    def __len__(self):
        return len(self._data)
    def __getitem__(self, key):
        if isinstance(key, (list, tuple, set)):
            return [self._data[i] for i in key]
        elif isinstance(key, (int, slice)):
            return self._data[key]
        else:
            errstr = self.name
            errstr += ' and other data mappings only accept integers or slices as keys'
            errstr += ', or optionally a list, tuple, or set of mapping indices'
            raise TypeError(errstr)
    def __setitem__(self, key, value):
        if isinstance(key, (list, tuple, set)):
            for i in key:
                self[i] = value[i]
        elif isinstance(key, (int, slice)):
            self._data = self._data[:key] + [value] + self._data[key+1:]
        else:
            errstr = self.name
            errstr += ' and other data mapping only accept integers or slices as keys'
            errstr += ', or optionally a list, tuple, or set of mapping indices'
    def __delitem__(self, key):
        del self._data[key]
    def __contains__(self, value):
        return value in self._data
    def append(self, value):
        self._data.append(value)
    def index(self, value):
        return self._data.index(value)
    def load(self, count=-1):
        if not isinstance(count, int):
            raise TypeError('Count must be integer or NoneType')
        size = self.calc_size()
        if self._has_count:
            size -= 4
        if self._name == 'DOT3':
            size -= 8
        self._stream.seek(0)
        
        estimated_count = size // (4 * self._magnitude)
        if count == -1 and self._has_count == False:
            print('No count specified, estimating value count from data size')
            count = estimated_count
        elif count != -1 and self._has_count == True:
            print('Count given on object with integrated count. Using integrated count')
            given_count = count
            count = int.from_bytes(self._stream.read(4), 'little')
            print('Requested', given_count, 'values. Integrated count lists', count, 'values')
        elif count == -1 and self._has_count:
            count = int.from_bytes(self._stream.read(4), 'little')
        else:
            pass
        unpack_string = '<' + str(count * self._magnitude) + 'f'
        data_raw = struct.unpack(unpack_string,
                                 self._stream.read(4*count*self._magnitude))
        self._data = list([data_raw[i:i+self._magnitude] for i in range(0, count*self._magnitude, self._magnitude)])
    def save(self):
        new_stream = io.BytesIO()
        if self._has_count:
            new_stream.write(struct.pack('<I', len(self._data)))
        pack_string = '<' + str(len(self._data) * self._magnitude) + 'f'
        new_stream.write(struct.pack(pack_string,
                                     *sum([list(a) for a in self._data], [])))
        self._stream.close()
        self._stream = new_stream

# I had to make substantial changes to this class. I've tried to document them as I recall.
# I added the _type & _ map to pass the proper variables to the save definition, for the 
# BLT chunks. This section is entirely for BLT chunks.
class Mapped_Vector_List_Chunk(iff_tools.DataChunk):
    def __init__(self, type_ID, magnitude=3, has_count = False):
        iff_tools.DataChunk.__init__(self, type_ID)
##        super(SKMG_Chunk, self).__init__(type_ID)
        self._magnitude = magnitude
        self._has_count = has_count
        self._type_id = type_ID
        self._data = []
        self._map = []
    def __len__(self):
        return len(self._data)
    def __getitem__(self, key):
        if isinstance(key, (list, tuple, set)):
            map_list = []
            for i in key:
                if i in self._map:
                    map_list.append(self._data[self._map.index(i)])
                else:
                    map_list.append([0 for i in range(self._magnitude)])
            return map_list
        elif isinstance(key, (int, slice)):
            return self._data[key]
        else:
            errstr = self.name
            errstr += ' and other data mappings only accept integers or slices as keys'
            errstr += ', or optionally a list, tuple, or set of mapping indices'
            raise TypeError(errstr)
    def __setitem__(self, key, value):
        self._data[key] = value
    def __delitem__(self, key):
        del self._data[key]
    def __contains__(self, value):
        return value in self._data
    def append(self, key, value):
        self._map.append(key)
        self._data.append(value)
    def load(self, count=-1):
        if not isinstance(count, int):
            raise TypeError('Count must be integer or NoneType')
        size = self.calc_size()
        if self._has_count:
            size -= 4
        if self._type_id == 'POSN':
            size -= 8
        self._stream.seek(0)

        estimated_count = size // (4 * (self._magnitude+1))
        if count == -1 and self._has_count == False:
            print('No count specified, estimating value count from data size')
            count = estimated_count
        elif count != -1 and self._has_count == True:
            print('Count given on object with integrated count. Using integrated count')
            given_count = count
            count = int.from_bytes(self._stream.read(4), 'little')
            print('Requested', given_count, 'values. Integrated count lists', count, 'values')
        elif count == -1 and self._has_count:
            count = int.from_bytes(self._stream.read(4), 'little')
        else:
            pass
        if self._type_id == 'POSN':
            estimated_count = size // (4 * (self._magnitude+1))
            unpack_string = '<' + ('Ifff')*estimated_count
        data_raw = struct.unpack(unpack_string,
                                 self._stream.read(4*count*(self._magnitude+1)))
        if self._type_id == 'POSN':
            self._data = [data_raw[i:i+self._magnitude+1] for i in range(0, count*(self._magnitude+1), (self._magnitude+1))]
    def save(self):
# the pack string provides a list of identifiers explaining the data to be loaded.  
# you have to have an identifer for each byte of data, i for int, f for float etc.
# you also have to untuple the data in to a single list of values. again, every value
# in the list has to have an identifer in the pack string as to it's type.
        raw_data = []
        new_stream = io.BytesIO()
        cnt = 0
        for dt in self._map:
            a = [i for i in self._data[cnt]]
            a.insert(0, self._map[cnt])
            raw_data.append(a)
            cnt += 1
# here I had to add an if to set a different magnitude for DOT3's as they have 4 per tuple.
        if self._type_id == 'DOT3':
            self._magnitude += 1
        pack_string = '<' + len(self._map) * ('I' + (self._magnitude * 'f'))
        new_stream.write(struct.pack(pack_string, *sum([tuple(i) for i in raw_data],())))
        self._stream.close()
        self._stream = new_stream

class Generic_Integer_List_Chunk(iff_tools.DataChunk):
    def __init__(self, type_ID, has_count = False):
        iff_tools.DataChunk.__init__(self, type_ID)
##        super(SKMG_Chunk, self).__init__(type_ID)
        self._has_count = has_count
        self._name = type_ID
        self._data = []
    def __len__(self):
        return len(self._data)
    def __getitem__(self, key):
        if isinstance(key, (list, tuple, set)):
            return [self._data[i] for i in key]
        elif isinstance(key, (int, slice)):
            return self._data[key]
        else:
            errstr = self.name
            errstr += ' and other data mappings only accept integers or slices as keys'
            errstr += ', or optionally a list, tuple, or set of mapping indices'
            raise TypeError(errstr)
    def __setitem__(self, key, value):
        if isinstance(key, (list, tuple, set)):
            for i in range(len(key)):
                self[key[i]] = value[i]
        elif isinstance(key, (int, slice)):
            self._data = self._data[:key] + [value] + self._data[key+1:]
        else:
            errstr = self.name
            errstr += ' and other data mapping only accept integers or slices as keys'
            errstr += ', or optionally a list, tuple, or set of mapping indices'
    def __delitem__(self, key):
        del self._data[key]
    def __contains__(self, value):
        return value in self._data
    def append(self, value):
        self._data.append(value)
    def new(self, count):
        self._data = [0 for i in range(count)]
    def load(self, count=-1):
        if not isinstance(count, int):
            raise TypeError('Count must be integer or NoneType')
        size = self.calc_size()
        if self._has_count:
            size -= 4
        if self._name == 'TWHD':
            size -= 8
        self._stream.seek(0)
        
        estimated_count = size // 4
        if count == -1 and self._has_count == False:
            print('No count specified, estimating value count from data size')
            count = estimated_count
        elif count != -1 and self._has_count == True:
            print('Count given on object with integrated count. Using integrated count')
            given_count = count
            count = int.from_bytes(self._stream.read(4), 'little')
            print('Requested', given_count, 'values. Integrated count lists', count, 'values')
        elif count == -1 and self._has_count:
            count = int.from_bytes(self._stream.read(4), 'little')
        else:
            pass

        print(f"{self._name} have: {len(self._data)} but need {4*count}")
        unpack_string = '<' + str(count) + 'I'
        self._data = list(struct.unpack(unpack_string, self._stream.read(4*count)))
    def save(self):
        new_stream = io.BytesIO()
        if self._has_count:
            new_stream.write(struct.pack('<I', len(self._data)))
        pack_string = '<' + str(len(self._data)) + 'I'
        new_stream.write(struct.pack(pack_string,
                                     *self._data))
        self._stream.close()
        self._stream = new_stream

class MGN_File(iff_tools.InterchangeFile):
    def __init__(self):
        iff_tools.InterchangeFile.__init__(self)
    def get_version(self):
        ver_str = self.dir()[1]
        ver_str = ver_str.split('.')[-1].split('_')[0]
        return int(ver_str)
    def add_vertex_weight(self, v_index, b_index, b_weight):
        twhd = self[self.dir()[1] + '.TWHD']
        twdt = self[self.dir()[1] + '.TWDT']
        twhd[v_index] += 1
        w_offset = sum(twhd[:v_index + twhd[v_index]])
        twdt.insert(w_offset, [b_index, b_weight])
    def get_dirlst(self):
        return self.dir()
class SKMG_Chunk(iff_tools.FormChunk):
    def __init__(self):
        iff_tools.FormChunk.__init__(self, 'SKMG')

class Version_Chunk(iff_tools.FormChunk):
    def __init__(self, version):
        iff_tools.FormChunk.__init__(self, str(version).zfill(4))
##        super(Version_Chunk, self).__init__(str(version).zfill(4))

class SKMG_INFO_Chunk(iff_tools.DataChunk):
    _info_fields = ['unk1', 'unk2', 'skeleton_count',
                    'bone_count', 'location_count',
                    'weight_count', 'normal_count',
                    'material_count', 'blend_count',
                    'ozn_count', 'fozc_count',
                    'ozc_count', 'occlusion_layer']
    _struct_string = '<9I3Hh'
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'INFO')
##        super(SKMG_INFO_Chunk, self).__init__('INFO')
        self._data = {}
    def __getitem__(self, key):
        return self._data[key]
    def __setitem__(self, key, value):
        self._data[key] = value
    def load(self):
        self._stream.seek(0)
        raw_data = struct.unpack(self._struct_string,
                                 self._stream.read())
        self._data = dict(zip(self._info_fields, raw_data))
    def save(self):
        raw_data = [self._data[f] for f in self._info_fields]
        self._stream.seek(0)
        self._stream.write(struct.pack(self._struct_string,
                                       *raw_data))
    def new(self):
        self._data = dict(zip(self._info_fields, [0 for i in range(13)]))

class SKTM_Chunk(Generic_String_List_Chunk):
    def __init__(self):
        Generic_String_List_Chunk.__init__(self, 'SKTM')
##        super(SKTM_Chunk, self).__init__('SKTM')

class XFNM_Chunk(Generic_String_List_Chunk):
    ## MGN Method Map Bone to Verts(vert_list, bone_name)
    def __init__(self):
        Generic_String_List_Chunk.__init__(self, 'XFNM')
##        super(XFNM_Chunk, self).__init__('XFNM')

class SKMG_POSN_Chunk(Generic_Vector_List_Chunk):
    def __init__(self):
        Generic_Vector_List_Chunk.__init__(self, 'POSN', 3, False)
##        super(SKMG_POSN_Chunk, self).__init__('POSN', 3, False)

class TWHD_Chunk(Generic_Integer_List_Chunk):
    ## Weight map counts.
    ## MGN Method Map Bone to Verts(vert_list, bone_name)
    def __init__(self):
        Generic_Integer_List_Chunk.__init__(self, 'TWHD', False)
##        super(TWHD_Chunk, self).__init__('TWHD', False)

class TWDT_Chunk(iff_tools.DataChunk):
    ## Weight data. Maps from TWHD
    ## MGN Method Map Bone to Verts(vert_list, bone_name)
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'TWDT')
##        super(TWDT_Chunk, self).__init__('TWDT')
        self._bone_map = []
        self._bone_weights = []
        self._data = []
        self._has_count = False
    def __len__(self):
        return len(self._bone_weights)
    def __getitem__(self, key):
        if isinstance(key, (list, tuple, set)):
            return [self._data[i] for i in key]
        elif isinstance(key, (int, slice)):
            return self._data
        else:
            errstr = self.name
            errstr += ' and other data mappings only accept integers or slices as keys'
            errstr += ', or optionally a list, tuple, or set of mapping indices'
            raise TypeError(errstr)
    def insert(self, key, value):
        bone_id, weight = value
        self._bone_map = self._bone_map[:key] + [bone_id] + self._bone_map[key:]
        self._bone_weights = self._bone_weights[:key] + [weight] + self._bone_weights[key:]
    def append(self, key, value):
        self._data.append(value)
    def load(self, count=-1):
        if not isinstance(count, int):
            raise TypeError('Count must be integer or NoneType')
        size = self.calc_size()
        if self._has_count:
            size -= 4
        size -= 8
        self._stream.seek(0)
        estimated_count = size // 8
        count = estimated_count
        unpack_string = '<' + count*'If'
        raw_data = struct.unpack(unpack_string,
                                 self._stream.read())
        self._data = [[raw_data[i] for i in range(0, count*2, 2)], [raw_data[i] for i in range(1, count*2, 2)]]
    def save(self):
        new_stream = io.BytesIO()
        raw_data = list(zip(self._bone_map, self._bone_weights))
        struct_string = '<' + len(raw_data) * 'If'
        new_stream.write(struct.pack(struct_string,
                                     *sum([tuple(i) for i in raw_data], ())))

        self._stream.close()
        self._stream = new_stream

class SKMG_NORM_Chunk(Generic_Vector_List_Chunk):
    ## Vector
    def __init__(self):
        Generic_Vector_List_Chunk.__init__(self, 'NORM', 3, False)
##        super(SKMG_NORM_Chunk, self).__init__('NORM', 3, False)

class SKMG_DOT3_Chunk(Generic_Vector_List_Chunk):
    ## vector + handedness
    def __init__(self):
        Generic_Vector_List_Chunk.__init__(self, 'DOT3', 4, True)
##        super(SKMG_DOT3_Chunk, self).__init__('DOT3', 4, True)

class SKMG_HPTS_Chunk(iff_tools.FormChunk):
    def __init__(self):
        iff_tools.FormChunk.__init__(self, 'HPTS')

class DYN_Chunk(iff_tools.DataChunk):
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'DYN ')

class STAT_Chunk(iff_tools.DataChunk):
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'STAT')

class BLTS_Chunk(iff_tools.FormChunk):
    ## Container form for all blends
    def __init__(self):
        iff_tools.FormChunk.__init__(self, 'BLTS')
##        super(BLTS_Chunk, self).__init__('BLTS')

class BLT_Chunk(iff_tools.FormChunk):
    ## Blend chunk container form
    def __init__(self):
        iff_tools.FormChunk.__init__(self, 'BLT ')        
##        super(BLT_Chunk, self).__init__('BLT ')

class BLT_INFO_Chunk(iff_tools.DataChunk):
    ## Info counters and name for Blend chunk
    _info_fields = ['position_count', 'normal_count']

    _struct_string = '<2I'
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'INFO')
##        super(SKMG_INFO_Chunk, self).__init__('INFO')
        self._data = {'position_count':0,
                      'normal_count':0,
                      'name':''}
    def __getitem__(self, key):
        return self._data[key]
    def __setitem__(self, key, value):
        self._data[key] = value
    def load(self):
        self._stream.seek(0)
        count_data = struct.unpack('<2I', self._stream.read(8))
        self._data['position_count'] = count_data[0]
        self._data['normal_count'] = count_data[1]
        self._data['name'] = str(self._stream.read().strip(b'\x00'),
                                 'ASCII')
    def save(self):
        raw_data = [self._data[f] for f in self._info_fields]
        self._stream.seek(0)
        self._stream.write(struct.pack(self._struct_string,
                                       *raw_data))
        self._stream.write(bytes(self._data['name'],
                               'ASCII') + (b'\x00'))
    def new(self):
        self._data = dict(zip(self._info_fields, [0 for i in range(2)]))

class BLT_POSN_Chunk(Mapped_Vector_List_Chunk):
    ## POSN Blend Vectors, mapped
    def __init__(self):
        Mapped_Vector_List_Chunk.__init__(self, 'POSN', 3, False)
##        super(BLT_POSN_Chunk, self).__init__('POSN', 3, False)

class BLT_NORM_Chunk(Mapped_Vector_List_Chunk):
    ## NORM Blend Vectors, mapped
    def __init__(self):
        Mapped_Vector_List_Chunk.__init__(self, 'NORM', 3, False)
##        super(BLT_NORM_Chunk, self).__init__('NORM', 3, False)

class BLT_DOT3_Chunk(Mapped_Vector_List_Chunk):
    ## DOT3 Blend Vectors, mapped like the rest, with a count chunk.
    def __init__(self):
        Mapped_Vector_List_Chunk.__init__(self, 'DOT3', 3, True)
##        super(BLT_DOT3_Chunk, self).__init__('DOT3', 3, True)

class BLT_HPTS_Chunk(iff_tools.DataChunk):
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'HPTS')

class OZN_Chunk(Generic_String_List_Chunk):
    ## Zone names
    def __init__(self):
        Generic_String_List_Chunk.__init__(self, 'OZN ')
##        super(OZN_Chunk, self).__init__('OZN ')

class FOZC_Chunk(iff_tools.DataChunk):
    ## Effectively an integer list chunk running on UInt16's with a count field.
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'FOZC')
##        super(FOZC_Chunk, self).__init__('FOZC')
        self._data = []
    def __len__(self):
        return len(self._data)
    def __getitem__(self, key):
        if isinstance(key, (list, tuple, set)):
            return [self._data[i] for i in key]
        elif isinstance(key, (int, slice)):
            return self._data[i]
        else:
            errstr = self.name
            errstr += ' and other data mappings only accept integers or slices as keys'
            errstr += ', or optionally a list, tuple, or set of mapping indices'
            raise TypeError(errstr)
    def __setitem__(self, key, value):
        self._data[key] = value
    def __delitem__(self, key):
        del self._data[key]
    def __contains__(self, value):
        return value in self._data
    def append(self, value):
        self._data.append(value)
    def load(self):
        size = self.calc_size()
        size -= 2
        self._stream.seek(0)
        
        estimated_count = size // 2
        count = int.from_bytes(self._stream.read(2), 'little')
        if count != estimated_count:
            print('Size mismatch in FOZC')
        unpack_string = '<' + str(count) + 'H'
        self._data = struct.unpack(unpack_string,
                                   self._stream.read(2*count))
    def save(self):
        new_stream = io.BytesIO()
        new_stream.write(struct.pack('<H', len(self._data)))
        pack_string = '<' + str(len(self._data)) + 'H'
        new_stream.write(struct.pack(pack_string,
                        *self._data))
        self._stream.close()
        self._stream = new_stream

class OZC_Chunk(iff_tools.DataChunk):
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'OZC ')
##        super(OZC_Chunk, self).__init__('OZC ')
        self._data = []
    def append(self, value):
        self._data.append(value)
    def load(self, count):
        self._stream.seek(0)
        unpack_string = '<' + (count*2)*'H'
        raw_data = struct.unpack(unpack_string,
                                 self._stream.read())
        self._data = []
        for i in range(0, count*2, 2):
            self._data.append(raw_data[i] * [raw_data[i+1]])
    def save(self):
        new_stream = io.BytesIO()
        pack_string = '<' + str(len(self._data)) + 'H'
        new_stream.write(struct.pack(pack_string,
                        *self._data))
        self._stream.close()
        self._stream = new_stream

class ZTO_Chunk(iff_tools.DataChunk):
    ## Nearly the same as FOZC, only without integral count
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'ZTO ')
##        super(ZTO_Chunk, self).__init__('ZTO ')
        self._data = []
    def __len__(self):
        return len(self._data)
    def __getitem__(self, key):
        if isinstance(key, (list, tuple, set)):
            return [self._data[i] for i in key]
        elif isinstance(key, (int, slice)):
            return self._data[i]
        else:
            errstr = self.name
            errstr += ' and other data mappings only accept integers or slices as keys'
            errstr += ', or optionally a list, tuple, or set of mapping indices'
            raise TypeError(errstr)
    def __setitem__(self, key, value):
        self._data[key] = value
    def __delitem__(self, key):
        del self._data[key]
    def __contains__(self, value):
        return value in self._data
    def append(self, value):
        self._data.append(value)
    def load(self, count):
        size = self.calc_size()
        self._stream.seek(0)
        estimated_count = size // 2
        count
        if count != estimated_count:
            print('Size mismatch in ZTO')
        unpack_string = '<' + str(count) + 'H'
        self._data = struct.unpack(unpack_string,
                                   self._stream.read(2*count))
    def save(self):
        new_stream = io.BytesIO()
        pack_string = '<' + str(len(self._data)) + 'H'
        new_stream.write(struct.pack(pack_string,
                        *self._data))
        self._stream.close()
        self._stream = new_stream

class PSDT_Chunk(iff_tools.FormChunk):
    def __init__(self):
        iff_tools.FormChunk.__init__(self, 'PSDT')
##        super(PSDT_Chunk, self).__init__('PSDT')
    def get_vertices(self, typestring):
        data = []
        try:
            posn_chunk = self['PIDX_0']
            posn_chunk.load()
        except KeyError:
            raise IOError('PSDT Chunk has no position chunk!')
        vert_count = len(posn_chunk)
        if 'P' in typestring:
            data.append(list(posn_chunk[:]))
        if 'N' in typestring:
            norm_chunk = self['NIDX_0']
            norm_chunk.load(vert_count)
            data.append(list(norm_chunk[:]))
        if 'D' in typestring:
            try:
                dot3_chunk = self['DOT3_0']
                dot3_chunk.load(vert_count)
                data.append(list(dot3_chunk[:]))
            except KeyError:
                pass
        if 'T' in typestring:
            uv_chunk = self['TCSF_0.TCSD_0']
            uv_chunk.load(vert_count)
            data.append(list(uv_chunk[:]))
        return data
    def set_vertices(self, typestring, *args):
        if len(typestring) != len(args):
            errstr = 'set_vertices requires',len(typestring),'arguments'
            raise ValueError(errstr)
        for t in range(len(typestring)):
            if typestring[t] == 'P':
                posn_chunk = self['PIDX_0']
                posn_chunk[list(range(len(args[t])))] = args[t]
            if typestring[t] == 'N':
                norm_chunk = self['NIDX_0']
                norm_chunk[list(range(len(args[t])))] = args[t]
            if typestring[t] == 'D':
                dot3_chunk = self['DOT3_0']
                dot3_chunk[list(range(len(args[t])))] = args[t]
            if typestring[t] == 'T':
                uv_chunk = self['TCSF_0.TCSD_0']
                uv_chunk[list(range(len(args[t])))] = args[t]
    def save(self):
        for child in self._children.keys():
            self._children[child].save()

class NAME_Chunk(iff_tools.DataChunk):
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'NAME')
##        super(NAME_Chunk, self).__init__('NAME')
    def __str__(self):
        return self._data
    def set(self, name):
        if isinstance(name, str):
            self._data = name
    def get(self):
        return str(self)
    def load(self):
        self._stream.seek(0)
        self._data = str(self._stream.read()[:-1],
                         'ASCII')
    def save(self):
        new_stream = io.BytesIO()
        self._stream.close()
        new_stream.write(bytes(self._data, 'ASCII') + b'\x00')
        self._stream = new_stream

class PIDX_Chunk(Generic_Integer_List_Chunk):
    def __init__(self):
        Generic_Integer_List_Chunk.__init__(self, 'PIDX', True)
##        super(PIDX_Chunk, self).__init__('PIDX', True)

class NIDX_Chunk(Generic_Integer_List_Chunk):
    def __init__(self):
        Generic_Integer_List_Chunk.__init__(self, 'NIDX', False)
##        super(NIDX_Chunk, self).__init__('NIDX', False)
        
class PSDT_DOT3_Chunk(Generic_Integer_List_Chunk):
    def __init__(self):
        Generic_Integer_List_Chunk.__init__(self, 'DOT3', False)

class TXCI_Chunk(iff_tools.DataChunk):
    ## Info counters and name for Blend chunk
    _loaded = False
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'TXCI')
##        super(TXCI_Chunk, self).__init__('TXCI')
        self._data = {'Field_1':0,
                      'Field_2':0}
    def __getitem__(self, key):
        return self._data[key]
    def __setitem__(self, key, value):
        self._data[key] = value
    def load(self):
        self._stream.seek(0)
        count_data = struct.unpack('<2I', self._stream.read(8))
        self._data['Field_1'] = count_data[0]
        self._data['Field_2'] = count_data[1]
        self._loaded = True
    def save(self):
        if self._loaded:
            new_stream = io.BytesIO()
            new_stream.write(struct.pack('<2I',
                                         self._data['Field_1'],
                                         self._data['Field_2']))
            self._stream.close()
            del self._stream
            self._stream = new_stream
    def new(self):
        self._loaded = True
        self._data['Field_1'] = 1
        self._data['Field_2'] = 2

class TCSF_Chunk(iff_tools.FormChunk):
    def __init__(self):
        iff_tools.FormChunk.__init__(self, 'TCSF')
##        super(TCSF_Chunk, self).__init__('TCSF')
    def save(self):
        self['TCSD_0'].save()

class TCSD_Chunk(Generic_Vector_List_Chunk):
    def __init__(self):
        Generic_Vector_List_Chunk.__init__(self, 'TCSD', 2, False)
##        super(TCSD_Chunk, self).__init__('TCSD')

class PRIM_Chunk(iff_tools.FormChunk):
    def __init__(self):
        iff_tools.FormChunk.__init__(self, 'PRIM')
##        super(PRIM_Chunk, self).__init__('PRIM')
    def save(self):
        for child in self._children.keys():
            self._children[child].save()

class PRIM_INFO_Chunk(iff_tools.DataChunk):
    _loaded = False
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'INFO')
##        super(PRIM_INFO_Chunk, self).__init__('INFO')
    def load(self):
        self._stream.seek(0)
        self._data = int.from_bytes(self._stream.read(4),
                                    'little')
        self._loaded = True
    def save(self):
        if self._loaded:
            self._stream.seek(0)
            self._stream.write(struct.pack('<I',
                                           self._data))
    def get(self):
        return self._data
    def set(self, value):
        self._data = value
        if not self._loaded:
            self._loaded = True

class OITL_Chunk(iff_tools.DataChunk):
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'OITL')
##        super(OITL_Chunk, self).__init__('OITL')
    def __len__(self):
        return len(self._map)
    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return list(zip(self._map, self._data))[key]
        elif isinstance(key, (list, tuple, set)):
            data = list(zip(self._map, self._data))[key]
            return [data[i] for i in key]
    def __setitem__(self, key, value):
        if isinstance(key, int):
            if not isinstance(value, (list, tuple)) or not len(value) == 2:
                raise TypeError('Index assignment Value must be a list or tuple containing one int and one list/tuple of three ints')
            a, b = value[:]
            if not isinstance(a, int):
                raise TypeError('Index assignment Value first field must be type int')
            elif not isinstance(b, (list, tuple)) or not len(b) == 3:
                raise TypeError('Index assignment Value second field must be a list of three ints')
            for i in b:
                if not isinstance(i, int):
                    raise TypeError('Index assignment Value second field must be a list of three ints')
            self._map = self._map[:key] + [a] + self._map[key+1:]
            self._data = self._data[:key] + [b] + self._data[key+1:]
        elif isinstance(key, (list, tuple)):
            if not isinstance(value, (list, tuple)) or not len(value) == len(key):
                raise TypeError('Multiple Mapping assignment Value must be a list or tuple of int/tri-list pairs the same length as the mapping list')
            for i in range(len(key)):
                self[key[i]] = value[i]
        else:
            errstr = self.name
            errstr += ' only accepts integers or slices as keys'
            errstr += ', or optionally a list or tuple of mapping indices'
            raise TypeError(errstr)

    def append(self, value):
        if not isinstance(value, (tuple, list)) or not len(value) == 4:
            raise TypeError('ITL Face values must be list or tuple of three integers')
        for i in value:
            if not isinstance(i, int):
                raise TypeError('ITL Face values must be list or tuple of three integers')
        a, b, c, d = value
        self._data.append((a, b, c, d))
    def new(self):
        self._data = []

    def load(self):
        self._stream.seek(0)
        count = int.from_bytes(self._stream.read(4), 'little')
        unpack_string = '<' + count*'H3I'
        raw_data = struct.unpack(unpack_string,
                                 self._stream.read())
        self._map = [raw_data[i] for i in range(0, count*4, 4)]
        self._data = [raw_data[i:i+3] for i in range(1, count*4, 4)]
    def save(self):
        count = len(self._data)
        raw_data = []
        for i in range(count):
            raw_data += self._data[i]
        pack_string = '<' + count*'H3I'
        new_stream = io.BytesIO()
        new_stream.write(struct.pack('<I', count))
        new_stream.write(struct.pack(pack_string,
                                     *raw_data))
        self._stream.close()
        del self._stream
        self._stream = new_stream

class ITL_Chunk(iff_tools.DataChunk):
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'ITL ')
##        super(OITL_Chunk, self).__init__('OITL')
    def __len__(self):
        return len(self._data)
    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self._data[key]
        elif isinstance(key, (list, tuple, set)):
            return [self._data[i] for i in key]
    def __setitem__(self, key, value):
        if isinstance(key, int):
            if not isinstance(value, (list, tuple)) or not len(value) == 2:
                raise TypeError('Index assignment Value must be a list or tuple containing one int and one list/tuple of three ints')
            a, b = value[:]
            if not isinstance(a, int):
                raise TypeError('Index assignment Value first field must be type int')
            elif not isinstance(b, (list, tuple)) or not len(b) == 3:
                raise TypeError('Index assignment Value second field must be a list of three ints')
            for i in b:
                if not isinstance(i, int):
                    raise TypeError('Index assignment Value second field must be a list of three ints')
            self._map = self._map[:key] + [a] + self._map[key+1:]
            self._data = self._data[:key] + [b] + self._data[key+1:]
        elif isinstance(key, (list, tuple)):
            if not isinstance(value, (list, tuple)) or not len(value) == len(key):
                raise TypeError('Multiple Mapping assignment Value must be a list or tuple of int/tri-list pairs the same length as the mapping list')
            for i in range(len(key)):
                self[key[i]] = value[i]
        else:
            errstr = self.name
            errstr += ' only accepts integers or slices as keys'
            errstr += ', or optionally a list or tuple of mapping indices'
            raise TypeError(errstr)

    def append(self, value):
        if not isinstance(value, (tuple, list)) or not len(value) == 3:
            raise TypeError('ITL Face values must be list or tuple of three integers')
        for i in value:
            if not isinstance(i, int):
                raise TypeError('ITL Face values must be list or tuple of three integers')
        a, b, c = value
        self._data.append((a, b, c))
                
    def load(self):
        self._stream.seek(0)
        count = int.from_bytes(self._stream.read(4), 'little')
        unpack_string = '<' + str(count*3) + 'I'
        raw_data = struct.unpack(unpack_string,
                                 self._stream.read())
        self._data = [raw_data[i:i+3] for i in range(0, count*3, 3)]
    def save(self):
##        print(self._data)
        count = len(self._data)
        raw_data = sum([tuple(i) for i in self._data], ())
##        print(count, raw_data)
        pack_string = '<' + str(count*3) + 'I'
        new_stream = io.BytesIO()
        new_stream.write(struct.pack('<I', count))
        new_stream.write(struct.pack(pack_string,
                                     *raw_data))
        self._stream.close()
        del self._stream
        self._stream = new_stream
    def new(self):
        self._data = []

class TRTS_Chunk(iff_tools.FormChunk):
    def __init__(self):
        iff_tools.FormChunk.__init__(self, 'TRTS')

class TRTS_INFO_Chunk(iff_tools.DataChunk):
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'INFO')

class TRT_Chunk(iff_tools.DataChunk):
    def __init__(self):
        iff_tools.DataChunk.__init__(self, 'TRT ')

_chunk_map = {'INFO':SKMG_INFO_Chunk,
              'SKTM':SKTM_Chunk,
              'XFNM':XFNM_Chunk,
              'POSN':SKMG_POSN_Chunk,
              'TWHD':TWHD_Chunk,
              'TWDT':TWDT_Chunk,
              'NORM':SKMG_NORM_Chunk,
              'DOT3':SKMG_DOT3_Chunk,
              'HPTS':SKMG_HPTS_Chunk,
              'HPTS.STAT':STAT_Chunk,
              'HPTS.DYN ':DYN_Chunk,
              'BLTS':BLTS_Chunk,
              'BLTS.BLT ':BLT_Chunk,
              'BLT .INFO':BLT_INFO_Chunk,
              'BLT .POSN':BLT_POSN_Chunk,
              'BLT .NORM':BLT_NORM_Chunk,
              'BLT .DOT3':BLT_DOT3_Chunk,
              'BLT .HPTS':BLT_HPTS_Chunk,
              'OZN ':OZN_Chunk,
              'FOZC':FOZC_Chunk,
              'OZC ':OZC_Chunk,
              'ZTO ':ZTO_Chunk,
              'PSDT':PSDT_Chunk,
              'PSDT.NAME':NAME_Chunk,
              'PSDT.PIDX':PIDX_Chunk,
              'PSDT.NIDX':NIDX_Chunk,
              'PSDT.DOT3':PSDT_DOT3_Chunk,
              'PSDT.TXCI':TXCI_Chunk,
              'PSDT.TCSF':TCSF_Chunk,
              'TCSF.TCSD':TCSD_Chunk,
              'PSDT.PRIM':PRIM_Chunk,
              'PRIM.INFO':PRIM_INFO_Chunk,
              'PRIM.OITL':OITL_Chunk,
              'PRIM.ITL ':ITL_Chunk,
              'TRTS':TRTS_Chunk,
              'TRTS.INFO':TRTS_INFO_Chunk,
              'TRTS.TRT ':TRT_Chunk}

def _strip_path(path):
    components = path.split('.')
    components = [i.split('_')[0] for i in components]
    components = components[2:][-2:]
    target = components.pop(-1)
    new_path = ''.join([i+'.' for i in components]) + target
    return new_path
    
def open(filepath, mode='rb'):
    ## open source stream and get size
    print("filepath:", filepath)
    source_stream = builtins.open(filepath, mode)
    source_stream.seek(0, 2)
    file_size = source_stream.tell()
    source_stream.seek(0)

    ## get blank iff
    mgn_iff = MGN_File()

    nest_level = [file_size]
    path_nodes = []
    dir_list = []

    ## make root node
    root_node_name = str(source_stream.read(4), 'ASCII')
    root_node_size = int.from_bytes(source_stream.read(4), 'big')
    if not root_node_name == 'FORM':
        raise IOError('Invalid MGN File; Root node not FORM type! Are you sure you loaded a .mgn?')
    root_node_name = str(source_stream.read(4), 'ASCII')
    if not root_node_name == 'SKMG':
        raise IOError('Invalid MGN file; Root node not SKMG! Are you sure you loaded a .mgn?')
    else:
        root_node = SKMG_Chunk()
        mgn_iff[root_node_name] = root_node
        nest_level.append(root_node_size)
        path_nodes.append(root_node_name + '_0')

    ## make version node
    version_node_name = str(source_stream.read(4), 'ASCII')
    version_node_size = int.from_bytes(source_stream.read(4), 'big')
    if not version_node_name == 'FORM':
        raise IOError('Invalid MGN File; Version node not FORM type! MGN file may be corrupt!')
    version_node_name = str(source_stream.read(4), 'ASCII')
    try:
        version = int(version_node_name)
    except ValueError:
        raise IOError('Invalid MGN File; Version node not ASCII number! MGN file may be corrupt!')
    version_node = Version_Chunk(version)
    nest_level.append(version_node_size)
    path_nodes.append(version_node_name + '_0')
    version_path = root_node_name + '_0.' + str(version).zfill(4) + '_0'
    mgn_iff[version_path] = version_node

    ## assignment loop
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

        ## Get path to new chunk
        path = ''.join([node + '.' for node in path_nodes]) + name + '_0'
        instance = 0
        while path in dir_list:
            instance += 1
            path = ''.join([node + '.' for node in path_nodes]) + name + '_' + str(instance)

        ## get bypath
        bypath = _strip_path(path)
        new_chunk = _chunk_map[bypath]()

        ## copy stream if nescessary:
        if isinstance(new_chunk, iff_tools.DataChunk):
            new_chunk.write(source_stream.read(size))

        ## Add path to master list
        dir_list.append(path)

        ## add chunk to iff
        print(path, new_chunk.name)
        mgn_iff[path] = new_chunk

        ## Add offset to end of chunk to nest list
        nest_level.append(offset + size + 8)

        ## Add pathname to path list
        path_nodes.append(name + '_' + str(instance))
    return mgn_iff
