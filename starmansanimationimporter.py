import bpy, json, os, base64, zlib
from pathlib import Path
from bpy.types import Operator
from bpy.types import Panel
from bpy.props import *

bl_info = {
    "name": "StarMan's Animation Importer",
    "author": "StarMan",
    "version": (1, 0),
    "blender": (3, 5, 0),
    "location": "SMAI 3D Tab",
    "category": "Animation"
}

def setDropdownFromMarkers(self, context):
    scene = bpy.context.scene
    markercurInd = 0
    newEnum = []
    
    for mkt in scene.smai_markers[scene.currentActionIndex].marktag:
        nInd = markercurInd
        data = (mkt.name, mkt.name, "a")
        newEnum.append(data)
        markercurInd += 1
    
    return newEnum
    
def stringIsInTable(str, tab):
    for stri in tab:
        if str == tab[stri]:
            return True
    return False
    
def onMarkerTagUpdate(self, value):
    scene = bpy.context.scene
    
    namesList = {}
    for mktag in scene.smai_markers[scene.currentActionIndex].marktag:
        if mktag != self:
            namesList[len(namesList)] = str(mktag.name)
    originalName = self.name
    newName = originalName
    
    if stringIsInTable(newName, namesList):
        gotIndex = False
        curInc = 1
        while gotIndex == False:
            newMarkerName = originalName+str(curInc)
            curInc += 1
            
            if stringIsInTable(newMarkerName, namesList) == False:
                newName = newMarkerName
                gotIndex = True
            
    self["name"] = str(newName)
    
class marker(bpy.types.PropertyGroup):
    time: IntProperty(name="")
    dropdown: EnumProperty(name = "", items = setDropdownFromMarkers)
    
class actionCheck(bpy.types.PropertyGroup):
    name: StringProperty(name="")
    value: BoolProperty(default=False)
    
class markerTag(bpy.types.PropertyGroup):
    name: StringProperty(name="", update=onMarkerTagUpdate)

class markerList(bpy.types.PropertyGroup):
    markfr: CollectionProperty(type = marker)
    action: PointerProperty(type=bpy.types.Action)
    marktag: CollectionProperty(type = markerTag)
    
class listAction(bpy.types.PropertyGroup):
    action:PointerProperty(type=bpy.types.Action)
    value:BoolProperty(name = "", default = False)
    start:IntProperty(name = "", default = 0)
    end:IntProperty(name = "", default = 0)
    
    indexName:StringProperty(name = "", default = "")
    
from mathutils import Matrix

class SMAI_OT_exportanim(Operator):
    bl_idname = "smai.exportanim"
    bl_label = "Export the current action animation."
    bl_description = "Copy export code"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = bpy.context.scene
        ob = bpy.context.object
        
        print(ob.name)
            
        Armature = None
        if ob.type == "ARMATURE":
            Armature = ob
        for m in ob.modifiers:
            if (m.type == 'ARMATURE') :
                Armature = m.object
                
        if Armature != None:
            self.report({'INFO'},
            "Copied export code.")
            
            fps = scene.render.fps
            print(fps)
            
            oldAction = Armature.animation_data.action
            
            finalList = {}
            
            for act in scene.currentActionsList:
                if act.value == True:
                    Armature.animation_data.action = bpy.data.actions[act.action.name]
                    
                    start_frame = act.start
                    end_frame = act.end
                
                    highList = {}
                    for f in range(start_frame, end_frame+1):
                        scene.frame_set(f)
                        scene.frame_set(f)
                        
                        bonesdataGot = {}
                        for bone in Armature.pose.bones:
                            if bone.parent is not None:
                                mat = (bone.parent.bone.matrix_local.inverted() @ bone.bone.matrix_local).inverted() @ (bone.parent.matrix.inverted() @ bone.matrix)
                            else:
                                mat = bone.bone.matrix_local.inverted() @ bone.matrix
                            
                            location, rotation,_ = mat.decompose()
                             
                            bonesdataGot[bone.name] = [
                                -location.x,
                                location.y,
                                -location.z,
                                -rotation.x,
                                rotation.y,
                                -rotation.z,
                                rotation.w
                                ]
                                
                        highList[f+1] = {'ps': bonesdataGot, 't': (f-start_frame)/fps}
                        
                    markerList = {}
                    if hasattr(scene, "smai_markers"):
                        for mI, m in scene.smai_markers[scene.currentActionIndex].markfr.items():
                            markerList[len(markerList)] = {"frame": m.time, "tag": m.dropdown}
                    
                    actionList = {"kf" : highList, "mk" : markerList, "n" : act.action.name}
                    
                    finalList[len(finalList)] = actionList
            ob.animation_data.action = oldAction
            
            finalList = finalList
            
            #print(finalList)
            encoded = json.dumps(finalList, separators=(',',':'))
            #bpy.context.window_manager.clipboard = encoded
            bpy.context.window_manager.clipboard = (base64.b64encode(zlib.compress(encoded.encode(), 9))).decode('utf-8')
        else:
            self.report({'ERROR'},
            "Select armature.")

        return {"FINISHED"}

class MARKER_UL_tags(bpy.types.UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        scene = bpy.context.scene
        ob = data
        mark = item
        mstr = mark.name
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            col = layout.column()
            row = layout.row()
            row.prop(mark, "name")
            #row.label(text= "Marker: ", translate=False)
            
            row1 = layout.row()
            #row1.scale_x = 3
            
            
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class MARKER_UL_frames(bpy.types.UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        scene = bpy.context.scene
        ob = data
        mark = item
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.row().separator()
            layout.row().separator()
            row = layout.row()
            
            row.prop(mark, "time")
            #row.label(text= "Marker: ", translate=False)
            
            row1 = layout.row()
            row1.prop(mark, "dropdown")
            row1.scale_x = 3
            
            
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)
            
def findActionIndex(action):
    scene = bpy.context.scene
    
    for markI, markO in enumerate(scene.smai_markers):
        if markO.action == action:
            return markI

            
class marker_tags_button(Operator):
    bl_idname = "smai.marker_tags_button"
    bl_label = "‎"
    
    button_type: StringProperty()
    description: StringProperty()
    
    def execute(self, context):
        scene = bpy.context.scene
        
        selectedIndex = scene.currentActionIndex
        button_type = self.button_type
        
        if button_type == "Add":
            mrkList = scene.smai_markers[selectedIndex].marktag
            mrk = mrkList.add()
            
            gotIndex = False
            curInc = 1
            while gotIndex == False:
                newMarkerName = "Marker"+str(curInc)
                curInc+=1
                if mrkList.get(newMarkerName) == None:
                    mrk.name:StringProperty()
                    mrk.name = newMarkerName
                    gotIndex = True
            
            
            mrk.time = scene.frame_current
                
        if button_type == "Remove":
            mrkList = scene.smai_markers[selectedIndex].marktag
            mrkList.remove(scene.active_smai_markertag)
            
            if scene.active_smai_markertag == len(mrkList):
                scene.active_smai_markertag = len(mrkList)-1
                
        return {"FINISHED"}
    
    @classmethod
    def description(cls, context, event):
        return getattr(context, "description")
    
             
class marker_button(Operator):
    bl_idname = "smai.marker_frames_button"
    bl_label = ""
    
    actionName:StringProperty()
    description:StringProperty()
    type: StringProperty()
    button_type: StringProperty()
    description: StringProperty()
    target: IntProperty()
    
    def execute(self, context):
        scene = bpy.context.scene
        
        selectedIndex = scene.currentActionIndex
        button_type = self.button_type
        type = self.type
        
        ## Acting as the frame related button
        if type == "Frames":    
            if button_type == "Add":
                mrkList = scene.smai_markers[selectedIndex].markfr
                mrk = mrkList.add()
                mrk.time = scene.frame_current
                    
            if button_type == "Remove":
                scene.smai_markers[selectedIndex].markfr.remove(self.target)
                #mrkList = scene.smai_markers[selectedIndex].markfr
                #mrkList.remove(scene.active_smai_markerframe)
                
                #if scene.active_smai_markerframe == len(mrkList):
                #    scene.active_smai_markerframe = len(mrkList)-1
                    
        ## Acting as the tags related button
        if type == "Tags":
            if button_type == "Add":
                mrkList = scene.smai_markers[selectedIndex].marktag
                mrk = mrkList.add()
                
                gotIndex = False
                curInc = 1
                while gotIndex == False:
                    newMarkerName = "Marker"+str(curInc)
                    curInc+=1
                    if mrkList.get(newMarkerName) == None:
                        mrk.name:StringProperty()
                        mrk.name = newMarkerName
                        gotIndex = True
                
                
                mrk.time = scene.frame_current
                    
            if button_type == "Remove":
                scene.smai_markers[selectedIndex].marktag.remove(self.target)
        return {"FINISHED"}
    
    @classmethod
    def description(cls, context, event):
        return getattr(event, "description")
    
class toggle_action(Operator):
    bl_idname = "smai.toggle_action"
    bl_label = ""
    
    actionInd:IntProperty()
    description:StringProperty()
    
    def execute(self, context):
        scene = bpy.context.scene
        
        actionData = scene.currentActionsList[self.actionInd]
        actionData.value = not actionData.value
        
        return {"FINISHED"}
    
    @classmethod
    def description(cls, context, event):
        return getattr(event, "description")

class exportActionsButton(Operator):
    bl_idname = "smai.export_actions_button"
    bl_label = ""
    bl_description = ""
    
    effect:StringProperty(name="")
    description:StringProperty()
    
    def execute(self, context):
        scene = bpy.context.scene
        
        if self.effect == "SelectAll":
            usedBool = False
            allSame = True
            
            for a, act in enumerate(scene.currentActionsList):
                
                if a == 0:
                    usedBool = act.value
                    
                if act.value != usedBool:
                    allSame = False
                    
                act.value = True
                
            if allSame:
                for act in scene.currentActionsList:
                    act.value = not usedBool
                    
        if self.effect == "SelectCurrent":
            playing = scene.currentActionIndex
            oldCurrent = scene.currentActionsList[playing].value
            
            for act in scene.currentActionsList:
                if act.name != playing:
                    act.value = oldCurrent
            scene.currentActionsList[playing].value = not oldCurrent
                
        
        return {"FINISHED"}
    
    @classmethod
    def description(cls, context, event):
        return getattr(event, "description")
    
class SMAI_miscButton(Operator):
    bl_idname = "smai.action_misc_button"
    bl_label = ""
    
    actionInd:IntProperty()
    description:StringProperty()
    effect:StringProperty()
    
    def execute(self, context):
        scene = bpy.context.scene

        if self.effect == "getStartEndNormal":
            act = scene.currentActionsList[self.actionInd]
            
            act.start = scene.frame_start
            act.end = scene.frame_end
            
            bpy.context.area.tag_redraw()
        
        return {"FINISHED"}
    
    @classmethod
    def description(cls, context, event):
        return getattr(event, "description")
    
class SMAI_PT_actionMisc(Panel):
    bl_label = ""
    bl_idname = "SMAI_PT_actionMisc"
    bl_options = {'INSTANCED'}
    bl_space_type = 'VIEW_3D' # 'PROPERTIES'
    bl_region_type = 'WINDOW'
    #bl_context = "object"

    def draw(self, context):
        layout = self.layout

        obj = context.object

        row = layout.row()
        row.label(text="Miscellaneous", icon='THREE_DOTS')

        row = layout.row()
        button = row.operator(SMAI_miscButton.bl_idname, text="Scene Start and End")
        button.actionName = context.my_string.name
        button.effect = "getStartEndNormal"

def loadPost(a):
    scene = bpy.context.scene
    
    bpy.types.Scene.currentActionsList = CollectionProperty(type=listAction)
    bpy.types.Scene.currentActionIndex = IntProperty()
    bpy.types.Scene.smai_markers = CollectionProperty(type = markerList)
    bpy.types.Scene.smai_oldAction = PointerProperty(type = bpy.types.Action)
    
    setActionIndexToCurrent()
    onActionChange(scene)
    bpy.app.handlers.depsgraph_update_post.append(onActionChange)
    

class SMAI_OT_load(Operator):
    bl_idname = "smai.load"
    bl_label = "Load Marker System"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        loadPost(None)
        return {"FINISHED"}

class SMAI_PT_sidebar(Panel):
    bl_label = "StarMan's Animation Importer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SMAI"
    
    stra : StringProperty(name="a", default="b")

    def draw(self, context):
        scene = bpy.context.scene
        col = self.layout.column(align=True)
        
        if hasattr(scene, "currentActionsList") == False or scene.currentActionsList == False:
            col.operator(SMAI_OT_load.bl_idname, text="Load System")
            return
        
        ob = bpy.context.object
        playingAction = None
        if hasattr(ob, "animation_data"):
            if hasattr(ob.animation_data, "action"):
                playingAction = ob.animation_data.action
        
        if hasattr(playingAction, "name"):
            playingAction = playingAction.name
        else:
            playingAction = None
        
        numberOfGotActs = 0
        for ac in scene.currentActionsList:
            if ac.value == True:
                numberOfGotActs += 1
        
        numberOfGotActs = numberOfGotActs < 2 and "Export Animation" or "Export Animations"
        col.operator(SMAI_OT_exportanim.bl_idname, text=numberOfGotActs, icon="COPYDOWN")
        selectedIndex = scene.currentActionIndex
        
        row1 = col.row()
        col.separator()
        #col.label(icon="REC", text=playingAction)
        #col.separator()
        currentActionIndex = scene.currentActionIndex
        
        if hasattr(scene, "smai_markers") and playingAction != None and len(scene.smai_markers) > 0:
            row2 = col.row()
            row2.label(text="Marker Tags:")
        
            if len(scene.smai_markers[currentActionIndex].marktag) != 0:
                mkTgFr = col.row()
                rowMarkersFrames = mkTgFr.column().box()
                rowMarkersFramesSide = mkTgFr.column()
                
                for actionI, action in enumerate(scene.smai_markers[currentActionIndex].marktag):
                    newRow = rowMarkersFrames.row()
                    
                    tFr = newRow.row(align=True)
                    tFr.prop(action, "name")
                    
                    removeMarker = newRow.operator(marker_button.bl_idname, icon="X")
                    removeMarker.type = "Tags"
                    removeMarker.button_type = "Remove"
                    removeMarker.description = "Remove selected marker"
                    removeMarker.target = actionI
                    
                    #boolButton = rmFr.operator(toggle_action.bl_idname, icon="X")
                addMarker = rowMarkersFramesSide.operator(marker_button.bl_idname, icon="PLUS")
                addMarker.type = "Tags"
                addMarker.button_type = "Add"
                addMarker.description = "Add a marker tag"
            else:
                mkTgFr = col.row()
                rowMarkersFrames = mkTgFr.column()
                rowMarkersFramesSide = mkTgFr.column()
                
                rowMarkersFrames.label(text="None")
            
                addMarker = rowMarkersFramesSide.operator(marker_button.bl_idname, icon="PLUS")
                addMarker.type = "Tags"
                addMarker.button_type = "Add"
                addMarker.description = "Add the first marker tag"
                
            row4 = col.row()
            row4.label(text="Marker Frames:")
             
            if len(scene.smai_markers[currentActionIndex].markfr) != 0:
                mkFrFr = col.row()
                rowMarkersFrames = mkFrFr.column().box()
                rowMarkersFramesSide = mkFrFr.column()
                for actionI, action in enumerate(scene.smai_markers[currentActionIndex].markfr):
                    newRow = rowMarkersFrames.row()
                    
                    tFr = newRow.row(align=True)
                    tFr.prop(action, "time")
                    tFr.prop(action, "dropdown")
                    
                    removeMarker = newRow.operator(marker_button.bl_idname, icon="X")
                    removeMarker.type = "Frames"
                    removeMarker.button_type = "Remove"
                    removeMarker.description = "Remove selected marker"
                    removeMarker.target = actionI
                    
                    #boolButton = rmFr.operator(toggle_action.bl_idname, icon="X")
                addMarker = rowMarkersFramesSide.operator(marker_button.bl_idname, icon="PLUS")
                addMarker.type = "Frames"
                addMarker.button_type = "Add"
                addMarker.description = "Add marker"
            else:
                mkTgFr = col.row()
                rowMarkersFrames = mkTgFr.column()
                rowMarkersFramesSide = mkTgFr.column()
                
                rowMarkersFrames.label(text="None")
            
                addMarker = rowMarkersFramesSide.operator(marker_button.bl_idname, icon="PLUS")
                addMarker.type = "Frames"
                addMarker.button_type = "Add"
                addMarker.description = "Adds the first marker frame"

        
        """
        row3 = col.row()
        row3.template_list("MARKER_UL_tags", "", scene.smai_markers[selectedIndex], "marktag", scene, "active_smai_markertag")
        
        col1 = row3.column()
        #col1.scale_x = 0.35
        #Add a marker tag
        addMarker = col1.operator(marker_button.bl_idname, icon="PLUS")
        addMarker.type = "Frames"
        addMarker.button_type = "Add"
        addMarker.description = "Add a marker tag"
        
        #Remove the selected marker tag
        removeMarker = col1.operator(marker_button.bl_idname, icon="X")
        removeMarker.type = "Frames"
        removeMarker.button_type = "Remove"
        removeMarker.description = "Remove selected marker tag"
        col.separator()
        """
        
        """
        row5 = col.row()
        row5.template_list("MARKER_UL_frames", "", scene.smai_markers[selectedIndex], "markfr", scene, "active_smai_markerframe")
        
        col1 = row5.column()
        col1.scale_x = 0.35
        #Add a marker to use with marker tags
        addMarker = col1.operator(marker_button.bl_idname, icon="PLUS")
        addMarker.type = "Tags"
        addMarker.button_type = "Add"
        addMarker.description = "Add a marker"
        
        #Remove the selected marker
        removeMarker = col1.operator(marker_button.bl_idname, icon="X")
        removeMarker.type = "Tags"
        removeMarker.button_type = "Remove"
        removeMarker.description = "Remove selected marker"""
        col.separator()
        
        row6 = col.row()
        row6.label(text="Exported Actions:")
        
        col1 = row6.column()
        col1.scale_x = 0.7
        selectAll = col1.operator(exportActionsButton.bl_idname, text="All", icon="LIGHTPROBE_GRID")
        selectAll.effect = "SelectAll"
        selectAll.description = "Toggle all actions"
        
        col2 = row6.column()
        col2.scale_x = 0.8
        selectCurrent = col2.operator(exportActionsButton.bl_idname, text="Current", icon="DECORATE_KEYFRAME")
        selectCurrent.effect = "SelectCurrent"
        selectCurrent.description = "Toggle current action"
        
        row7 = col.box()
        for actionIndex, action in enumerate(scene.currentActionsList):
            if hasattr(action, "action") == True:
                actionName = action.action.name
                
                newRow = row7.row(align=True)
                newRow.scale_x = 0.5
                
                forLabelRow = newRow
                if actionName == playingAction:
                    plIc = newRow.row()
                    forLabelRow = plIc
                    
                    plIc.label(icon="RADIOBUT_ON")
                    plIc.scale_x = 0.6
                    plIc.separator()
                
                forLabelRow.label(text=actionName)
                
                #gotValue = actionData["value"]
                newIcon = action.value == True and "RADIOBUT_ON" or "RADIOBUT_OFF"
                
                newRow = newRow.row(align=True)
                newRow.label(icon="PREVIEW_RANGE")
                newRow.separator()
                newRow.separator()
                newRow.separator()
                newRow.separator()
                newRow.prop(action, "start")
                
                newRow.prop(action, "end")
                newRow.separator()
                newRow = newRow.row(align=True)
                newRow.scale_x = 1.5
                
                boolButton = newRow.operator(toggle_action.bl_idname, icon=newIcon)
                boolButton.actionInd = actionIndex
                boolButton.description = "Toggle if exported"
                
                newRow.context_pointer_set("my_string", scene.currentActionsList[currentActionIndex])
                misc = newRow.operator(SMAI_miscButton.bl_idname, icon = "DRIVER_DISTANCE")
                misc.actionInd = actionIndex
                misc.effect = "getStartEndNormal"
                misc.description = "Set start and end to scene's"
                #misc = newRow.popover(SMAI_PT_actionMisc.bl_idname, icon = "THREE_DOTS")
                

class savedMarkers(bpy.types.PropertyGroup):
    coll : CollectionProperty(type = markerList)#CollectionProperty(type = bpy.types.PropertyGroup)

def save_storedData(self, context):
    #print(bpy.context.scene["currentActionsList"])
    scene = bpy.context.scene
    
    """
    #if scene["currentActionsListSaved"] is not None:
        #print("a")
    bpy.types.Scene.currentActionsListSaved = CollectionProperty(type=listAction)
    
    if scene["currentActionsList"] is not None:
         print(scene.currentActionsList[1].name)
    scene.currentActionsListSaved.clear()
    
    if scene["currentActionsList"] is not None:
        for inst in scene["currentActionsList"]:
            new = scene.currentActionsListSaved.add()
            
            for p in inst:
                setattr(new, p, inst[p])
                
        p#rint(scene.currentActionsListSaved[1].name)
    scene = bpy.context.scene
    if hasattr(scene, "smai_markers"):
        scene.smai_storedMarkers.coll.clear()
        bpy.types.Scene.smai_storedMarkers = PointerProperty(type=savedMarkers)
        
        for col in scene.smai_markers:
            added = scene.smai_storedMarkers.coll.add()
            added = col
            
            added.action = col.action
            
            # Post Fixes
            #print(added.action)
            
        for coli, col in enumerate(scene.smai_storedMarkers.coll):
            print(col.markfr.time)
    """
        

def load_storedData():
    scene = bpy.context.scene
    
    pkg = scene["smai_storedMarkers"].coll
    scene.smai_markers = pkg

def setActionIndexToCurrent():
    scene = bpy.context.scene
    
    ob = bpy.context.object
    if hasattr(ob, "animation_data") and hasattr(ob.animation_data, "action"):
        playingAction = ob.animation_data.action
        
        playingAnimIndex = findActionIndex(playingAction)
        scene.currentActionIndex = playingAnimIndex or 0

def onActionChange(scene):
    scene = bpy.context.scene
    ob = bpy.context.object
    
    if not hasattr(ob, "animation_data") or not hasattr(ob.animation_data, "action"):
        return
    
    newAction = ob.animation_data.action
    
    oldInList = {}
    for a, b in enumerate(scene.currentActionsList):
        if hasattr(b, "action"):
            oldInList[b.action] = True
    
    for a in bpy.data.actions:
        got = False
        for act in scene.currentActionsList:
            if act.action == a:
                got = True
        if got == False:
            print("b")
            newActList = scene.currentActionsList.add()
            newActList.action = a
            #newActList.name = a.name
            
            newMark = scene.smai_markers.add()
            newMark.action = a
            #newMark.name = a.name
            
            oldInList[a] = None
        
    for actOg in oldInList:
        if oldInList[actOg] == True:
            for actI, act in enumerate(scene.currentActionsList):
                if act == actOg:
                    scene.currentActionsList.remove(actI)
            
            for actI, act in enumerate(scene.smai_markers):
                if act == actOg:
                    scene.smai_markers.remove(actI)
    
    if newAction != scene.smai_oldAction:
        scene.smai_oldAction = newAction
        setActionIndexToCurrent()

classes = [
    markerTag,
    marker,
    markerList,
    listAction,
    
    MARKER_UL_frames,
    MARKER_UL_tags,
    
    marker_button,
    
    toggle_action,
    exportActionsButton,
    SMAI_PT_actionMisc,
    SMAI_miscButton,
    SMAI_PT_sidebar,
    SMAI_OT_exportanim,
    SMAI_OT_load,
    
    savedMarkers,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)

    
def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    
    bpy.app.handlers.depsgraph_update_post.remove(onActionChange)

def preload(scene, a):
    bpy.types.Scene.currentActionsList = False
    bpy.types.Scene.currentActionIndex = False
    bpy.types.Scene.smai_markers = False
    bpy.types.Scene.smai_oldAction = None
bpy.app.handlers.load_pre.append(preload)

if __name__ == "__main__":
    register()