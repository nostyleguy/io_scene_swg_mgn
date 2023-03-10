# MIT License
#
# Copyright (c) 2022 Nick Rafalski
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

TextureCoordinateSetCountShift = 8
TextureCoordinateSetCountMask = 15

TextureCoordinateSetDimensionBaseShift = 12
TextureCoordinateSetDimensionPerSetShift = 2
TextureCoordinateSetDimensionAdjustment = 1
TextureCoordinateSetDimensionMask = 3

BlendCountShift = 24
BlendMask = 7


F_none = 0b00000000000000000000000000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 0000),
F_position = 0b00000000000000000000000000000001 # BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 0001),
F_transformed = 0b00000000000000000000000000000010 # BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 0010),
F_normal = 0b00000000000000000000000000000100 # BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 0100),
F_color0 = 0b00000000000000000000000000001000 #BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 1000),
F_color1 = 0b00000000000000000000000000010000 #BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0001, 0000),

F_pointSize = 0b00000000000000000000000000010000 #BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0010, 0000),

F_textureCoordinateCount0 = 0b00000000000000000000000000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateCount1 = 0b00000000000000000000000100000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0001, 0000, 0000),
F_textureCoordinateCount2 = 0b00000000000000000000001000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0010, 0000, 0000),
F_textureCoordinateCount3 = 0b00000000000000000000001100000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0011, 0000, 0000),
F_textureCoordinateCount4 = 0b00000000000000000000010000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0100, 0000, 0000),
F_textureCoordinateCount5 = 0b00000000000000000000010100000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0101, 0000, 0000),
F_textureCoordinateCount6 = 0b00000000000000000000011000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0110, 0000, 0000),
F_textureCoordinateCount7 = 0b00000000000000000000011100000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0111, 0000, 0000),
F_textureCoordinateCount8 = 0b00000000000000000000100000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 1000, 0000, 0000),

F_textureCoordinateSet0_1d = 0b00000000000000000000000000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet0_2d = 0b00000000000000000001000000000000 # BINARY8(0000, 0000, 0000, 0000, 0001, 0000, 0000, 0000),
F_textureCoordinateSet0_3d = 0b00000000000000000010000000000000 # BINARY8(0000, 0000, 0000, 0000, 0010, 0000, 0000, 0000),
F_textureCoordinateSet0_4d = 0b00000000000000000011000000000000 # BINARY8(0000, 0000, 0000, 0000, 0011, 0000, 0000, 0000),
F_textureCoordinateSet1_1d = 0b00000000000000000000000000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet1_2d = 0b00000000000000000100000000000000 # BINARY8(0000, 0000, 0000, 0000, 0100, 0000, 0000, 0000),
F_textureCoordinateSet1_3d = 0b00000000000000001000000000000000 # BINARY8(0000, 0000, 0000, 0000, 1000, 0000, 0000, 0000),
F_textureCoordinateSet1_4d = 0b00000000000000001100000000000000 # BINARY8(0000, 0000, 0000, 0000, 1100, 0000, 0000, 0000),

F_textureCoordinateSet2_1d = 0b00000000000000000000000000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet2_2d = 0b00000000000000010000000000000000 # BINARY8(0000, 0000, 0000, 0001, 0000, 0000, 0000, 0000),
F_textureCoordinateSet2_3d = 0b00000000000000100000000000000000 # BINARY8(0000, 0000, 0000, 0010, 0000, 0000, 0000, 0000),
F_textureCoordinateSet2_4d = 0b00000000000000110000000000000000 # BINARY8(0000, 0000, 0000, 0011, 0000, 0000, 0000, 0000),
F_textureCoordinateSet3_1d = 0b00000000000000000000000000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet3_2d = 0b00000000000001000000000000000000 # BINARY8(0000, 0000, 0000, 0100, 0000, 0000, 0000, 0000),
F_textureCoordinateSet3_3d = 0b00000000000010000000000000000000 # BINARY8(0000, 0000, 0000, 1000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet3_4d = 0b00000000000011000000000000000000 # BINARY8(0000, 0000, 0000, 1100, 0000, 0000, 0000, 0000),

F_textureCoordinateSet4_1d = 0b00000000000000000000000000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet4_2d = 0b00000000000100000000000000000000 # BINARY8(0000, 0000, 0001, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet4_3d = 0b00000000001000000000000000000000 # BINARY8(0000, 0000, 0010, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet4_4d = 0b00000000001100000000000000000000 # BINARY8(0000, 0000, 0011, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet5_1d = 0b00000000000000000000000000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet5_2d = 0b00000000010000000000000000000000 # BINARY8(0000, 0000, 0100, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet5_3d = 0b00000000100000000000000000000000 # BINARY8(0000, 0000, 1000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet5_4d = 0b00000000110000000000000000000000 # BINARY8(0000, 0000, 1100, 0000, 0000, 0000, 0000, 0000),

F_textureCoordinateSet6_1d = 0b00000000000000000000000000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet6_2d = 0b00000001000000000000000000000000 # BINARY8(0000, 0001, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet6_3d = 0b00000010000000000000000000000000 # BINARY8(0000, 0010, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet6_4d = 0b00000011000000000000000000000000 # BINARY8(0000, 0011, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet7_1d = 0b00000000000000000000000000000000 # BINARY8(0000, 0000, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet7_2d = 0b00000100000000000000000000000000 # BINARY8(0000, 0100, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet7_3d = 0b00001000000000000000000000000000 # BINARY8(0000, 1000, 0000, 0000, 0000, 0000, 0000, 0000),
F_textureCoordinateSet7_4d = 0b00001100000000000000000000000000 # BINARY8(0000, 1100, 0000, 0000, 0000, 0000, 0000, 0000),
F_blend0 = 0b00000000000000000000000000000000 # BINARY8(0000,0000,0000,0000,0000,0000,0000,0000),
F_blend1 = 0b00010000000000000000000000000000 # BINARY8(0001,0000,0000,0000,0000,0000,0000,0000),
F_blend2 = 0b00100000000000000000000000000000 # BINARY8(0010,0000,0000,0000,0000,0000,0000,0000),
F_blend3 = 0b00110000000000000000000000000000 # BINARY8(0011,0000,0000,0000,0000,0000,0000,0000),
F_blend4 = 0b01000000000000000000000000000000 # BINARY8(0100,0000,0000,0000,0000,0000,0000,0000),
F_blend5 = 0b01010000000000000000000000000000 # BINARY8(0101,0000,0000,0000,0000,0000,0000,0000)

def hasPosition(flags):
    return (flags & F_position) != 0

def isTransformed(flags):
    return (flags & F_transformed) != 0

def hasNormal(flags):
    return (flags & F_normal) != 0

def hasPointSize(flags):
    return (flags & F_pointSize) != 0

def hasColor0(flags):
    return (flags & F_color0) != 0

def hasColor1(flags):
    return (flags & F_color1) != 0

def getNumberOfTextureCoordinateSets(flags):
    return (int(flags) >> int(TextureCoordinateSetCountShift)) & (int(TextureCoordinateSetCountMask))

def getTextureCoordinateSetDimension(flags, textureCoordinateSet):
    shift = int(TextureCoordinateSetDimensionBaseShift) + (textureCoordinateSet * int(TextureCoordinateSetDimensionPerSetShift))
    before_adjustment = ((flags >> shift) & TextureCoordinateSetDimensionMask) 
    return before_adjustment + TextureCoordinateSetDimensionAdjustment

def setPosition(flags, enabled):
    if (enabled):
        flags |= F_position
    else:
        flags &= ~F_position
    return flags

def setTransformed(flags, enabled):
    if (enabled):
        flags |= F_transformed
    else:
        flags &= ~F_transformed
    return flags

def setNormal(flags,  enabled):
    if (enabled):
        flags |= F_normal
    else:
        flags &= ~F_normal
    return flags
        
def setPointSize(flags,  enabled):
    if(enabled):
        flags |= F_pointSize
    else:
        flags &= ~F_pointSize
    return flags

def setColor0(flags,  enabled):
    if (enabled):
        flags |= F_color0
    else:
        flags &= ~F_color0
    return flags

def setColor1(flags,  enabled):
    if (enabled):
        flags |= F_color1
    else:
        flags &= ~F_color1
    return flags

def setNumberOfTextureCoordinateSets(flags, numberOfTextureCoordinateSets):
    flags = (flags & ~(TextureCoordinateSetCountMask << TextureCoordinateSetCountShift)) | ((numberOfTextureCoordinateSets) << TextureCoordinateSetCountShift)
    return flags

def setTextureCoordinateSetDimension(flags, textureCoordinateSet, dimension):
    shift = (TextureCoordinateSetDimensionBaseShift + (textureCoordinateSet * TextureCoordinateSetDimensionPerSetShift))
    flags = (flags & ~((TextureCoordinateSetDimensionMask) << shift)) | ((dimension - TextureCoordinateSetDimensionAdjustment) << shift)
    return flags
