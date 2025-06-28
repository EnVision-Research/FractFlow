import os
import ast
from pathlib import Path

class ToolTemplateVisitor(ast.NodeVisitor):
    def __init__(self):
        self.is_tool_template_subclass = False
        self.tool_name = None
        self.tool_description = ""
        self.dependencies = []
        self.class_node = None

    def visit_ClassDef(self, node):
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'ToolTemplate':
                self.is_tool_template_subclass = True
                self.tool_name = node.name
                self.class_node = node
                break
        if self.is_tool_template_subclass:
            self.generic_visit(node)

    def visit_Assign(self, node):
        if self.is_tool_template_subclass and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                if target.id == 'TOOL_DESCRIPTION':
                    if isinstance(node.value, ast.Str):
                        self.tool_description = node.value.s.strip()
                    elif isinstance(node.value, ast.Constant): # Python 3.8+
                        self.tool_description = node.value.value.strip()

                elif target.id == 'TOOLS':
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, (ast.List, ast.Tuple)) and len(elt.elts) == 2:
                                tool_path_node = elt.elts[0]
                                tool_alias_node = elt.elts[1]
                                
                                tool_path = self._get_string_value(tool_path_node)
                                tool_alias = self._get_string_value(tool_alias_node)

                                if tool_path and tool_alias:
                                    self.dependencies.append({
                                        "path": tool_path,
                                        "alias": tool_alias
                                    })

    def _get_string_value(self, node):
        if isinstance(node, ast.Str):
            return node.s
        if isinstance(node, ast.Constant): # Python 3.8+
            return node.value
        return None


class AgentScanner:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def scan_agents(self, tools_path: str = "tools"):
        agents_info = []
        root_path = self.base_path / tools_path
        for file_path in root_path.rglob("*_agent.py"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                    visitor = ToolTemplateVisitor()
                    visitor.visit(tree)
                    
                    if visitor.is_tool_template_subclass:
                        relative_path = file_path.relative_to(self.base_path)
                        agent_id = str(relative_path.with_suffix('')).replace(os.path.sep, '.')
                        
                        docstring = ast.get_docstring(visitor.class_node) if visitor.class_node else ""

                        # Create dependency IDs from their paths
                        dependency_ids = []
                        for dep in visitor.dependencies:
                            dep_path = Path(dep["path"])
                            dep_id = str(dep_path.with_suffix('')).replace(os.path.sep, '.')
                            dependency_ids.append(dep_id)

                        agents_info.append({
                            "id": agent_id,
                            "name": visitor.tool_name,
                            "path": str(relative_path),
                            "description": visitor.tool_description or docstring,
                            "dependencies": dependency_ids,
                        })
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
        return agents_info

if __name__ == '__main__':
    # Example usage:
    # Assuming the script is run from the project root
    scanner = AgentScanner(base_path=os.getcwd())
    agents = scanner.scan_agents()
    import json
    print(json.dumps(agents, indent=2)) 