import asyncio
import subprocess
import os
import time
import sys

async def run_process(script_path, args=None):
    """运行指定的Python脚本并等待完成"""
    print(f"\n{'='*50}")
    print(f"执行脚本: {script_path}")
    if args:
        print(f"参数: {args}")
    print(f"{'='*50}\n")
    
    cmd = [sys.executable, script_path]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # 实时输出结果
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        print(line.decode('utf-8').rstrip())
    
    # 等待进程完成
    await process.wait()
    if process.returncode != 0:
        stderr = await process.stderr.read()
        print(f"错误: {stderr.decode('utf-8')}")
        print(f"脚本 {script_path} 执行失败，返回码: {process.returncode}")
    else:
        print(f"\n脚本 {script_path} 执行成功\n")

async def run_iteration(room_dimensions, room_description, iteration):
    """运行一次完整迭代"""
    print(f"\n{'*'*50}")
    print(f"执行迭代 {iteration+1}/5")
    print(f"房间尺寸: {room_dimensions}")
    print(f"描述: {room_description}")
    print(f"{'*'*50}\n")
    
    create_agent_path = "create_agent.py"
    corrector_path = "corrector.py"
    
    # 备份原文件
    with open(create_agent_path, 'r', encoding='utf-8') as f:
        original_create_agent = f.read()
        
    with open(corrector_path, 'r', encoding='utf-8') as f:
        original_corrector = f.read()
    
    try:
        # 修改create_agent.py的main调用
        with open(create_agent_path, 'w', encoding='utf-8') as f:
            lines = original_create_agent.splitlines()
            main_line_index = -1
            if_main_index = -1
            
            # 找到if __name__ == "__main__": 行和asyncio.run行
            for i, line in enumerate(lines):
                if line.strip().startswith('if __name__ =='):
                    if_main_index = i
                elif 'asyncio.run(main(' in line:
                    main_line_index = i
            
            if if_main_index != -1:
                # 在if __name__后插入新的变量定义
                lines.insert(if_main_index + 1, f"    # 自动生成的调用")
                lines.insert(if_main_index + 2, f"    room_dims = {room_dimensions}")
                lines.insert(if_main_index + 3, f"    user_pref = '{room_description}'")
            
            if main_line_index != -1:
                # 替换asyncio.run行
                lines[main_line_index + 3] = f"    asyncio.run(main(room_dims, user_pref))"
            
            modified_content = '\n'.join(lines)
            f.write(modified_content)
        
        # 修改corrector.py的main调用
        with open(corrector_path, 'w', encoding='utf-8') as f:
            lines = original_corrector.splitlines()
            if_main_index = -1
            main_line_index = -1
            backtrack_line_index = -1
            
            # 找到相关行的索引
            for i, line in enumerate(lines):
                if line.strip().startswith('if __name__ =='):
                    if_main_index = i
                elif 'asyncio.run(main(' in line:
                    main_line_index = i
                elif 'backtrack(verbose=True' in line:
                    backtrack_line_index = i
            
            if if_main_index != -1:
                # 在if __name__后插入新的变量定义
                lines.insert(if_main_index + 1, f"    # 自动生成的调用")
                lines.insert(if_main_index + 2, f"    room_dims = {room_dimensions}")
                lines.insert(if_main_index + 3, f"    user_pref = '{room_description}'")
            
            # 更新main调用行的索引（因为插入了3行）
            if main_line_index != -1 and if_main_index != -1 and main_line_index > if_main_index:
                main_line_index += 3
            
            # 更新backtrack调用行的索引（因为插入了3行）
            if backtrack_line_index != -1 and if_main_index != -1 and backtrack_line_index > if_main_index:
                backtrack_line_index += 3
            
            if main_line_index != -1:
                # 替换asyncio.run行
                lines[main_line_index] = f"    asyncio.run(main(room_dims, user_pref))"
            
            if backtrack_line_index != -1:
                # 替换backtrack行
                lines[backtrack_line_index] = f"    backtrack(verbose=True, room_dimensions=room_dims)"
            
            modified_content = '\n'.join(lines)
            f.write(modified_content)
            
        # 运行脚本
        await run_process(create_agent_path)
        await run_process(corrector_path)
        
        # 重命名结果文件以保留每次迭代的结果
        iteration_suffix = f"_iter{iteration+1}"
        for filename in ["scene_graph_after_engineer.json", "scene_graph_after_corrector.json", "scene_graph_final.json"]:
            if os.path.exists(filename):
                new_name = filename.replace(".json", f"{iteration_suffix}.json")
                os.rename(filename, new_name)
                print(f"重命名 {filename} 为 {new_name}")
        
    finally:
        # 恢复原文件
        with open(create_agent_path, 'w', encoding='utf-8') as f:
            f.write(original_create_agent)
            
        with open(corrector_path, 'w', encoding='utf-8') as f:
            f.write(original_corrector)

async def run_iterations():
    """运行5次迭代"""
    # 您可以在这里定义不同的房间尺寸和描述
    iterations = [
        ([3.0, 4.0, 2.4], "Design me a bed room"),
        ([2.5, 3.0, 2.4], "Design me a bed room"),
        ([3.5, 4.5, 2.4], "Design me a bed room"),
        ([4.0, 5.0, 2.4], "Design me a bed room"),
        ([2.4, 3.5, 2.4], "Design me a bed room")
    ]
    
    for i, (dimensions, description) in enumerate(iterations):
        await run_iteration(dimensions, description, i)
        
        # 迭代之间等待一些时间
        if i < len(iterations) - 1:
            print(f"\n等待10秒后开始下一次迭代...\n")
            time.sleep(10)

if __name__ == "__main__":
    # 检查脚本是否存在
    create_agent_path = "create_agent.py"
    corrector_path = "corrector.py"
    
    if not os.path.exists(create_agent_path):
        print(f"错误: {create_agent_path} 不存在")
        sys.exit(1)
    
    if not os.path.exists(corrector_path):
        print(f"错误: {corrector_path} 不存在")
        sys.exit(1)
    
    asyncio.run(run_iterations())