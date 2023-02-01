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
import bpy, struct, array
from . import swg_types

from bpy.props import *
from bpy_extras.io_utils import unpack_list, unpack_face_list
from mathutils import Vector

def import_mgn( context, 
                filepath, 
                *,      
                global_matrix=None):

    mgn = swg_types.SWGMgn(filepath)
    mgn.load()

    mesh_name = filepath.split('\\')[-1].split('.')[0]
    mesh = bpy.data.meshes.new(mesh_name)
        
    edges=[]
    blender_verts = []
    blender_norms = []
    for v in mgn.positions:
        blender_verts.append([v[0],v[1],v[2]])

    for n in mgn.normals:
        blender_norms.append([n[0],n[1],-n[2]])

    faces_by_material=[]
    normals=[]
    tris = []
    tris_flat = []
    uvs_flat = []
    for pid, psdt in enumerate(mgn.psdts):
        mat = bpy.data.materials.new(psdt.stripped_shader_name())
        mesh.materials.append(mat)        
        faces_by_material.append([])

        for prim in psdt.prims:
            for tri in prim:
                p1 = psdt.pidx[tri.p3]
                p2 = psdt.pidx[tri.p2]
                p3 = psdt.pidx[tri.p1]
                
                normals.append(blender_norms[psdt.nidx[tri.p3]])
                normals.append(blender_norms[psdt.nidx[tri.p2]])
                normals.append(blender_norms[psdt.nidx[tri.p1]])

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
                    
                    uvs_flat[uv_layer_num].append(psdt.uvs[uv_layer_num][tri.p3])
                    uvs_flat[uv_layer_num].append(psdt.uvs[uv_layer_num][tri.p2])
                    uvs_flat[uv_layer_num].append(psdt.uvs[uv_layer_num][tri.p1])

    mesh.from_pydata(blender_verts, edges, tris)
    mesh.use_auto_smooth = True
    mesh.normals_split_custom_set(normals)
    mesh.transform(global_matrix)
    scene_object = bpy.data.objects.new(mesh_name, mesh)
    context.collection.objects.link(scene_object)
    mesh.validate()
    mesh.update()        

    for flist in mesh.polygons: 
        for id, face_list in enumerate(faces_by_material):
            if flist.vertices[:] in face_list:
                flist.material_index = id

    for i, uvs in enumerate(uvs_flat):
        print(f'UV Layer: {i} -- lengths of UVs ({len(uvs)}) and Tri indecies ({len(tris_flat)})')
        if len(uvs) != len(tris_flat):
            print(f'*** WARNING *** UV Layer: {i} -- Unmatched lengths of UVs ({len(uvs)}) and Tri indecies ({len(tris_flat)}). Skipping!')
            continue
        uvlayer = mesh.uv_layers.new(name=f'UVMap-{str(i)}')
        mesh.uv_layers.active = uvlayer
        for ind, vert in enumerate(tris_flat):
            uv = [uvs[ind][0], 1 - uvs[ind][1]]
            uvlayer.data[ind].uv = uv

    vgs = {}
    for i, bone in enumerate(mgn.bone_names):
        vg = scene_object.vertex_groups.new(name=bone)
        vgs[i] = vg

    for i, vertex_weights in enumerate(mgn.vertex_weights):
        sum=0
        for weight in vertex_weights:
            if sum + weight[1] > 1.0:
                weight[1] = (1.0 - sum)
                print(f"Capped bone weight contribution of: {i} {weight[0]} to {weight[1]}!")
            vgs[weight[0]].add([i], weight[1], 'ADD')
    
    scene_object.shape_key_add(name='Basis')
    for i, blend in enumerate(mgn.blends):
        sk = scene_object.shape_key_add(name=blend.name)
        for vert in blend.positions:
            id = vert[0]
            delta = [vert[1][0], vert[1][1], -vert[1][2]]
            delta_v = Vector(delta)
            sk.data[id].co = scene_object.data.vertices[id].co + (global_matrix @ delta_v)
    
    for i, skel in enumerate(mgn.skeletons):
        scene_object[f'SKTM_{i}'] = skel

    print(f"Occulusions: {str(mgn.occlusions)}")
    for zone in mgn.occlusions:
        scene_object[zone[0]] = zone[2]

    scene_object[f'OCC_LAYER'] = mgn.occlusion_layer

    return {'FINISHED'}