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
# Instructions:  this will import MGN files from the Star Wars Galaxies Game.
# Be aware that the import will mirror the UV map on the Y axis, which will
# allow you to load the textures properly in Blender. (MGN UV's are upside down)
# ##############################################################################
import bpy, mathutils, struct, bmesh
from . import swg_types
from bpy_extras.io_utils import (
        ImportHelper,
        #ExportHelper,
        orientation_helper,
        #path_reference_mode,
        axis_conversion,
        )

from bpy.props import *
from bpy_extras.io_utils import unpack_list, unpack_face_list
from mathutils import Vector
from . import iff_tools, mgn_tools

def import_mgn(context, filepath):

    #import_mgn_old(context, filepath)

    mgn = swg_types.SWGMgn(filepath)
    mgn.load()

    mesh_name = filepath.split('\\')[-1].split('.')[0]
    blend_mesh = bpy.data.meshes.new(mesh_name)

    scene_object = bpy.data.objects.new(mesh_name, blend_mesh)
    context.collection.objects.link(scene_object)

    scene_object.rotation_mode = 'XYZ'
    scene_object.rotation_euler = (1.57, 0, 0)

    faces_by_material=[]

    tris = []
    tris_flat = []
    vertices_flat = []
    uvs_flat = []
    for pid, psdt in enumerate(mgn.psdts):
        mat = bpy.data.materials.new(psdt.stripped_shader_name())
        blend_mesh.materials.append(mat)        
        faces_by_material.append([])

        for prim in psdt.prims:
            for tri in prim:
                p1 = psdt.pidx[tri.p1]
                p2 = psdt.pidx[tri.p2]
                p3 = psdt.pidx[tri.p3]
                tris_flat.append(p1)
                tris_flat.append(p2)
                tris_flat.append(p3)
                tris.append([p1, p2, p3])
                faces_by_material[pid].append((p1, p2, p3))

                for uv_layer_num in range(0, psdt.num_uvs):                    
                    if psdt.uv_dimensions[uv_layer_num] != 2:
                        print(f"*** Warning *** Not handling UV layer {uv_layer_num} with dimension: {psdt.uv_dimensions[uv_layer_num]}")
                        continue 
                    if len(uvs_flat) <= uv_layer_num:
                        uvs_flat.append([])
                    
                    uvs_flat[uv_layer_num].append(psdt.uvs[uv_layer_num][tri.p1])
                    uvs_flat[uv_layer_num].append(psdt.uvs[uv_layer_num][tri.p2])
                    uvs_flat[uv_layer_num].append(psdt.uvs[uv_layer_num][tri.p3])


    #print(f'Mine: ({len(tris_flat)}), {str(tris_flat)}')

    # print(f'Faces by material: {str(len(faces_by_material))}')
    # for i, faces in enumerate(faces_by_material):
    #     print(f'{i}: {str(len(faces))}')
    
    blend_mesh.vertices.add(len(mgn.positions))
    vertices_flat = [vv for v in mgn.positions for vv in v]    

    blend_mesh.vertices.foreach_set("co", vertices_flat) 
    blend_mesh.loops.add(len(tris_flat))
    blend_mesh.loops.foreach_set("vertex_index", tris_flat)
    blend_mesh.polygons.add(len(tris))

    loop_start = []
    loop_total = []
    for i in range(0, len(tris)):
        loop_start.append(3*i)
        loop_total.append(3)
    
    blend_mesh.polygons.foreach_set("loop_start", loop_start)
    blend_mesh.polygons.foreach_set("loop_total", loop_total)

    for flist in blend_mesh.polygons: 
        for id, face_list in enumerate(faces_by_material):
            if flist.vertices[:] in face_list:
                flist.material_index = id

    for i, uvs in enumerate(uvs_flat):
        print(f'UV Layer: {i} -- lengths of UVs ({len(uvs)}) and Tri indecies ({len(tris_flat)})')
        if len(uvs) != len(tris_flat):
            print(f'*** WARNING *** UV Layer: {i} -- Unmatched lengths of UVs ({len(uvs)}) and Tri indecies ({len(tris_flat)}). Skipping!')
            continue
        uvlayer = blend_mesh.uv_layers.new(name=f'UVMap-{str(i)}')
        blend_mesh.uv_layers.active = uvlayer
        for ind, vert in enumerate(tris_flat):
            uv = [uvs[ind][0], 1 - uvs[ind][1]]
            uvlayer.data[ind].uv = uv

    vgs = {}
    for i, bone in enumerate(mgn.bone_names):
        vg = scene_object.vertex_groups.new(name=bone)
        vgs[i] = vg

    for i, vertex_weights in enumerate(mgn.vertex_weights):
        for weight in vertex_weights:
            vgs[weight[0]].add([i], weight[1], 'ADD')
    
    scene_object.shape_key_add(name='Basis')
    for i, blend in enumerate(mgn.blends):
        sk = scene_object.shape_key_add(name=blend.name)
        for vert in blend.positions:
            id = vert[0]
            delta = Vector(vert[1])
            sk.data[id].co = scene_object.data.vertices[id].co + delta


    print("Validate Mesh data")
    blend_mesh.validate()
    blend_mesh.update(calc_edges=True) 
    blend_mesh.calc_normals()
    
    for i, skel in enumerate(mgn.skeletons):
        scene_object[f'SKTM_{i}'] = skel

    for zone in mgn.occlusions:
        scene_object[zone] = 1


def import_mgn_old(context, filepath):   
    mgn_file = mgn_tools.open(filepath)

# Get mgn version
    print("Get MGN Version")
    version = mgn_file.get_version()
    version_chunk = mgn_file['SKMG_0.' + str(version).zfill(4) + '_0']

# Get full Directory list for MGN
    print("Get Directory List")
    dirlist = mgn_file.get_dirlst()

# get MGN info
    print("Get INFO Chunk")
    info_chunk = version_chunk['INFO_0']
    info_chunk.load()

# Get Skeleton file
    print("get Skeleton Chunk")
    sktm_chunk = version_chunk['SKTM_0']
    sktm_chunk.load()

# get OZN chunk
    print("Get OZN Chunk")
    ozn =[]
    try:
        ozn_chunk = version_chunk['OZN _0']
        ozn_chunk.load()
        ozntmp = list(ozn_chunk)
        for xs in ozntmp:
            xstr = xs
            #xstr = xstr[2:-1]
            ozn.append(xstr)
        ozntmp =[]
    except KeyError:
        pass
        
# get material count
    print("Get Material INFO chunk")
    material_count = info_chunk['material_count']
    blend_count = info_chunk['blend_count']

    posn = []
    norm = []
    uvs = []
    faces = []
    face_materials = []
    mat_face_ord = []
    mat_face_idx = {}

# Load vert data
    print("Get PSDT data(PIDX, NIDX, UV, OITL, ITL, and make faces")
    for material in range(material_count):
        v_count = len(posn)
        mat_chunk = version_chunk['PSDT_' + str(material)]
        mat_chunk['NAME_0'].load()
        material = mat_chunk['NAME_0'].get()

        pidx, nidx, uv = mat_chunk.get_vertices('PNT')
        posn += pidx
        norm += nidx
        uvs += uv

        try:
            face_chunk = mat_chunk['PRIM_0.OITL_0']
            face_chunk.load()
            new_zones, new_faces = zip(*face_chunk[:])
            faces += [[i+v_count for i in f] for f in new_faces]
            face_materials += [material for i in new_faces]
        except KeyError:
            face_chunk = mat_chunk['PRIM_0.ITL _0']
            face_chunk.load()
            new_faces = face_chunk[:]
            faces += [[i+v_count for i in f] for f in new_faces]
            face_materials += [material for i in new_faces]

        ufacemat = material.split('/')[1].split('.')[0]
        mat_face_ord.append(ufacemat)
        mat_face_idx[ufacemat] = [[i+v_count for i in f] for f in new_faces]

# Flip UV?
    print("Flipping UV map on Y axis")
    x3=[]
    for x in uvs:
        x2 = (x[0],1-x[1])
        x3.append(x2)
    uvs = x3
    del x3

# Convert UV's to per-face
    print("Convert UV's to per-face")
    pf_uvs = [[uvs[i] for i in f] for f in faces]

# Start pulling XFNM data
    print("Get XFNM Data")
    xfnm = []
    xfnm_chunk = version_chunk['XFNM_0']
    xfnm_chunk.load()
    vgn = list(xfnm_chunk)
    for xs in vgn:
        xstr = xs
        #xstr = xstr[2:-1]
        xfnm.append(xstr)
        
# Start building positions.
    print("Get POSN Data")
    posn_chunk = version_chunk['POSN_0']
    posn_chunk.load()
    positions = posn_chunk[posn]
    origposn = posn_chunk
    print(f'POSN. len(posn_chunk._data): {len(posn_chunk._data)}, len(positions): {len(positions)}, len(posn): {len(posn)}')
    print(f'posn: {str(posn)}')
    print(f'positions: {str(positions)}')
    
# Start building TWDT chunk.
    print("Get TWDT Data")
    twdt_chunk = version_chunk['TWDT_0']
    twdt_chunk.load()
    vgdata = twdt_chunk[0]
    vgidx = vgdata[0]
    vgweight = vgdata[1]

# Start building TWHD chunk.
    print("Get TWHD Data")
    twhd_chunk = version_chunk['TWHD_0']
    twhd_chunk.load()    
    vwdata = twhd_chunk
    vwdata = list(vwdata)

# Start pulling DOT3 chunk.
    print("Get DOT3 Data")
    for a in dirlist:
        if 'DOT3_0' in a:
            dot3_chunk = version_chunk['DOT3_0']
            dot3_chunk.load()    
            d3data = dot3_chunk
            d3data = list(d3data)

# Start Processing BLTS.
    print("Get BLTS Data")
    bltposndata = []
    bltidx = []
    bltchunkidx = []

# get BLT id's for looping through sets.
    for a in dirlist:       
        terms=a.split('.')    
        #print('Dirlist: ', str(a), ' Count: ', len(terms))
        if (len(terms) >= 4) and terms[3].startswith('BLT '):
            if len(terms) == 4:
                bltidx.append(terms[3])
            elif len(terms) == 5:
                bltchunkidx.append(terms[4])
                
    seen = set()
    bltidx = [x for x in bltidx if x not in seen and not seen.add(x)]
    bltchunkidx = [x for x in bltchunkidx if x not in seen and not seen.add(x)]

    if blend_count != 0:
        bltdict = {}
        blts_chunk = version_chunk['BLTS_0']
        for i in bltidx:
            bltgrp_chunk = blts_chunk[i]
            
# get BLT INFO data for each blt section.
            bltinfo_chunk = bltgrp_chunk[bltchunkidx[0]]
            bltinfo_chunk.load()
            bltinfoname = bltinfo_chunk['name']
            bltdict[i+bltchunkidx[0]] = bltinfoname
            
# Get BLT POSN data for each blt section.
            bltposn_chunk = bltgrp_chunk[bltchunkidx[1]]
            bltposn_chunk.load()
            for z in bltposn_chunk:
                bltposndata.append(z)
            bltdict[i+bltchunkidx[1]] = bltposndata
            bltposndata = []

    mesh_name = filepath.split('\\')[-1].split('.')[0]
    blend_mesh = bpy.data.meshes.new(mesh_name)
    blend_mesh.vertices.add(len(positions))
    vertices_flat = [vv for v in positions for vv in v]
    blend_mesh.vertices.foreach_set("co", vertices_flat)

    print(f"blend_mesh positions: {len(positions)} verts: {len(blend_mesh.vertices)}")
    print(f"old : {str(vertices_flat)}")

# add Materials
    print("Add Materials to Blender")
    for material in bpy.data.materials:
        material.user_clear()
        bpy.data.materials.remove(material)
    materials = [bpy.data.materials.new(name) for name in sorted(mat_face_ord)]
    for material in materials:
        blend_mesh.materials.append(material)
    material_map = dict(zip(set(face_materials), range(len(materials))))

# Make Normals
    print("Get Norm Data and load to Blender")
    norm_chunk = version_chunk['NORM_0']
    norm_chunk.load()
    normals = norm_chunk[norm]
    
    # for v in range(len(posn)):
    #     blend_mesh.vertices[v].normal = normals[v]

# Make UVS.
    print("Make UV's")
    # blend_mesh.tessfaces.add(len(faces)) 
    # blend_mesh.tessfaces.foreach_set("vertices_raw", unpack_face_list(faces))
    zipped = sum(faces, [])
    print(f'His : ({len(zipped)}), {str(zipped)}')
    blend_mesh.loops.add(len(zipped))
    blend_mesh.loops.foreach_set("vertex_index", zipped)
    blend_mesh.polygons.add(len(faces))

    loop_start = []
    loop_total = []
    for i in range(0, len(faces)):
        loop_start.append(3*i)
        loop_total.append(3)
    
    blend_mesh.polygons.foreach_set("loop_start", loop_start)
    blend_mesh.polygons.foreach_set("loop_total", loop_total)
    # uv_tex = blend_mesh.tessface_uv_textures.new(name="officialUV")
        
    # for i, face in enumerate(faces):
    #     tface = uv_tex.data[i]
    #     tface.uv1 = pf_uvs[i][0]
    #     tface.uv2 = pf_uvs[i][1]
    #     tface.uv3 = pf_uvs[i][2]
    #me = blend_mesh.data
    uvlayer = blend_mesh.uv_layers.new() # default naem and do_init

    blend_mesh.uv_layers.active = uvlayer

    for face in blend_mesh.polygons:
        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
            #uvlayer.data[loop_idx].uv = pf_uvs[loop_idx] # ie UV coord for each face with vert  me.vertices[vert_idx]
            #print(f'Face: {str(face)}, vert_idx: {vert_idx}, loop_idx: {loop_idx}')
            uvlayer.data[loop_idx].uv = uvs[vert_idx]

# Validate, update and calc normals
    print("Validate Mesh data")
    blend_mesh.validate()
    blend_mesh.update(calc_edges=True) 
    blend_mesh.calc_normals() 

    

    print(f"blend_mesh verts2: {len(blend_mesh.vertices)}")
    

# Write object to scene
    print("Write mesh to scene.")
    scene_object = bpy.data.objects.new(mesh_name, blend_mesh)
    #bpy.context.scene.objects.link(scene_object)
    #bpy.context.scene.update()
    context.collection.objects.link(scene_object)

# Declare some new vars.
    obj = bpy.data.objects[mesh_name]
    #bpy.context.scene.objects.active = obj
    #bobj = bpy.context.active_object
    bobj = scene_object

# change material for each polygon to proper material id
    print("changing material assignments", len(blend_mesh.polygons))
    for flist in blend_mesh.polygons:
        for mx, mat in enumerate(sorted(mat_face_ord)):
            for fac in mat_face_idx[mat]:
                if Vector(fac) == Vector(flist.vertices[:]):
                    flist.select = True
                    flist.material_index = mx
                    flist.select = False

# add custom property for skeleton
    # for cp in sktm_chunk:
    #     if len(cp) >= 4:
    #         obj['SKTM'] = cp[2:-1].split('/')[2].split('.')[0]
    skel = ''
    for cp in sktm_chunk:
        print("Skt: ", cp)
        skel = cp + ':' + skel
    print("Final SKTM : ", skel)
    scene_object['SKTM'] = skel

# Add custom properties for OZN
    for cp in ozn:
        scene_object[cp] = 1

# Removing Duplicate vertices.
    print("Removing duplicate vertices ...")
    # original_area = bpy.context.area.type
    # bpy.ops.object.editmode_toggle()
    # bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.remove_doubles()
    # bpy.context.area.type = original_area
    # bpy.ops.object.editmode_toggle()
    
    t = bmesh.new()
    t.from_mesh(blend_mesh)
    print(f'Result of removing doubles: {bmesh.ops.remove_doubles(t)}')
    t.to_mesh(blend_mesh)
    t.free()

# Create Vertex groups with weight of 1 (doesn't assign vertexes correctly but adds groups)    
# Create dictionary for TWDT vertice indices and values.
    print("Build TWDT dictionary")
    w1 = 0
    k = 0
    twdtx = []
    twdtb = []
    twdtxref = {}
    for i, w in zip(vgidx, vgweight):
        w1 += round(w,4)
        twdtx.append(w)
        twdtb.append(i)
        if w1 >= .99 and w1 <= 1.1:
            twdtxref[k] = twdtx, twdtb
            w1 = 0
            k += 1
            twdtx = []
            twdtb = []

# Createx the vxref for original position index to PIDX vertex index.
    print("build POSN/PIDX cross reference by comparing Vector locations")
    vxref = {}    
    for i, verts in enumerate(bobj.data.vertices):
        for k, vert2 in enumerate(origposn):
            if Vector(list(origposn[k])) == Vector(list(bobj.data.vertices[i].co)):
                vxref[i] = k
                
# Create vertex groups and add weights from twdtxref{} dictionary.
    print("create vertex groups and weights using TWDT data")
    tmpidx = []
    tmpwgt = []
    uvgr = list(set(vgidx))
    for au in uvgr[:]:
        vg = bobj.vertex_groups.new(name=xfnm[au])
        for pos in twdtxref.keys():
            for xi, bone in enumerate(twdtxref[pos][1]):
                if bone == au:
                    if pos in vxref.values():
                        tmpidx.append(list(vxref.keys())[list(vxref.values()).index(pos)])
                        tmpwgt.append(twdtxref[pos][0][xi])
                        vg.add(tmpidx, twdtxref[pos][0][xi],"ADD")
                        tmpidx = []
                        tmpwgt = []

 #lets add shape key blends:
    if blend_count !=0:
        print("Add shape keys")
        #bpy.ops.object.shape_key_add(from_mix=False)
        #shape_key=obj
        bltvertsidx = []
        bltvertsdata = []
        for x in bltdict.keys():
            if 'INFO' in x:
                kn = bltdict[x]
                sk = obj.shape_key_add(name=kn)
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                sl = bm.verts.layers.shape.get(kn)
          
                vertices = [e for e in bm.verts]
                p = x.replace('INFO','POSN')
                bltverts = bltdict[p]
                for h in bltverts:
                    bltvertsidx.append(h[0])
                    bltvertsdata.append(h[1:4])
                for vert in vertices:
                    try:
                        xx = bltvertsidx.index(vxref[vert.index])     
                    except ValueError:
                        xx = 99999
                    if xx != 99999:
                        vert[sl] = vert.co + Vector(bltvertsdata[xx])
                bm.to_mesh(obj.data)
            bltvertsidx =[]
            bltvertsdata=[]

    bobj.rotation_mode = 'XYZ'
    bobj.rotation_euler = (1.57, 0, 0)
    #bpy.ops.object.select_all(action='SELECT')
    

class IMPORT_OT_galaxies_mgn(bpy.types.Operator, ImportHelper):
    '''Import MGN object'''
    bl_idname='import_mesh.mgn'
    bl_label='Import MGN'
    bl_description = 'Import a SWG Animated Mesh.'
    bl_options = {'PRESET', 'UNDO'}
    #filepath = StringProperty(name="File Path", description="File path used for importing the MGN file", maxlen=1024, default="", subtype='FILE_PATH')
    filter_glob: StringProperty(
                default="*.mgn",
                options={'HIDDEN'},
        )
    filename_ext = ".mgn"
    def execute(self, context):

        keywords = self.as_keywords(ignore=("filter_glob",))        

        imported = import_mgn(context, **keywords)

        if imported:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

    # def invoke(self, context, event):
    #     wm = context.window_manager
    #     wm.fileselect_add(self)
    #     return {'RUNNING_MODAL'}
    def draw(self, context):
        pass
