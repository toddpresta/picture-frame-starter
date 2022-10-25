bl_info = {
  'name': 'Picture Frame Starter',
  'version': (0, 1),
  'author': 'Todd Presta',
  'blender': (3, 1, 0),
  'category': 'Mesh',
  'location': 'Operator Search'
}

import bpy

class PictureFrameStarterPanel(bpy.types.Panel):
    bl_label = 'Picture Frame Starter'
    bl_idname = 'PANEL_PT_picture_frame_starter'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TP'
    
    def draw(self, context):
        layout = self.layout

        self.layout.label(text="Dimensions")        

        box = layout.box()

        row = box.row()
        row.prop(context.scene, 'frame_width')

        row = box.row()
        row.prop(context.scene, 'frame_height')
        
        row = box.row()
        row.prop(context.scene, 'frame_depth')

        row = box.row()
        row.prop(context.scene, 'frame_bar_width')

        self.layout.operator(PictureFrameStarterOp.bl_idname, text='Generate')

class MESH_OT_picture_frame_starter(bpy.types.Operator):
    """Create a starter picture frame"""
    bl_idname = 'mesh.picture_frame_starter'
    bl_label  = 'Picture Frame Starter'
    bl_options = {'REGISTER', 'UNDO'}
    
    frame_width: bpy.props.FloatProperty (
      name = 'Frame Width',
      default = 8.0
    )
    frame_height: bpy.props.FloatProperty (
      name = 'Frame Height',
      default = 10.0
    )
    frame_depth: bpy.props.FloatProperty (
      name = 'Frame Depth',
      default = 1.0
    )
    frame_bar_width: bpy.props.FloatProperty (
      name = 'Frame Bar Width',
      default = 2.0
    )
    
    def execute(self, context):
        """Generate Base Frame"""
        generator = PictureFrameStarterGenerator (
          self.frame_width, self.frame_height,
          self.frame_depth, self.frame_bar_width
        )
        
        generator.generate()
        
        return {"FINISHED"}

class PictureFrameStarterGenerator:
    """This class was developed as part of a self-directed Blender 3D API
    (in v3.1.2) learning project and generates a simple four-bar starter picture
    frame mesh based on passed-in width, height, depth, and bar width. Calculations
    begin with the inner surfaces of the frame and then expand outward by frame
    bar width. Starts with planar left frame, mirrors it, bridges the
    some edges, and then it extrudes all faces by depth value.
    """

    COLL_NM = 'Picture Frame Starter'
    MESH_NM = 'frame_starter_mesh'
    OBJ_NM  = 'frame_starter_obj'
    
    """JOINS: A hack to predetermine the correct edges to bridge based
    based on the calculated vertices until we can figure out how to 
    do it programmatically :)
    """
    JOINS = (1, 3, 5, 7)

    def __init__(self, w, h, d, bw):
        self.w = w
        self.h = h
        self.d = d
        self.bw = bw

    def _calc_verts(self):
        """Calculate the vertex positions of the leftmost vertical
        frame bar which would actually be the right side of the frame 
        from behind. Assumes 3D cursor in center of world and no
        other objects selected. 
    
        B
        |\ A
        | |
        |/ C
        D
        
        Spelling out the calcs below for clarity :)
        """
    
        frm_depth = -self.d/2
    
        pt_A = (-(self.w)/2, frm_depth,  self.h/2)
        pt_B = (pt_A[0]-self.bw, frm_depth, (self.h/2)+self.bw)
        pt_C = (-(self.w)/2, frm_depth, -(self.h/2))
        pt_D = (pt_C[0]-self.bw, frm_depth, pt_C[2]-self.bw)
        
        self.verts = [ pt_A, pt_B, pt_C, pt_D ]

    def generate(self):
        """Generates a rectangular picture frame with four frame
        bars each meeting at 45 degree angles, centered in the 3D
        view and in it's own Scene Collection.
        """
        # Calculate verts
        self._calc_verts()

        # Create frame mesh
        frame_mesh = bpy.data.meshes.new(self.MESH_NM)
        frame_mesh.from_pydata(self.verts, [], [])
        frame_mesh.update()
    
        # Create frame object for mesh
        frame_base_obj = bpy.data.objects.new(self.OBJ_NM, frame_mesh)

        # Create Collection - add frame
        frame_base_coll = bpy.data.collections.new(self.COLL_NM)
        bpy.context.scene.collection.children.link(frame_base_coll)
        frame_base_coll.objects.link(frame_base_obj)

        # Set the frame active
        bpy.context.view_layer.objects.active = bpy.data.objects[self.OBJ_NM]
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.edge_face_add()

        # Mirror vertical frame bar with modifier
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.object.modifiers.new(name="MM",type='MIRROR')
        bpy.ops.object.modifier_apply(modifier="MM")

        # Go into EDIT mode with all edges deselected
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False,type='EDGE')
        bpy.ops.mesh.select_all(action='DESELECT')

        # Select and bridge top edges of both vertical frame bars
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.active_object.data.edges[self.JOINS[0]].select = True
        bpy.context.active_object.data.edges[self.JOINS[2]].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.bridge_edge_loops()
        bpy.ops.mesh.select_all(action='DESELECT')

        # Select and bridge bottom edges of vertical frame bars
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.active_object.data.edges[self.JOINS[1]].select = True
        bpy.context.active_object.data.edges[self.JOINS[3]].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.bridge_edge_loops()
        
        """Select all edges and extrude, then deselect
        TODO: Determine if more params needed for extrude method.
        """
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_region_move(
            TRANSFORM_OT_translate = {
                "value":(-0, self.d, 0)
            }
        )

        bpy.ops.mesh.select_all(action='DESELECT')        

def register():
    bpy.utils.register_class(MESH_OT_picture_frame_starter)
    
def unregister():
    bpy.utils.unregister_class(MESH_OT_picture_frame_starter)    
    
if __name__ == '__main__':
    register()
