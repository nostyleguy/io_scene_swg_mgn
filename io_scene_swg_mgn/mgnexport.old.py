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
import bpy, mathutils, struct, os
import bmesh
from bpy.props import *
from mathutils import Vector
from . import iff_tools, mgn_tools

def export_mgn(filepath):
    bpy.ops.object.mode_set(mode='OBJECT')
    
# Let layer to 0 (layer1), to make sure no other layers get processed.  
    layerIndex = 0 
    objects = bpy.context.scene.objects

# Set intial declarations and blend names.  Recalc Tessfaces
    print("Set intial variables and lists")
    bltname = ['blend_muscle','blend_fat','blend_skinny','blend_flat_chest','blend_chinsize_1','blend_chinsize_0']
    current_obj = bpy.context.active_object
    mesh_object = bpy.context.object.data
    scene = bpy.context.scene
    bm = bmesh.new()
    bm.from_mesh(mesh_object)
    if not mesh_object.tessfaces and mesh_object.polygons:
        mesh_object.calc_tessface()

# Start pulling Faces, Vertices, UVS, etc.. add to mat_dict & uv_dict
    print("build material dictionary for PSDT")
    mat_dict = {}
    allfaces = []
    matkey = 0
    face_set = []
    vert_set = []
    uvs = []
    uv_dict = {}
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    uvname = bm.loops.layers.uv.verify()
    uvMap = bm.loops.layers.uv[uvname.name]
    for face in bm.faces:
        face_set.append(face.index)
        allfaces.append(face.index)
        for loop in face.loops:
            xx = loop[uvMap].uv[0], 1-loop[uvMap].uv[1]
            uvs.append(xx)
            uv_dict[loop.index] = loop.vert.index, xx, face.material_index, loop.index, (tuple(v.index for v in face.verts))
    vertex_indices = [tuple([i for i in mesh_object.polygons[f].vertices]) for f in face_set]
    active_texture = mesh_object.tessface_uv_textures.active
    vertex_uvs = [(active_texture.data[f].uv1[:],
                active_texture.data[f].uv2[:],
                active_texture.data[f].uv3[:]) for f in face_set]
    vertex_indices = sum(vertex_indices, ())
    vertex_uvs = sum(vertex_uvs, ())
    vert_data = zip(vertex_indices, vertex_uvs)
    unique_verts = list(set(vert_data))
    vertex_indices, vertex_uvs = zip(*unique_verts)
    poslib = set([])
    poslib.update(vertex_indices)
    poslib = sorted(list(poslib))
    mat_dict[matkey] = ("material", face_set, vertex_indices, vertex_uvs, "material", poslib, uv_dict)
    matkey += 1

# Build Vertex Group Data.
    print("build Vertex Group (bone weights) data")
    vertex_groups = current_obj.vertex_groups
    bone_names = vertex_groups.keys()
    twdtdata = []
    for name in bone_names:
        selverts = [v for v in mesh_object.vertices]
        indexval = current_obj.vertex_groups[name].index
        for v in selverts:
            for n in v.groups:
                if n.group == indexval:
                    twdtdata.append([v.index, indexval, n.weight])
    twdtdata = sorted(twdtdata)
    
# get All unique positions (position_index) and the vectors (PSN)
    print("build position index and vectors")
    position_index = [tuple([i for i in mesh_object.polygons[f].vertices]) for f in allfaces]
    position_index = list(set(sum(position_index, ())))
    PSN = [mesh_object.vertices[i].co[:] for i in position_index]

# Build Bone map, and start building TWHD & TWDT chunks.
    print("Building Initial TWHD & TWDT data chunk data")
    bone_map = dict(zip(bone_names, range(len(bone_names))))
    twhd = mgn_tools.TWHD_Chunk()
    twdt = mgn_tools.TWDT_Chunk()
    for v in position_index: ## for every vertex
        twhd.append(0)
        for group in reversed(vertex_groups):
            try:
                vg_id = bone_map[group.name]
                vg_weight = group.weight(v)
                if vg_weight > 0.0:
                    w_offset = sum(twhd[:position_index.index(v) + twhd[position_index.index(v)]])
                    twhd[v] +=1
            except:
                pass   
    for ix, v in enumerate(twdtdata):
        twdt.insert(ix, (v[1], v[2]))

# Get all Normal data   
    print("Build normals Data")
    mesh_object.calc_normals()
    normal_lib = set([])
    normal_lib.update([mesh_object.vertices[i].normal[:] for i in position_index])

# Get Tangent Data
    print("Build tangents (DOT3) data")
    tang_lib = set([])
    mesh_object.calc_tangents()
    for loop in mesh_object.loops:
        a = loop.tangent[:]
        a = list(a)
        a.insert(3, 1.0)
        a = tuple(a)
        tang_lib.add(a[:])
    tang_lib = sorted(list(tang_lib))

# Start building BLT data Dictionaries.
    print("Build data dictionaries for BLT Data")
    bltlst = []    
    bltnamedata = {}
    bltposndata = {}
    bltnormdata = {}
    bltdot3data = {}
    bltindex = {}
    v2 = []
    v3 = []
    for keys in bpy.data.shape_keys:
        if keys == mesh_object.shape_keys:
            for key in keys.key_blocks[1:]:
                if key.name in bltname:
                    bltlst.append(key.name)
                    bltnamedata[key.name] = 1
                    bv = keys.key_blocks[0].data
                    for j, kv in enumerate(key.data):
                        delta = kv.co - bv[j].co
                        v2.append(delta)
                        v3.append(j)
                    a = []
                    for ele in v2:
                        a.append(ele[:])
                    a = list(a)
                    bltposndata[key.name] = a[:]
                    bltindex[key.name] = v3[:]
                    del a[:]
                    del v2[:]
                    del v3[:]
                    shpmesh = current_obj.to_mesh(scene, True, 'PREVIEW')
                    shpmesh.calc_normals()
                    bltnormdata[key.name] =([shpmesh.vertices[i].normal[:] for i in position_index])
                    bpy.data.meshes.remove(shpmesh)
                    tmp=set([])
                    shpmesh = current_obj.to_mesh(scene, True, 'PREVIEW')
                    shpmesh.calc_tangents()
                    for loop in shpmesh.loops:
                        a = loop.tangent[:]
                        a = list(a)
                        a.insert(3, 1.0)
                        a = tuple(a)
                        tmp.add(a[:])
                    tmp = list(tmp)
                    bltdot3data[key.name] = tmp[:]
                    shpmesh.free_tangents()  
                    bpy.data.meshes.remove(shpmesh)
                      
# Start building mesh here:  
# Part of this is building the cascading IFF styled folder structure.
# Root starts everything, followed by SKMG and 0004.  This exporter 
# builds v4 MGN's so I hard code it. I don't see any reason to give the 
# option to build v1, v2, & v3's. the INFO and subsequent chunks are 
# assigned to the "version" chunk as items.
    print("start building MGN")
    root = mgn_tools.SKMG_Chunk()
    version = mgn_tools.Version_Chunk(4)
    root.add_chunk(version)
    
# here we start building the Occlusion zones, default list, then pulling any from custom properties.
    if option_occlusions:
        print("Start building Occlusion zone names, and check for any attached to custom properties")
        oznfulllist = ['face','neck','skull','sideburn_l','sideburn_r','chest','torso_f','torso_b','waist_f','waist_b','r_thigh','r_shin','r_foot','l_thigh','l_shin','l_foot','r_arm','r_forearm','r_hand','l_arm','l_forearm','l_hand']
        if len(current_obj.keys()) >= 0:
            oznlist = []
            for name in current_obj.keys():
                if current_obj[name] == 1:
                    oznlist.append(name)
        else:
            oznlist = oznfulllist
    else:
        print("Skipping OZN & ZTO chunks")
        oznlist = []

# INFO chunk is fairly self explanatory. these counts are important tho.
    print("build INFO chunk")
    info = mgn_tools.SKMG_INFO_Chunk()
    info.new()
    info['unk1'] = 0
    info['unk2'] = 0
    info['skeleton_count'] = 1
    info['bone_count'] = len(bone_names)
    info['location_count'] = len(PSN)
    info['weight_count'] = len(twdtdata)
    info['normal_count'] = len(normal_lib)
    info['material_count'] = len(bpy.data.materials)
    info['blend_count'] = len(bltlst)
    if not option_occlusions:
        info['ozn_count'] = 0
        info['fozc_count'] = 0
        info['ozc_count'] = 0
        info['occlusion_layer'] = -1
    else:
        info['ozn_count'] = len(oznlist)
        info['fozc_count'] = 0
        info['ozc_count'] = len(oznlist)
        info['occlusion_layer'] = 2

    info.save()
    version.add_chunk(info)

# Grab Skeleton file name from Export Dialogue or custom property if assigned.
    print("build SKTM chunk")
    option_skeleton = 'all_b'
    skeletons = mgn_tools.SKTM_Chunk()
    try:
        if current_obj['SKTM']:
            skel_name = 'appearance/skeleton/' + current_obj['SKTM'] + '.skt'
    except KeyError:
        skel_name = 'appearance/skeleton/' + option_skeleton + '.skt'
    skeletons.append(skel_name)
    skeletons.save()
    version.add_chunk(skeletons)

# build XFNM or bone list
    print("Build XFNM Chunk")
    xfnm = mgn_tools.XFNM_Chunk()
    for name in bone_names:
        xfnm.append(name)
    xfnm.save()
    version.add_chunk(xfnm)

# Build POSN or position vectors
    print("build POSN chunk")
    posn = mgn_tools.SKMG_POSN_Chunk()
    for v in PSN:
        posn.append(v)
    posn.save()
    version.add_chunk(posn)

# Finish saving the TWHD and TWDT chunks that were built above.  
    print("build TWHD & TWDT chunks from prior data")  
    twhd.save()
    twdt.save()
    version.add_chunk(twhd)
    version.add_chunk(twdt)

# Build NORM chunk    
    print("build NORM chunk")        
    norm = mgn_tools.SKMG_NORM_Chunk()
    for v in normal_lib:
        norm.append(v)
    norm.save()
    version.add_chunk(norm)

# Build DOT3 chunk with tangent data.
    print("Build DOT3 Chunk")
    dot3 = mgn_tools.SKMG_DOT3_Chunk()
    for v in tang_lib:
        dot3.append(v)
    dot3.save()
    version.add_chunk(dot3)

# Start building the blends.
    if bltnamedata:
        print("build BLTS & BLT chunks")
        bltschunk = mgn_tools.BLTS_Chunk()
        version.add_chunk(bltschunk)
# BLT is a subfolder(child) of BLTS, so we add it to the BLTS chunk instead of 
# version.  Because we can have multiple BLT chunks we start a loop of keys.
    bltidx = []
    for key in bltnamedata:
        bltchunk = mgn_tools.BLT_Chunk()
        bltschunk.add_chunk(bltchunk)
# BLT info is important in that the counts matter, otherwise it's the same structure
# as INFO prior.
        bltinfo = mgn_tools.BLT_INFO_Chunk()
        bltinfo.new()
        bltinfo['normal_count'] = len(bltnormdata[key])
        bltinfo['position_count'] = len(bltposndata[key])
        bltinfo['name'] = key
        bltinfo.save()
        bltchunk.add_chunk(bltinfo)
# Because the client was freaking out by only adding positions with delta's
# I'm adding ALL the vertex positions, even those that didn't move.  Seems 
# to work much better, even tho the SOE MGN's don't contain zero delta's.
# for note, here I send the key like "blend_muscle" and list of tuples for data.
        bltidx = bltindex[key]
        bltposn = mgn_tools.BLT_POSN_Chunk()
        t = 0
        for v in bltposndata[key]:
            bltposn.append(bltidx[t], v)
            t += 1
        bltposn.save()
        bltchunk.add_chunk(bltposn)
# this is remarked out as they don't appear to shade correctly.
# again, we send all normas, not just delta's as key and list of tuples.
#        bltnorm = mgn_tools.BLT_NORM_Chunk()
#        t = 0
#        for v in bltnormdata[key]:
#            bltnorm.append(t, v)
#            t += 1
#        bltnorm.save()
#        bltchunk.add_chunk(bltnorm)

# same as above, all dot3 data as key and list of tuples.
#        bltdot3 = mgn_tools.BLT_DOT3_Chunk()
#        t = 0
#        for v in bltdot3data[key]:
#            bltdot3.append(t, v)
#            t += 1
#        bltdot3.save()
#        bltchunk.add_chunk(bltdot3)

# Build OZN chunk from custom properties added to the mesh.
    if option_occlusions:
        print("build OZN Chunk")
        ozn = mgn_tools.OZN_Chunk()
        for name in oznlist:
            ozn.append(name)
        ozn.save()
        version.add_chunk(ozn)  

# The FOZC and OCZ chunks are currently remarked out as I dont fully understand their functions yet.
#    fozc = mgn_tools.FOZC_Chunk()
#    for name in fozcidx:
#        fozc.append(0)
#    fozc.save()
#    version.add_chunk(fozc)         

#    ozc = mgn_tools.OZC_Chunk()
#    #for name in ozcidx:
#        #ozc.append(0)
#    ozc.save()
#    version.add_chunk(ozc)      

# Build the ZTO chunk from the OZN chunk names.
        print("build ZTO Chunk")
        zto = mgn_tools.ZTO_Chunk()
        for ix, name in enumerate(oznlist):
            zto.append(ix)
        zto.save()
        version.add_chunk(zto)

# Build PSDT Chunks, one for each assigned material.
    print("Build PSDT chunk(s)")
    for matidx, material in enumerate(bpy.data.materials):  #mat_dict.keys():
        mat = 0

        # Add PSDT chunk.
        psdt = mgn_tools.PSDT_Chunk()

        # get UV's, Verts, Faces, etc.. from mat_dict.
        uvdict = mat_dict[mat][6]
        u_verts = []
        u_uvs = []
        u_faces = []
        u_pcord = []
        for indi in uvdict.keys():
            u_verts.append(uvdict[indi][0])
            u_uvs.append(uvdict[indi][1])
            u_faces.append(uvdict[indi][2])
        for i, ii in enumerate(u_verts):
            u_pcord.append(i)
        u_pcord = [(u_pcord[i],u_pcord[i+1],u_pcord[i+2]) for i in range(0,len(u_pcord),3)]
        u_faces = [u_faces[i] for i in range(0,len(u_faces),3)]
        
        # Add Name Chunk.
        name = mgn_tools.NAME_Chunk()
        mat_name = 'shader/' + material.name + '.sht'
        name.set(mat_name)
        name.save()
        psdt.add_chunk(name)

        # Add PIDX Chunk.
        pidx = mgn_tools.PIDX_Chunk()
        pidx_map = u_verts
        for i in pidx_map:
            pidx.append(i)
        pidx.save()
        psdt.add_chunk(pidx)

        # add NIDX chunk.
        nidx = mgn_tools.NIDX_Chunk()
        mat_normals = [mesh_object.vertices[i].normal[:] for i in u_verts]
        nidx_map = [list(normal_lib).index(v) for v in mat_normals]
        for i in nidx_map:
            nidx.append(i)
        nidx.save()
        psdt.add_chunk(nidx)

        # add TXCI chunk.
        txci = mgn_tools.TXCI_Chunk()
        txci.new()
        txci.save()
        psdt.add_chunk(txci)

        # add TCSD Chunk (UV's)
        mat_tcsd = mgn_tools.TCSD_Chunk()
        for uv in u_uvs:
            mat_tcsd.append(uv)
        mat_tcsd.save()

        # add TCSF parent chunk.
        tcsf = mgn_tools.TCSF_Chunk()
        tcsf.add_chunk(mat_tcsd)
        psdt.add_chunk(tcsf)

        # add PRIM chunk.
        prim = mgn_tools.PRIM_Chunk()
        prim_info = mgn_tools.PRIM_INFO_Chunk()
        prim_info.set(1)
        prim_info.save()
        prim.add_chunk(prim_info)

        # ITL / OITL chunks. USE ITL until we figure out FOZC & OCZ chunks.
        itl = mgn_tools.ITL_Chunk()
        itl.new()
        for i, f in enumerate(u_pcord):
            if bpy.data.materials[u_faces[i]] == material:
                itl.append(f)
        itl.save()

        # OITL,  but it doesn't do anything different without OZC.
        itlst = []
        itlst1 = []
        oitl = mgn_tools.OITL_Chunk()
        oitl.new()
        mapped_indices = mat_dict[mat][2]
        for i, f in enumerate(u_pcord):
            if bpy.data.materials[u_faces[i]] == material:
                itlst.append(f)
                itlst1.append(0)
                for x in itlst[:]:
                    itlst1.append(x[0])
                    itlst1.append(x[1])
                    itlst1.append(x[2])
                oitl.append(tuple(itlst1))
                itlst = []    
                itlst1 = []
        oitl.save()

        # Logic for ITL / OITL.  
        if option_oitldata:
            print("Using OITL")
            prim.add_chunk(oitl)
        else:
            print("Usint ITL")
            prim.add_chunk(itl)
        psdt.add_chunk(prim)
        version.add_chunk(psdt)

    # Build final MGN file.
    print("build MGN File")
    mgn_out = mgn_tools.MGN_File()
    mgn_out.add_root(root)
    if os.path.exists(filepath):
        option_overwrite == True
    mgn_out.save(filepath, option_overwrite)

class EXPORT_OT_galaxies_mgn(bpy.types.Operator):
    '''Export MGN object'''
    bl_idname='export_mesh.mgn'
    bl_label='Export MGN'
    bl_description = 'Export a SWG Animated Mesh.'

    filepath = StringProperty(name="File Path", description="File path used for exporting the MGN file", maxlen=1024, default="", subtype='FILE_PATH')
    tangents = BoolProperty(name='Calculate Tangents', description="Calculate tangent vectors.", default=True)
    skeleton = StringProperty(name='Skeleton File', description="Skeleton file this mesh references. Debug option", maxlen=1024, default='all_b')
    occlusions = BoolProperty(name='Include OZN & ZTO?', description="Add OZN & ZTO chunks?", default=False)
    oitldata = BoolProperty(name='Use OITL?', description="Select to use OITL instead of ITL", default=False)
    overwriteWarning = BoolProperty(name="Overwrite Existing File", default=False)

    def execute(self, context):
        global option_tangents, option_skeleton, option_occlusions, option_oitldata, option_overwrite
        option_tangents = self.tangents
        option_skeleton = self.skeleton
        option_occlusions = self.occlusions
        option_oitldata = self.oitldata
        option_overwrite = self.overwriteWarning
        exported = export_mgn(self.filepath)
        if exported:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {"RUNNING_MODAL"}
