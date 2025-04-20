import asyncio
import os
from dotenv import load_dotenv
import re
import json
from utils import extract_list_from_json
import copy
import time
# Import the FractalFlow Agent
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager
from schemas import interior_designer_schema, interior_architect_schema, engineer_schema

async def main(room_dimensions, user_preference):
    # 创建agents
    interior_designer = Agent(name='interior_designer')
    interior_architect = Agent(name="interior_architect")
    engineer = Agent(name='engineer')
    print(room_dimensions)

    # 复制配置
    config_designer = copy.deepcopy(interior_designer.get_config())
    config_architect = copy.deepcopy(interior_architect.get_config())
    config_engineer = copy.deepcopy(engineer.get_config())

    # 设置API提供商和模型
    for config in [config_designer, config_architect, config_engineer]:
        config['agent']['provider'] = 'qwen'
        config['qwen']['model'] = "qwen-max-2025-01-25"
        config['qwen']['base_url'] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        config['qwen']['api_key'] = 'key' #TODO
        config['agent']['max_iterations'] = 10
    # for config in [config_designer, config_architect, config_engineer]:
    #     config['agent']['provider'] = 'deepseek'
    #     config['deepseek']['model'] = 'DeepSeek-R1-671B ' # "qwen-max-2025-01-25"
    #     config['deepseek']['base_url'] = 'https://gpt-api.hkust-gz.edu.cn/v1' # "https://dashscope.aliyuncs.com/compatible-mode/v1"
    #     config['deepseek']['api_key'] = 'cap3d 58d0bacc761d4678855f9582819abcc77a4bacaa54984213905d9d546670638a' # 'sk-d770b774f1aa42a2b17fecbd08bd0362'
    #     config['agent']['max_iterations'] = 10

    # return interior_designer, interior_architect , engineer
    # 1. Load environment variables 
    load_dotenv()
    
    # interior_designer, interior_architect, engineer= create_agents()
    print("Initializing agent...")
    #         You should analyze the given json file which contains potential objects in the room. Now you should think carefully about the objects and rearrange information.
    config_designer['agent']['custom_system_prompt'] = f""" Interior Designer. Let's think step by step. 
        The suggested objects should contain the following information:

        1. Object name (ex. bed, desk, chair, monitor, bookshelf, etc.)
        2. Architecture style (ex. modern, classic, etc.)
        3. Material (ex. wood, metal, etc.)
        4. Bounding box size in meters (ex. Length : 1.0m, Width : 1.0m, Height : 1.0m). Only use "Length", "Width", "Height" as keys for the size of the bounding box!
        5. Quantity (ex. 1, 2, 3, etc.)

        IMPORTANT: Do not suggest any objects related to doors or windows, such as curtains, blinds, etc.

        Follow the JSON schema below:
        {interior_designer_schema}

        Respond ONLY with the raw JSON object.
        DO NOT include any markdown formatting or code block markers.
        DO NOT use ```json tags.
        """

    config_architect['agent']['custom_system_prompt'] = f""" Interior Architect. Let's think step by step. Your role is to analyze the given json file, think about where the optimal
        placement for each object would be that the Interior Designer suggests according to the description in the json file.
        If the quantity of an object is greater than one, you have to find a place for each instance of this object separately!, but give all this information in one list item!
        Give explicit answers for EACH object on the following three aspects:

        Placement: 
        Find a relative place for the object according to the description in the json file (ex. on the middle of the floor, in the north-west corner, on the east wall, right of the desk, on the rug...).
        For relative placement with other objects in the room use the prepositions "on", "left of", "right of", "in front", "behind", "under".
        For relative placement with the room layout elements (walls, the middle of the room, ceiling) use the prepositions "on", "in the corner".
        You are not allowed to use any prepositions different from the ones above!! 
        Expliticly state the placement for each instance (ex. one is left of desk_1, one is on the south_wall)!!

        Proximity : 
        Proximity of this object to the relative placement objects:
        1. Adjacent : The object is physically contacting the other object or it is supported by the other object or they are touching or they are close to each other.
        2. Not Adjacent: The object is not physically contacting the other object and it is distant from the other object.


        Facing :
        Think about which wall (west/east/north/south_wall) this object should be facing and explicitly state this (ex. one is facing the south_wall, one is facing the west_wall)!

        Follow the JSON schema below:
        {interior_architect_schema}

        If the quantity of an object is greater than one, you have to find a place for each instance of this object separately, but give all this information in one list item!
        This means the output should have one dictionary for each object, but all their instances (quantity higher than one) should be in the same dictionary!

        Respond ONLY with the raw JSON object.
        DO NOT include any markdown formatting or code block markers.
        DO NOT use ```json tags.
        """
    
    config_engineer['agent']['custom_system_prompt'] = f""" Engineer. Let's think step by step. You listen to the input by the Admin and create a JSON file.
        Every time when the Admin outputs objects to be in the room you will save ALL of them in the given schema!
        For the scene graph, you can use the ids for the objects that are already in the room, but only output the objects to be placed!
        If an object has a quantity higher than one, save each instance of this object separately!!
        If the Json_schema_debugger reports a validation error about the JSON schema, solve the error in a way that spatially makes sense!

        IMPORTANT: The inputted "Placement" key should be used for the "placement" key in the JSON object follow exatly the prepositions stated, 
        do not use the information in "Facing" key for the room layout elements!!!

        IMPORTANT: For object quantities greater than one, the "placement" key gives separately the relative placement of each instance of that object in the room
        make the distinction accordingly!

        Use only the following JSON Schema to save the JSON object:
        {engineer_schema}

        Respond ONLY with the raw JSON object.
        DO NOT include any markdown formatting or code block markers.
        DO NOT use ```json tags.
        """

    try:
        # Interactive chat loop
        print("Agent chat started. Type 'exit', 'quit', or 'bye' to end the conversation.")
        # while True:
        interior_designer.set_config(config_designer)
        await interior_designer.initialize()
        user_input_designer = f"""
        The room has the size {room_dimensions[0]}m x {room_dimensions[1]}m x {room_dimensions[2]}m
        Suggest a reasonal number of objects according to the room size. They should be fit in the room.
        User Preference (in triple backquotes):
        ```
        {user_preference}
        ```
        Room layout elements in the room (in triple backquotes):
        ```
        ['south_wall', 'north_wall', 'west_wall', 'east_wall', 'middle of the room', 'ceiling']
        ```
        json
        """
        # user_input = input("\nYou: ")

        # if user_input_designer.lower() in ('exit', 'quit', 'bye'):
        #     break
            
        print("\n thinking... \n", end="")
        result_designer = await interior_designer.process_query(user_input_designer)
        print("Interior Designer: {}".format(result_designer))

        interior_architect.set_config(config_architect)  
        await interior_architect.initialize()

        user_input_architect = f"""
        The room has the size {room_dimensions[0]}m x {room_dimensions[1]}m x {room_dimensions[2]}m
        The number of objects in the room is as many as possible, but it should be fit in the room.
        User Preference (in triple backquotes):
        ```
        {user_preference}
        ```
        Room layout elements in the room (in triple backquotes):
        ```
        ['south_wall', 'north_wall', 'west_wall', 'east_wall', 'middle of the room', 'ceiling']
        ```
        json
        """

        designer_output = 'Interior Designer suggested the following objects: ' + result_designer

        # if user_input_designer.lower() in ('exit', 'quit', 'bye'):
        #     break
            
        print("\n thinking... \n", end="")
        result_architect = await interior_architect.process_query(user_input_architect + designer_output)
        print("Interior Architect: {}".format(result_architect))
        
        def clean_json_string(content):
            # 使用正则表达式匹配JSON内容
            pattern = r'```(?:json)?\s*(\{[\s\S]*\})\s*```'
            match = re.search(pattern, content)
            if match:
                return match.group(1)
            # 如果没有markdown标记，直接返回内容
            return content.strip()
        
        designer_response = json.loads(clean_json_string(result_designer))
        architect_response = json.loads(clean_json_string(result_architect))

        blocks_designer, blocks_architect = extract_list_from_json(designer_response), extract_list_from_json(architect_response)
        if len(blocks_designer) != len(blocks_architect):
            print("Lengths: ", len(blocks_designer), len(blocks_architect))
            raise ValueError("The number of blocks from the designer and architect should be the same! Please generate again.")

        engineer.set_config(config_engineer)   
        await engineer.initialize()
        json_data = None
        for d_block, a_block in zip(blocks_designer, blocks_architect):
            prompt = str(d_block) + "\n" + str(a_block)
            object_ids = [item["new_object_id"] for item in json_data["objects_in_room"]] if json_data is not None else []
            user_input_engineer = f"""
                Room layout elements in the room (in triple backquotes):
                ```
                ['south_wall', 'north_wall', 'west_wall', 'east_wall', 'middle of the floor', 'ceiling']
                ```
                Array of objects in the room (in triple backquotes):
                ```
                {object_ids}
                ```
                Objects to be placed in the room (in triple backquotes):
                ```
                {prompt}
                ```
                json
                """
            result_engineer = await engineer.process_query(user_input_engineer)
            if json_data is None:
                json_data = json.loads(result_engineer)
            else:
                json_data["objects_in_room"] += json.loads(result_engineer)['objects_in_room']
        
            print("Engineer: {}".format(result_engineer))
            
        print(json_data)
        with open('scene_graph_after_engineer.json', 'w') as f:
            json.dump(json_data, f, indent=4)
    except:
        print('Error')
    finally:
        # Shut down the agent gracefully
        await interior_designer.shutdown()            
        await interior_architect.shutdown()
        await engineer.shutdown()
        print("\nAgent chat ended.")

if __name__ == "__main__":
    import sys
    
    # 默认参数
    room_dimensions = [4, 5, 2.8]
    
    # 如果有命令行参数，则使用命令行参数
    if len(sys.argv) > 1:
        try:
            dimensions = sys.argv[1].split(',')
            room_dimensions = [float(dim) for dim in dimensions]
        except:
            print("警告: 无法解析房间尺寸参数，使用默认值")
    
    print(f"使用房间尺寸: {room_dimensions}")
    
    user_preference = 'Design me a living room.'
    # 执行主函数
    asyncio.run(main(room_dimensions, user_preference)) 