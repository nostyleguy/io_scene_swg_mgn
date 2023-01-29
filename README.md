# io_scene_swg_mgn
A Blender add-on for importing and export Star Wars Galaxies animated mesh files (.mgn)
## Blender Version Support
Should work with Blender 3+
## Features
* Imports base mesh, UV, Shader Name, Bone names, Vertex weights, Blends, occlusion zones, and skeleton name as follows:
  * The mesh is obviously the active imported object.
  * Bone names are Imported as vertex groups.
  * Vertex weights are imported and assigned relative to the vertex groups they belong to.
  * Blends are imported as shape keys.
  * Occlusion layer (2 for most wearables) is stored in the custom property, "OCC_LAYER"
  * Skeleton name(s) are imported as a custom properties. The name of the property will be of the form SKTM_n where n is an integer. This allows multiple skeletons to be affected. The value of the property is the path to the skeleton, including the directory, e.g. "appearance/skeleton/all_b.skt".
  * Occlusions are imported as custom properties. The name of the occlusion zone is the name of the custom property. Any custom proprety whose value isn't OCC_LAYER or starts with "STKM_" will be treated like an occlusion zone.
  * Shader name is imported as a material, in cases where there are multiple shaders, each shader is added as a new material.  Also,  each polygon in the mesh is properly assigned to each material.  However, each created material while having the proper shader name, will still only be a default blank material, without textures, shading, etc…  You can, however, load any textures associated with the SWG shader into blender, and they will map properly onto the mesh.  But you have to do this manually, the importer will not do this for you. 
  * UVs are imported for each shader, and stored in a single UV file within blender.  Again, the UV’s are assigned properly to each Poly and material that gets created.  This allows you to import any and all textures from the SWG shader files into blender, and they will map properly.   Please be aware that SWG UV’s are written to the MGN files Upside-Down.  Meaning they have to be flipped upright on import for them to work properly in blender.   
* This plugin will export a single object from blender into the MGN file format for SWG.  Items exported are the mesh, UV, Shader names, Bone names, bone weights, Blends, Occlusions and skeleton name.
  * Each item works the same as has already been described above for the importer.   This exporter will fail if multiple objects are selected for export.
  * The exporter will also flip the UV Upside down (mirror on the Y axis), on export,  so you don’t need to manually flip the UV.
  * Materials get written to the PDST chunks in the order in which they appear in blender.  I would not change this order for imported MGNs, and for custom items, if you find the materials and shaders getting mixed up in the client,  I’d adjust the listing order to compensate.  This shouldn’t be a problem,  but it has on occasion been a bit fickle.

Notes: 
* If you create a new original mesh/object, you’ll first need to choose a skeleton file that your mesh should use.  From that skeleton file, you’ll want to use the bone names in the file for your vertex group names in Blender.  Then you can assign vertex weights as necessary.  When finished, make sure that the skeleton file name is set as a SKTM_n custom property where n is an integer. 
* If you import an existing MGN,  the vertex groups will be named properly from the start.  The skeleton file to be used will also be added as a custom property to the mesh. 
* Occlusion (OZN and ZTO chunks, not FOZC or OZC yet) are exported automatically based on the existence of Custom Properties. To understand what this is doing you probably need some additional information on how it works.
  * The SWG client has a list of zones that can be made invisible for humanoid type objects.  Most creatures do not use occlusions, and any extra layers of clothing or items are made to fit exactly without clipping.  For humanoids that can use extra layers of clothing and items,  SWG uses occlusions to avoid clipping with lower level layers.  So using a human as an example,  it loads with a default skin as layer 1.  If you make a shirt for the human to wear,  the shirt will occupy layer 2,  and without any occlusions the layer 1 body can clip through the shirt during movement in some circumstances.  To avoid this clipping, you can use occlusions, which will make segments of the layer 1 skin invisible.  a long sleeved shirt will occlude the chest, torso_f, torso_b, L_arm, R_arm, and maybe the formarms, and maybe even the waist zones… 
  * It’s important to understand that you are not occluding zones on the object you’re working with, but rather that you are occluding zones on the base skin mesh you want to make invisible.
  * So, to include occlusions as part of the export, I did so by making each exclusion zone a custom property for the blender mesh/object.   The easiest way to see this in action is to import an existing clothing item,  dresses or robes are probably the best examples to get to know the system.  Then in blender,  look at the custom properties, and you’ll see a listing for every occlusion zone that clothing item has been set to use.   For the properties:  1 = occluded (invisible),  0 = not occluded.  All zones import as occluded “1” by default, so you’ll want to make sure that you’ve switched the zones you want to see to “0”.
  * If you export your clothing item, and load up the SWG client, and don’t see a body part you were expecting to see,  example:  hands, or feet, or face, etc…,   then come back to blender and set those zones to zero.
Some additional function information.
* Blends / Shape keys:
  * Blends are the basic deformations of the base mesh that define how the object deforms along with the “body shape” sliders within the SWG client.  There are 4 main Blends for most clothing:  flat_chest, Skinny, Fat, and Muscle.  Heads for the various species have many more blends that correspond to the sliders you see at character creation. The base mesh, is also the Basis shape key.  Search google,  research, and learn for yourself how to properly use and save shape keys within blender.
* DOT3:
  * DOT3 (aka tangents, aka normalmap coords, aka per-pixel lighting coords) are optionally exportable since some shaders don't want them. Controlled by the export option, "DOT3" 

Limitations:
* No support for hardpoints (either dynamic or static) yet. These are sometimes used for things like earing placeholders on species' heads. I have a plan for this
* No support for the TRTS (Texture Renderers) form yet. This is necessary to let certain species' body parts have different textured skin, tatoos, etc.
* No Support for per-triangle occlusions (OITL)
* No support for the FOZC or OZC occlusion chunks. Most wearables seem fine without these, but it's possible something will goof up without them. 
* Material management leaves a lot to be desired. If you import multiple models that use the same material, it will create 2 materials, the second with a postfixed number (armor_padded_buckle_as9.001), and this entire name WILL be written as the shader into the PSDT chunk, which isn't what you want. You can manually assign the original material back to the slot, and it will work.  
