import bpy
import json
import math
import os

# [
#     {
#         "model": "tinyllama",
#         "api_type": "ollama"
#     }
# ]
# [
#     {
#         "model": "gpt-4-turbo",
#         "api_key": "58d0bacc761d4678855f9582819abcc77a4bacaa54984213905d9d546670638a",
#         "base_url": "https://gpt-api.hkust-gz.edu.cn/v1/chat/completions"
#     }
# ]
object_name = 'Cube'
object_to_delete = bpy.data.objects.get(object_name)

# Check if the object exists before trying to delete it
if object_to_delete is not None:
    bpy.data.objects.remove(object_to_delete, do_unlink=True)

def import_glb(file_path, object_name):
    bpy.ops.import_scene.gltf(filepath=file_path)
    imported_object = bpy.context.view_layer.objects.active
    if imported_object is not None:
        imported_object.name = object_name

def create_room(width, depth, height):
    # Create floor
    # bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0))

    # # Extrude to create walls
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0, 0, height)})
    # bpy.ops.object.mode_set(mode='OBJECT')

    # # Scale the walls to the desired dimensions
    # bpy.ops.transform.resize(value=(width, depth, 1))

    # bpy.context.active_object.location.x += width / 2
    # bpy.context.active_object.location.y += depth / 2
    bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    
    # 创建墙壁
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, height)})
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 缩放墙壁到所需尺寸
    bpy.ops.transform.resize(value=(width, depth, 1))
    
    # 将墙壁位置调整到中心
    bpy.context.active_object.location.x += width / 2
    bpy.context.active_object.location.y += depth / 2

    # 创建两种材质：半透明墙壁和全透明天花板
    wall_material = bpy.data.materials.new(name="TransparentWallMaterial")
    ceiling_material = bpy.data.materials.new(name="TransparentCeilingMaterial")
    wall_material.use_nodes = True
    ceiling_material.use_nodes = True

    # 设置墙壁材质（30%透明度）
    wall_bsdf = wall_material.node_tree.nodes.get("Principled BSDF")
    wall_bsdf.inputs['Alpha'].default_value = 0.8

    # 设置天花板材质（100%透明）
    ceiling_bsdf = ceiling_material.node_tree.nodes.get("Principled BSDF")
    ceiling_bsdf.inputs['Alpha'].default_value = 0.0

    # 将材质赋给物体
    obj = bpy.context.active_object
    if len(obj.data.materials) == 0:
        obj.data.materials.append(wall_material)
        obj.data.materials.append(ceiling_material)
    
    # 在编辑模式下选择天花板面并赋予全透明材质
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 选择最上面的面（天花板）
    for poly in obj.data.polygons:
        if poly.center[2] > height/2:  # 如果面的中心点在上半部分
            poly.material_index = 1  # 使用第二个材质（全透明）
    
    # 设置两种材质的混合方法
    wall_material.blend_method = 'BLEND'
    ceiling_material.blend_method = 'BLEND'

def find_glb_files(directory):
    glb_files = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".glb"):
                key = file.split(".")[0]
                if key not in glb_files:
                    glb_files[key] = os.path.join(root, file)
    return glb_files

def get_highest_parent_objects():
    highest_parent_objects = []

    for obj in bpy.data.objects:
        # Check if the object has no parent
        if obj.parent is None:
            highest_parent_objects.append(obj)
    return highest_parent_objects

def delete_empty_objects():
    # Iterate through all objects in the scene
    for obj in bpy.context.scene.objects:
        # Check if the object is empty (has no geometry)
        print(obj.name, obj.type)
        if obj.type == 'EMPTY':
            bpy.context.view_layer.objects.active = obj
            bpy.data.objects.remove(obj)

def select_meshes_under_empty(empty_object_name):
    # Get the empty object
    empty_object = bpy.data.objects.get(empty_object_name)
    print(empty_object is not None)
    if empty_object is not None and empty_object.type == 'EMPTY':
        # Iterate through the children of the empty object
        for child in empty_object.children:
            # Check if the child is a mesh
            if child.type == 'MESH':
                # Select the mesh
                child.select_set(True)
                bpy.context.view_layer.objects.active = child
            else:
                select_meshes_under_empty(child.name)
def add_text_label(obj, text, obj_rotation):
    # 创建文本对象
    bpy.ops.object.text_add(location=(0, 0, 0))
    text_obj = bpy.context.active_object
    
    # 将文本分成两行（每行最多8个字符）
    words = text.split('-')
    if len(words) > 1:
        text_obj.data.body = f"{words[0]}\n{'-'.join(words[1:])}"
    else:
        text_obj.data.body = text
    
    # 设置文本大小和对齐方式
    text_obj.data.size = 0.12  # 缩小字号
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'
    
    # 获取物体的尺寸和旋转角度
    obj_dims = obj.dimensions
    
    # 计算偏移位置（考虑旋转）
    offset_distance = obj_dims.y * 0.5  # 只使用物体尺寸的30%
    offset_x = -offset_distance * math.sin(obj_rotation)
    offset_y = -offset_distance * math.cos(obj_rotation)
    
    text_obj.location = (
        obj.location.x,
        obj.location.y,
        obj.location.z + obj_dims.z / 2 + 0.05
    )
    
    # 设置文本的旋转与物体相同
    # text_obj.rotation_euler.z = obj_rotation
    # 创建文本材质（白色）
    text_material = bpy.data.materials.new(name="TextMaterial")
    text_material.use_nodes = True
    text_material.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (1, 0.55, 0, 1)  # 白色
    text_obj.data.materials.append(text_material)
    
    return text_obj
def rescale_object(obj, scale):
    # Ensure the object has a mesh data
    if obj.type == 'MESH':
        bbox_dimensions = obj.dimensions
        scale_factors = (
                         scale["length"] / bbox_dimensions.x, 
                         scale["width"] / bbox_dimensions.y, 
                         scale["height"] / bbox_dimensions.z
                        )
        obj.scale = scale_factors
    else:
        print(obj.name, obj.type)

objects_in_room = {}
scene_number = 5 # TODO
file_path = f"scene_graph/scene_graph{scene_number}.json"
with open(file_path, 'r') as file:
    data = json.load(file)
    for item in data:
        if item["new_object_id"] not in ["south_wall", "north_wall", "east_wall", "west_wall", "middle of the room", "ceiling"]:
            objects_in_room[item["new_object_id"]] = item

directory_path = os.path.join(os.getcwd(), "Assets")
glb_file_paths = find_glb_files(directory_path)

for item_id, object_in_room in objects_in_room.items():
    glb_file_path = os.path.join(directory_path, glb_file_paths[item_id])
    import_glb(glb_file_path, item_id)

parents = get_highest_parent_objects()
empty_parents = [parent for parent in parents if parent.type == "EMPTY"]

for empty_parent in empty_parents:
    bpy.ops.object.select_all(action='DESELECT')
    select_meshes_under_empty(empty_parent.name)
    
    bpy.ops.object.join()
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    
    joined_object = bpy.context.view_layer.objects.active
    if joined_object is not None:
        joined_object.name = empty_parent.name + "-joined"

bpy.context.view_layer.objects.active = None

MSH_OBJS = [m for m in bpy.context.scene.objects if m.type == 'MESH']
for OBJS in MSH_OBJS:
    bpy.context.view_layer.objects.active = OBJS
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    OBJS.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.objects.active = OBJS
    OBJS.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

# 在主代码中添加一个计数器
object_counter = 1

MSH_OBJS = [m for m in bpy.context.scene.objects if m.type == 'MESH']
for OBJS in MSH_OBJS:
    if OBJS.name.split("-")[0] not in ["south_wall", "north_wall", "east_wall", "west_wall", "middle of the room", "ceiling"]:
        print(OBJS.name)
        item = objects_in_room[OBJS.name.split("-")[0]]
        object_position = (item["position"]["x"], item["position"]["y"], item["position"]["z"])
        object_rotation_z = (item["rotation"]["z_angle"] / 180.0) * math.pi + math.pi
        
        bpy.ops.object.select_all(action='DESELECT')
        OBJS.select_set(True)
        OBJS.location = object_position
        # ov=bpy.context.copy()
        # ov['area']=[a for a in bpy.context.screen.areas if a.type=="VIEW_3D"][0]
        # bpy.ops.transform.rotate(ov, value=math.radians(object_rotation_z), orient_axis='Z')
        bpy.ops.transform.rotate(value=object_rotation_z, orient_axis='Z')
        rescale_object(OBJS, item["size_in_meters"])

        # 添加编号标签
        # add_text_label(OBJS, str(object_counter), object_rotation_z)
        object_counter += 1  # 增加计数器

bpy.ops.object.select_all(action='DESELECT')
delete_empty_objects()

# TODO: Generate the room with the room dimensions


def export_scene(output_path):

    # 确保所有对象都被选中  
    bpy.ops.object.select_all(action='SELECT')
    
    # 更详细的导出设置
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        use_selection=True,  # 只导出选中的对象
        export_apply=True,   # 应用所有变换
        export_materials=True,  # 导出材质
        export_colors=True,
        export_extras=True,
        export_yup=True,     # 使用 Y-up 坐标系
        will_save_settings=True
    )
    
    print(f"Scene exported to: {output_path}")

# 在导出之前确保所有变换都被应用
def prepare_for_export():
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            # 选择对象
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            
            # 应用所有变换
            bpy.ops.object.transform_apply(
                location=True, 
                rotation=True, 
                scale=True
            )



def setup_top_camera(room_width, room_depth, room_height):
    # 创建相机
    bpy.ops.object.camera_add(location=(room_width / 2, room_depth / 2, room_height + 2))  # 位置在房间上方中心
    camera = bpy.context.active_object
    
    # 设置相机朝向（看向房间中心）
    camera.rotation_euler = (0, 0, 0)  # 相机朝下
    
    # 设置相机为当前场景的活动相机
    bpy.context.scene.camera = camera
    
    # 设置正交模式（更适合俯视图）
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 8  # 调整视野范围
    
    # 设置渲染参数
    bpy.context.scene.render.engine = 'CYCLES'  # 使用 Cycles 渲染引擎
    bpy.context.scene.render.film_transparent = True  # 透明背景
    bpy.context.scene.render.resolution_x = 1920  # 设置分辨率
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.resolution_percentage = 100

def render_scene(output_dir, scene_num):
    # 设置输出路径
    output_path = os.path.join(output_dir, f'render_result{scene_num}.png')
    bpy.context.scene.render.filepath = output_path
    
    # 渲染场景
    bpy.ops.render.render(write_still=True)
    print(f"Scene rendered to: {output_path}")
def add_compass(room_width, room_depth):
    # 计算房间中心点
    center_x = room_width / 2
    center_y = room_depth / 2
    height = 2.45  # 天花板高度
    
    # 创建十字的两条线（使用细长的立方体）
    # 南北方向（Y轴）
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(center_x, center_y, height)
    )
    ns_line = bpy.context.active_object
    ns_line.scale = (0.03, 0.3, 0.01)  # 细长的立方体
    
    # 东西方向（X轴）
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(center_x, center_y, height)
    )
    ew_line = bpy.context.active_object
    ew_line.scale = (0.3, 0.03, 0.01)  # 细长的立方体
    
    # 添加方向文字
    directions = {
        'N': (0, 0.2, 0),
        'E': (0.2, 0, 0),
        'S': (0, -0.2, 0),
        'W': (-0.2, 0, 0)
    }
    
    for direction, offset in directions.items():
        bpy.ops.object.text_add(location=(
            center_x + offset[0],
            center_y + offset[1],
            height
        ))
        text = bpy.context.active_object
        text.data.body = direction
        text.data.size = 0.1
        text.data.align_x = 'CENTER'
        text.data.align_y = 'CENTER'
        
        # 黑色材质
        text_mat = bpy.data.materials.new(name=f"Text_{direction}")
        text_mat.use_nodes = True
        text_mat.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (1, 1, 0, 1)
        text.data.materials.append(text_mat)
    
    # 为十字线添加黑色材质
    line_mat = bpy.data.materials.new(name="Compass_Lines")
    line_mat.use_nodes = True
    line_mat.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (1, 1, 0, 1)
    
    for line in [ns_line, ew_line]:
        line.data.materials.append(line_mat)

def add_area_light(room_width, room_depth, room_height):
    """
    添加一个覆盖整个房间的平面光源
    """
    # 创建平面光源
    bpy.ops.object.light_add(type='AREA', location=(room_width/2, room_depth/2, room_height))
    light = bpy.context.active_object
    
    # 设置光源大小为房间大小
    light.data.size = room_width
    light.data.size_y = room_depth
    
    # 设置光源朝向（向下）
    light.rotation_euler = (0, 0, 0)
    
    # 设置光源强度和颜色
    light.data.energy = 150  # 光源强度
    light.data.color = (1.0, 1.0, 1.0)  # 白色光
    
    # 设置阴影
    light.data.use_shadow = False
    # light.data.shadow_soft_size = 0.5  # 软阴影大小
    
    print(f"添加了平面光源，大小: {room_width}x{room_depth}，高度: {room_height}")
    
    return light

def setup_multiple_cameras(room_width, room_depth, room_height):
    # 创建一个空物体作为相机目标点
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(2, 2, 1))
    target = bpy.context.active_object
    target.name = "CameraTarget"
    
    # 创建第一个相机 (0,0,2)
    bpy.ops.object.camera_add(location=(0, 0, 2))
    camera1 = bpy.context.active_object
    camera1.name = "Camera_Corner"
    
    # 创建第二个相机 (4,4,2)
    bpy.ops.object.camera_add(location=(3.5, 4.5, 2))
    camera2 = bpy.context.active_object
    camera2.name = "Camera_FarCorner"
    
    # 为两个相机设置"跟踪到"约束，使它们指向目标点
    for camera in [camera1, camera2]:
        constraint = camera.constraints.new('TRACK_TO')
        constraint.target = target
        constraint.track_axis = 'TRACK_NEGATIVE_Z'  # 相机的-Z轴指向目标
        constraint.up_axis = 'UP_Y'  # Y轴向上
        
        # 设置相机参数
        camera.data.type = 'ORTHO'
        camera.data.lens = 28  # 稍微广角
    
    # 设置渲染参数
    bpy.context.scene.render.engine = 'CYCLES'  # 使用 Cycles 渲染引擎
    bpy.context.scene.render.film_transparent = True  # 透明背景
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.resolution_percentage = 100
    
    return [camera1, camera2]

def render_from_cameras(cameras, output_dir, scene_num):
    original_camera = bpy.context.scene.camera
    
    for i, camera in enumerate(cameras):
        # 设置当前相机为渲染相机
        bpy.context.scene.camera = camera
        
        # 设置输出路径
        output_path = f"{output_dir}/{scene_num}_render_camera_{i+1}.png"
        bpy.context.scene.render.filepath = output_path
        
        # 渲染图像
        bpy.ops.render.render(write_still=True)
        
        print(f"已渲染相机 {camera.name} 的视图到 {output_path}")
    
    # 恢复原始相机
    bpy.context.scene.camera = original_camera

room_size = [3.5, 4.5, 2.4]
create_room(room_size[0], room_size[1], room_size[2])
# 在主代码中调用（在创建房间后）
# add_compass(4.0, 4.0)  # width 和 depth 是房间的宽度和深度
# 在主代码最后添加：
setup_top_camera(room_size[0], room_size[1], room_size[2])
add_area_light(room_size[0], room_size[1], room_size[2])

# 修改: 使用room_size中的元素而不是未定义的变量
cameras = setup_multiple_cameras(room_size[0], room_size[1], room_size[2])

# 确保输出目录存在
output_dir = "/remote-home/mingzesun/workspace/FractFlow/IDesign/render"  # 相对于.blend文件的路径
os.makedirs(bpy.path.abspath(output_dir), exist_ok=True)

# 首先渲染俯视图
# bpy.context.scene.render.filepath = f"{output_dir}/render_top_view.png"
# bpy.ops.render.render(write_still=True)

# 然后从两个角落相机渲染
render_from_cameras(cameras, output_dir, scene_number)

print("所有视图渲染完成！")
render_scene(output_dir, scene_number)

# 在主代码最后
prepare_for_export()
export_scene(f"/remote-home/mingzesun/workspace/FractFlow/IDesign/scene/scene_result{scene_number}.glb")

    # 设置两个角落相机并渲染
