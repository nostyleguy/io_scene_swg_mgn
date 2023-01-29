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
# Instructions: use to Export a single Object to Star Wars Galaxies MGN format.
# Option Calc Tangents: Recalc the Tangental normals (Dot3). Usually Necessary.
# Option OZN & ZTO: export Occlusions. See Readme.
# Option Skeleton:  name of the skeleton file without extention. See Readme.
# Option OITL:  Export OITL instead of ITL. See Readme.
# ##############################################################################
import bpy, mathutils, struct, os, collections
import time, datetime
import bmesh
from bpy.props import *
from mathutils import Vector
from . import swg_types, mgn_tools

oznfulllist = ['face','neck','skull','sideburn_l','sideburn_r','chest','torso_f','torso_b','waist_f','waist_b','r_thigh','r_shin','r_foot','l_thigh','l_shin','l_foot','r_arm','r_forearm','r_hand','l_arm','l_forearm','l_hand']
        
def mesh_triangulate(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()

def export_mgn(context, 
               filepath, 
               *,
               do_tangents = True):    
    t = time.time()

    current_obj = None
    objects = context.selected_objects
    mat = None
    if not (len(objects) == 1):
        return {'ERROR'}

    for ob_main in objects:
        obs = [(ob_main, ob_main.matrix_world)]
        for ob, ob_mat in obs:
            if ob.type != 'MESH':
                return False
            else:
                current_obj = ob
                mat = ob_mat
                
    scene = context.scene
                
    bm = current_obj.to_mesh()    
    #bm.transform(global_matrix @ ob_mat)
    mesh_triangulate(bm)

    bm.calc_normals()
    
    tang_lib = []
    if do_tangents:
        bm.calc_tangents()
        for i, loop in enumerate(bm.loops):
            a = loop.tangent[:]
            b = list(a)
            b.insert(3, 1.0)
            b = tuple(b)
            tang_lib.append(b[:])

    mgn = swg_types.SWGMgn(filepath)

    i = 0
    for key in current_obj.keys():
        if key.startswith("SKTM_"):
            mgn.skeletons.append(current_obj[key])
        else:
            mgn.occlusions.append([key, i, current_obj[key]])
            i += 1

    for vert in bm.vertices:
        mgn.positions.append([vert.co[0],vert.co[2],vert.co[1]])
        mgn.normals.append([-vert.normal[0],-vert.normal[2],-vert.normal[1]])

    if do_tangents:
        mgn.dot3=[]
        for tang in tang_lib:
            mgn.dot3.append([tang[0], tang[2], tang[1], tang[3]])

    twhd = []
    twdt = []
    for keys in bpy.data.shape_keys:
        if keys == bm.shape_keys:
            for key in keys.key_blocks[1:]:

                blt = swg_types.SWGBLendShape()
                blt.name = key.name
                blt.dot3 = []
                basis = keys.key_blocks[0].data
                for j, kv in enumerate(key.data):
                    delta = kv.co - basis[j].co
                    if delta[0] != 0 and delta[1] != 0 and delta[2] != 0:
                        blt.positions.append([j, delta[:]])
                        blt.normals.append([j, [0,0,0]])

                        if do_tangents:
                            blt.dot3.append([j, [0,0,0]])
                mgn.blends.append(blt)
            
    face_index_pairs = [(face, index) for index, face in enumerate(bm.polygons)]
    faces_by_material = {}
    for f, f_index in face_index_pairs:
        if not f.material_index in faces_by_material:
            faces_by_material[f.material_index] = []    
            #print(f'Added material index: {f.material_index}')    
        faces_by_material[f.material_index].append(f)

    #print(f'faces_by_material: {[(str(len(faces_by_material[key]))) for key in faces_by_material]}')

    
    #num_uv_layers = len(bm.uv_layers)    
    uv_layer = bm.uv_layers.active.data[:]
    for material_index in faces_by_material:
        last_tri_index = None
        running_tri_index = 0
        faces = faces_by_material[material_index]
        psdt = swg_types.SWGPerShaderData()
        psdt.name = current_obj.material_slots[material_index].material.name

        # psdt.num_uvs = num_uv_layers
        # for i in range(0, num_uv_layers):
        #     psdt.uvs.append([])
        #     psdt.uv_dimensions.append(2) # has to be 2 right?..

        print(f'Material: {psdt.name}')
        mgn.psdts.append(psdt)

        reverse_position_lookup={}
        pidx_id = 0

        psdt.prims.append([])
        psdt.uvs.append([])
        psdt.dot3 = []

        
        for f in faces:
            t1=None
            t2=None
            t3=None
            for uv_index, l_index in enumerate(f.loop_indices):
                master_vert_id = f.vertices[uv_index]

                if not master_vert_id in reverse_position_lookup:
                    reverse_position_lookup[master_vert_id] =  pidx_id                    
                    pidx_id += 1

                #if not master_vert_id in psdt.pidx:
                psdt.pidx.append(master_vert_id)
                psdt.nidx.append(master_vert_id)
                psdt.uvs[0].append(uv_layer[l_index].uv)

                if do_tangents:
                    psdt.dot3.append(l_index)
                
                if last_tri_index == None:
                    last_tri_index = l_index
                    print(f"Starting last_tri_index at {last_tri_index}")
                    
                if t1 == None:
                    #t1 = reverse_position_lookup[master_vert_id]
                    #t1 = running_tri_index - last_tri_index
                    t1 = running_tri_index
                elif t2 == None:
                    #t2 = reverse_position_lookup[master_vert_id]
                    #t2 = running_tri_index - last_tri_index
                    t2 = running_tri_index
                else:
                    #t3 = reverse_position_lookup[master_vert_id]
                    #t3 = running_tri_index - last_tri_index
                    t3 = running_tri_index
                    psdt.prims[0].append(t1)
                    psdt.prims[0].append(t2)
                    psdt.prims[0].append(t3)
                    
                    #print(f"Wrote tri {t1} {t2} {t3}")

                running_tri_index += 1

    vertex_groups = current_obj.vertex_groups
    bone_names = vertex_groups.keys()
    twdtdata = {}
    for name in bone_names:
        mgn.bone_names.append(name)
        selverts = [v for v in bm.vertices]
        indexval = current_obj.vertex_groups[name].index
        for v in selverts:
            for n in v.groups:
                if n.group == indexval:
                    if not v.index in twdtdata:
                        twdtdata[v.index] = []
                    twdtdata[v.index].append([indexval, n.weight])
    od = collections.OrderedDict(sorted(twdtdata.items()))
    mgn.twdt = list(od.values())

    print(f"Assembling final IFF ... ")
    mgn.write()
    now = time.time()        
    print(f"Successfully wrote: {filepath} Duration: " + str(datetime.timedelta(seconds=(now-t))))
    return {'FINISHED'}