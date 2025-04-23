import asyncio
import os
import json
import copy
from dotenv import load_dotenv
from FractFlow.agent import Agent
import re
import time

from schemas import layout_corrector_schema, layout_refiner_schema
from utils import get_room_priors, extract_list_from_json
from utils import preprocess_scene_graph, build_graph, remove_unnecessary_edges, handle_under_prepositions, get_conflicts, get_size_conflicts, get_object_from_scene_graph
from utils import get_object_from_scene_graph, get_rotation, get_cluster_objects, clean_and_extract_edges
from utils import get_cluster_size
from utils import get_possible_positions, is_point_bbox, calculate_overlap, get_topological_ordering, place_object, get_depth, get_visualization
from jsonschema import validate

def json_schema_debugger_corrector(json_data):
    message = json_data

    preps_layout = ["left-side", "right-side", "in the middle"]
    preps_objs = ['on', 'left of', 'right of', 'in front', 'behind', 'under', 'above']

    pattern = r'```json\s*([^`]+)\s*```' # Match the json object
    match = re.search(pattern, message, re.DOTALL)
    if match:
        return match.group(1)
    else:
        match = message
    json_obj_new = json.loads(match)
    is_success  = False
    try:
        validate(instance=json_obj_new, schema=layout_corrector_schema)
        is_success = True
    except Exception as e:
        feedback = str(e.message)
        if e.validator == "enum":
            if str(preps_objs) in e.message:
                feedback += f"Change the preposition {e.instance} to something suitable with the intended positioning from the list {preps_objs}"
            elif str(preps_layout) in e.message:
                feedback += f"Change the preposition {e.instance} to something suitable with the intended positioning from the list {preps_layout}"
    if is_success:
        return "SUCCESS"
    return feedback
def json_schema_debugger_refiner(json_data):
    message = json_data

    preps_layout = ["left-side", "right-side", "in the middle"]
    preps_objs = ['on', 'left of', 'right of', 'in front', 'behind', 'under', 'above']

    json_obj_new = json.loads(message)
    if "items" in json_obj_new["children_objects"]:
        json_obj_new = {"children_objects" : json_obj_new["children_objects"]["items"]}
    is_success  = False
    try:
        validate(instance=json_obj_new, schema=layout_refiner_schema)
        is_success = True
    except Exception as e:
        feedback = str(e.message)
        if e.validator == "enum":
            if str(preps_objs) in e.message:
                feedback += f"Change the preposition {e.instance} to something suitable with the intended positioning from the list {preps_objs}"
            elif str(preps_layout) in e.message:
                feedback += f"Change the preposition {e.instance} to something suitable with the intended positioning from the list {preps_layout}"
    if is_success:
        return "SUCCESS"
    return feedback


async def main(room_dimensions, user_preference):
    print(room_dimensions)
    time.sleep(5)
    # 创建两个agent
    room_priors = get_room_priors(room_dimensions)
    corrector = Agent(name='corrector')
    refiner = Agent(name='refiner')
    
    # 复制配置
    config_corrector = copy.deepcopy(corrector.get_config())
    config_refiner = copy.deepcopy(refiner.get_config())
    
    # 设置API提供商和模型
    for config in [config_corrector, config_refiner]:
        config['agent']['provider'] = 'deepseek' # This is a little bit hack. 
        config['deepseek']['model'] = 'gpt-4o-2024-08-06' # 'DeepSeek-R1-671B' # "qwen-max-2025-01-25"
        config['deepseek']['base_url'] = 'https://gpt-api.hkust-gz.edu.cn/v1' # "https://dashscope.aliyuncs.com/compatible-mode/v1"
        config['deepseek']['api_key'] = 'Bearer 58d0bacc761d4678855f9582819abcc77a4bacaa54984213905d9d546670638a' # 'sk-d770b774f1aa42a2b17fecbd08bd0362'
        config['agent']['max_iterations'] = 10
    
    # 设置各自的系统提示
    config_corrector['agent']['custom_system_prompt'] = f"""
        Spatial Corrector Agent. Let's think step by step. Whenever a user provides an object that don't fit the room for various spatial conflicts,
        You are going to make changes to its "scene_graph" and "facing_object" keys so that these conflicts are removed. 
        You are going to use the JSON Schema to validate the JSON object that the user provides.

        For relative placement with other objects in the room use the prepositions "on", "left of", "right of", "in front", "behind", "under".
        For relative placement with the room layout elements (walls, the middle of the room, ceiling) use the prepositions "on", "in the corner".

        Use only the following JSON Schema to save the JSON object:
        {layout_corrector_schema}
        true or false should be written in lowercase.
        """
    
    config_refiner['agent']['custom_system_prompt'] = """ Layout Refiner. Every time when the Admin speaks; you will look at the parent object and children objects, the first  
        preposition that connects these objects and find a second suitable relative placement for the children objects whilst considering the initial positioning of the object. 
        Give the relative placement of the children objects with each other and with the parent object! For example, if there are five children objects that are 'on' the parent
        object, give the relative positions of the children objects to one another and the second preposition to the the parent object ('on' is the first preposition).

        Use only the following JSON Schema to save the JSON object:
        {
            "children_objects" : {
                "type" : "array",
                "items" : {
                    "type" : "object",
                    "properties" : {
                        "name_id" : {
                            "type" : "string"
                        },
                        "placement" : {
                            "type" : "object",
                            "properties" : {
                                "children_objects" : {
                                    "type" : "array",
                                    "items" : {
                                        "type" : "object",
                                        "properties" : {
                                            "name_id" : {
                                                "type" : "string",
                                                "description" : "The name_id of the other child object"
                                            },
                                            "preposition" : {
                                                "type" : "string",
                                                "description" : "The preposition that connects this object and the connected object, ex. left of the desk, behind the plant, the rug is under the desk...",
                                                "enum" : ["on", "left of", "right of", "in front", "behind", "under", "above"]
                                            },
                                            "is_adjacent" : {
                                                "type" : "boolean",
                                                "description" : "Whether this object and the connected object are adjacent to each other, ex. an object on the desk is adjacent to the desk."
                                            }
                                        },
                                        "required" : ["name_id", "preposition", "is_adjacent"]
                                    }
                                }
                            },
                            "required" : ["children_objects"]
                        }
                    },
                    "required" : ["name_id", "placement"]
                }
            },
        }
        """
    
# 读取scene_graph_after_engineer.json
    with open('scene_graph_after_engineer.json', 'r') as f:
        scene_graph = json.load(f)
        
    print("成功读取场景图JSON")
    
    # 设置配置并初始化agents
    corrector.set_config(config_corrector)
    await corrector.initialize()
    sg = scene_graph
    scene_graph = preprocess_scene_graph(scene_graph["objects_in_room"])
    G = build_graph(scene_graph)
    G = remove_unnecessary_edges(G)
    G, scene_graph = handle_under_prepositions(G, scene_graph)

    conflicts = get_conflicts(G, scene_graph)

    verbose = True
    if verbose:
        print("-------------------CONFLICTS-------------------")
        for conflict in conflicts:
            print(conflict)
            print("\n\n")
    print(len(conflicts))
    print("\n")
    while len(conflicts) > 0:
        corrector_input = f"""
            {conflicts[0]}
            """
        while True:
            correction = await corrector.process_query(corrector_input)
            print("Corrector结果: ", correction)
            pattern = r'```json\s*([^`]+)\s*```' # Match the json object
            match = re.search(pattern, correction, re.DOTALL)
            if match:
                json_content = match.group(1)
            else:
                json_content = correction  # 使用原始内容

            check = json_schema_debugger_corrector(json_content)
            print(check)
            if check == 'SUCCESS':
                break
            else:
                corrector_input = check

        correction_json = json.loads(json_content)
        corr_obj = get_object_from_scene_graph(correction_json["corrected_object"]["new_object_id"], scene_graph)
        corr_obj["is_on_the_floor"] = correction_json["corrected_object"]["is_on_the_floor"]
        corr_obj["facing"] = correction_json["corrected_object"]["facing"]
        corr_obj["placement"] = correction_json["corrected_object"]["placement"]
        G = build_graph(scene_graph)
        conflicts = get_conflicts(G, scene_graph)

    sg["objects_in_room"] = scene_graph
    with open('scene_graph_after_corrector.json', 'w') as f:
        json.dump(sg, f, indent=4)
    with open('scene_graph_after_corrector.json', 'r') as f:
        scene_graph = json.load(f)
    cluster_dict = get_cluster_objects(scene_graph["objects_in_room"])
    # cluster 是指只和某一个对象有关系的集合
    inputs = []
    for key, value in cluster_dict.items():
        key = list(key)
        if len(key[0]) == 2:
            parent_id = key[0][0][1]
            prep = key[0][1][1]
        elif len(key[0]) == 3:
            parent_id = key[0][1][1]
            prep = key[0][2][1]
        objs = value

        inputs.append((parent_id, prep, objs))

    # if verbose:
    #     if inputs == []:
    #         print("No clusters found")
    #     for parent_id, prep, objs in inputs:
    #         print(f"Parent Object : {parent_id}")
    #         print(f"Children Objects : {objs}")
    #         print(f"The children objects are '{prep}' the parent object")
    #         print("\n")
    # breakpoint()
    for parent_id, prep, obj_names in inputs:
        objs = [get_object_from_scene_graph(obj, scene_graph["objects_in_room"]) for obj in obj_names]
        objs_rot = [get_rotation(obj, scene_graph["objects_in_room"]) for obj in objs]

        parent_obj = get_object_from_scene_graph(parent_id, scene_graph["objects_in_room"])
        if parent_obj is None:
            parent_obj = [prior for prior in room_priors if prior.get("new_object_id") == parent_id][0]
        parent_obj_rot = get_rotation(parent_obj, scene_graph["objects_in_room"])

        rot_diffs = [obj_rot - parent_obj_rot for obj_rot in objs_rot]
        direction_check = lambda diff, prep: (diff % 180 == 0 and prep in ["left of", "right of"]) or (diff % 180 != 0 and prep in ["in front", "behind"]) or (diff % 180 != 0 and prep == "on")
        possibilities_str = "Constraints:\n" + '\n'.join(["\t" + f"Place objects {'`behind` or `in front`' if direction_check(diff, prep) else '`left of` or `right of`'} of {name}!" for name, diff in zip(obj_names, rot_diffs)])

        refiner.set_config(config_refiner)
        await refiner.initialize()

        refiner_input = f"""
            Parent Object : {parent_id}
            Children Objects : {obj_names}

            {possibilities_str}

            The children objects are '{prep}' the parent object
            """
        while True:

            new_relationships = await refiner.process_query(refiner_input)
            print("refiner结果: ", new_relationships)
            pattern = r'```json\s*([^`]+)\s*```' # Match the json object
            match = re.search(pattern, new_relationships, re.DOTALL)
            if match:
                json_content = match.group(1)
            else:
                json_content = new_relationships  # 使用原始内容

            check = json_schema_debugger_refiner(json_content)
            print(check)
            if check == 'SUCCESS':
                break
            else:
                refiner_input = check
        new_relationships = json.loads(json_content)
        if "items" in new_relationships["children_objects"]:
            new_relationships = {"children_objects" : new_relationships["children_objects"]["items"]}
        # Check whether the relationships are valid
        invalid_name_ids = []
        for child in new_relationships["children_objects"]:
            for other_child in child["placement"]["children_objects"]:
                
                other_child_rot = get_rotation(get_object_from_scene_graph(other_child["name_id"], scene_graph["objects_in_room"]), scene_graph["objects_in_room"])
                if direction_check(other_child_rot - parent_obj_rot, prep) and other_child["preposition"] not in ["in front", "behind"]:
                    invalid_name_ids.append(child["name_id"])
                elif not direction_check(other_child_rot - parent_obj_rot, prep) and other_child["preposition"] not in ["left of", "right of"]:
                    invalid_name_ids.append(child["name_id"])

        if verbose:
            print("Invalid name IDs: ", invalid_name_ids)
        new_relationships["children_objects"] = [child for child in new_relationships["children_objects"] if child["name_id"] not in invalid_name_ids]         
        
        if len(new_relationships["children_objects"]) == 0:
            continue

        edges, edges_to_flip = clean_and_extract_edges(new_relationships, parent_id, verbose=verbose)

        prep_correspondences ={
            "left of" : "right of",
            "right of" : "left of",
            "in front" : "behind",
            "behind" : "in front",
        }


        for obj in new_relationships["children_objects"]:
            name_id = obj["name_id"]
            rel = obj["placement"]["children_objects"]
            for r in rel:
                if (name_id, r["name_id"]) in edges:
                    to_flip = edges_to_flip[(name_id, r["name_id"])]
                    if to_flip:
                        corr_obj = get_object_from_scene_graph(r["name_id"], scene_graph["objects_in_room"])
                        corr_prep = prep_correspondences[r["preposition"]]
                        corr_obj["placement"]["objects_in_room"].append({"object_id" : name_id, "preposition" : corr_prep, "is_adjacent" : r["is_adjacent"]})
                    else:
                        corr_obj = get_object_from_scene_graph(name_id, scene_graph["objects_in_room"])
                        corr_obj["placement"]["objects_in_room"].append({"object_id" : r["name_id"], "preposition" : r["preposition"], "is_adjacent" : r["is_adjacent"]})
    with open('scene_graph_after_refiner.json', 'w') as f:
        json.dump(scene_graph, f, indent=4)
    print("scene_graph_after_refiner.json 已保存")
# 关闭agents
    await corrector.shutdown()
    await refiner.shutdown()
    print("\nAgents已关闭")

def create_object_clusters(verbose=False):
    
    # Assign the rotations
    with open("scene_graph_after_refiner.json", "r", encoding="utf-8") as f:
        scene_graph = json.load(f)
    for obj in scene_graph["objects_in_room"]:
        rot = get_rotation(obj, scene_graph["objects_in_room"])
        obj["rotation"] = {"z_angle" : rot}
    
    ROOM_LAYOUT_ELEMENTS = ["south_wall", "north_wall", "west_wall", "east_wall", "ceiling", "middle of the room"]

    G = build_graph(scene_graph["objects_in_room"])
    nodes = G.nodes()

    # Create clusters
    for node in nodes:
        if node not in ROOM_LAYOUT_ELEMENTS:
            cluster_size, children_objs = get_cluster_size(node, G, scene_graph["objects_in_room"])
            if verbose:
                print("Node: ", node)
                print("Cluster size: ", cluster_size)
                print("Children: ", children_objs)
                print("\n")
            node_obj = get_object_from_scene_graph(node, scene_graph["objects_in_room"])
            cluster_size = {"x_neg" : cluster_size["left of"], "x_pos" : cluster_size["right of"], "y_neg" : cluster_size["behind"], "y_pos" : cluster_size["in front"]}
            node_obj["cluster"] = {"constraint_area" : cluster_size}
    with open("scene_graph_after_cluster.json", "w", encoding="utf-8") as f:
        json.dump(scene_graph, f, indent=4, ensure_ascii=False)

def backtrack(verbose=False, room_dimensions=[4, 4, 2.5]):
    print(room_dimensions)
    time.sleep(5)
    with open('scene_graph_after_cluster.json', 'r', encoding='utf-8') as f:
        scene_graph = json.load(f)
    room_priors = get_room_priors(room_dimensions)
    scene_graph = scene_graph["objects_in_room"] + room_priors
    prior_ids = ["south_wall", "north_wall", "east_wall", "west_wall", "ceiling", "middle of the room"]
    
    point_bbox = dict.fromkeys([item["new_object_id"] for item in scene_graph], False)
    
    # Place the objects that have an absolute position
    for item in scene_graph:
        if item["new_object_id"] in prior_ids:
            continue
        possible_pos = get_possible_positions(item["new_object_id"], scene_graph, room_dimensions)
        # Determine the overlap based on the possible positions
        overlap = None
        if len(possible_pos) == 1:
            overlap = possible_pos[0]
        elif len(possible_pos) > 1:
            overlap = possible_pos[0]
            for pos in possible_pos[1:]:
                overlap = calculate_overlap(overlap, pos)
        # If the overlap is a point bbox, assign the position
        if overlap is not None and is_point_bbox(overlap) and len(possible_pos) > 0:
            item["position"] = {"x" : overlap[0], "y" : overlap[2], "z" : overlap[4]}
            point_bbox[item["new_object_id"]] = True
    
    scene_graph_wo_layout = [item for item in scene_graph if item["new_object_id"] not in prior_ids]
    object_ids = [item["new_object_id"] for item in scene_graph_wo_layout]
    # Get depths
    depth_scene_graph = get_depth(scene_graph_wo_layout)
    max_depth = max(depth_scene_graph.values())
    
    if verbose:
        print("Max depth: ", max_depth)
        print("Depth scene graph: ", depth_scene_graph)
        print("Point BBox: ", [key for key, value in point_bbox.items() if value])
        get_visualization(scene_graph, room_priors)
        for obj in scene_graph_wo_layout:
            if "position" in obj.keys():
                print(obj["new_object_id"], obj["position"])
    
    topological_order = get_topological_ordering(scene_graph_wo_layout)
    topological_order = [item for item in topological_order if item not in prior_ids]
    if verbose:
        print("Topological order: ", topological_order)
    
    d = 1
    while d <= max_depth:   
        if verbose:
            print("Depth: ", d)
        error_flag = False
        
        # Get nodes at the current depth
        nodes = [node for node in topological_order if depth_scene_graph[node] == d]
        if verbose:
            print(f"Nodes at depth {d}:", nodes)
        
        errors = {}
        for node in nodes:
            if point_bbox[node]:
                print(f"{node} has already been placed")
                continue
            
            # Find the object corresponding to the current node
            obj = next(item for item in scene_graph_wo_layout if item["new_object_id"] == node)
            errors = place_object(obj, scene_graph, room_dimensions, errors={}, verbose=verbose)
            if verbose:
                print(f"Errors for {obj['new_object_id']}:", errors)

            if errors:
                if d > 1:
                    d -= 1
                    if verbose:
                        print("Reducing depth to: ", d)
                
                error_flag = True
                # Delete positions for objects at or beyond the current depth
                for del_item in scene_graph_wo_layout:
                    if depth_scene_graph[del_item["new_object_id"]] >= d:
                        if "position" in del_item.keys() and not point_bbox[del_item["new_object_id"]]:
                            if verbose:
                                print("Deleting position for: ", del_item["new_object_id"])
                            del del_item["position"]
                errors = {}
                break
                        
        if not error_flag:
            d += 1
    if verbose:
        get_visualization(scene_graph, room_priors)
    with open('scene_graph.json', 'w', encoding='utf-8') as f:
        json.dump(scene_graph, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    room_dimensions = [5, 5, 2.8]
    # 运行主函数
    asyncio.run(main(room_dimensions, 'Design me a living room')) 
    create_object_clusters(verbose=True)
    backtrack(verbose=True, room_dimensions=room_dimensions)
