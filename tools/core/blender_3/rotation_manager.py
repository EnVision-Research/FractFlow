"""
旋转管理器 - 统一处理Blender中的各种旋转模式

提供旋转模式检测、转换和统一设置功能，解决不同旋转表示之间的兼容性问题
"""

import bpy
from mathutils import Euler, Quaternion, Matrix, Vector
import math
import json

class RotationManager:
    """统一旋转管理器"""
    
    # 支持的旋转模式
    SUPPORTED_MODES = ['QUATERNION', 'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX', 'AXIS_ANGLE']
    
    # 默认旋转模式
    DEFAULT_MODE = 'XYZ'
    
    def __init__(self):
        """初始化旋转管理器"""
        pass
    
    def detect_rotation_mode(self, obj):
        """
        检测对象的当前旋转模式
        
        Args:
            obj: Blender对象
            
        Returns:
            str: 旋转模式字符串
        """
        if hasattr(obj, 'rotation_mode'):
            return obj.rotation_mode
        return self.DEFAULT_MODE
    
    def get_rotation_value(self, obj, as_mode=None):
        """
        获取对象的旋转值
        
        Args:
            obj: Blender对象
            as_mode: 期望的旋转模式格式
            
        Returns:
            tuple: (rotation_value, rotation_mode)
        """
        current_mode = self.detect_rotation_mode(obj)
        
        if as_mode and as_mode != current_mode:
            # 需要转换
            return self.convert_rotation_from_object(obj, as_mode), as_mode
        
        # 返回原始格式
        if current_mode == 'QUATERNION':
            return list(obj.rotation_quaternion), current_mode
        elif current_mode == 'AXIS_ANGLE':
            return list(obj.rotation_axis_angle), current_mode
        else:
            # 欧拉角模式
            return list(obj.rotation_euler), current_mode
    
    def convert_rotation_from_object(self, obj, target_mode):
        """
        从对象当前旋转转换到目标模式
        
        Args:
            obj: Blender对象
            target_mode: 目标旋转模式
            
        Returns:
            list: 转换后的旋转值
        """
        current_mode = self.detect_rotation_mode(obj)
        
        if current_mode == target_mode:
            return self.get_rotation_value(obj, current_mode)[0]
        
        # 获取世界变换矩阵的旋转部分
        world_matrix = obj.matrix_world
        rotation_matrix = world_matrix.to_3x3().normalized()
        
        if target_mode == 'QUATERNION':
            quat = rotation_matrix.to_quaternion()
            return [quat.w, quat.x, quat.y, quat.z]
        elif target_mode == 'AXIS_ANGLE':
            quat = rotation_matrix.to_quaternion()
            axis_angle = quat.to_axis_angle()
            return [axis_angle[0], axis_angle[1].x, axis_angle[1].y, axis_angle[1].z]
        else:
            # 欧拉角模式
            euler = rotation_matrix.to_euler(target_mode)
            return [euler.x, euler.y, euler.z]
    
    def convert_rotation(self, rotation_value, from_mode, to_mode):
        """
        转换旋转值从一种模式到另一种模式
        
        Args:
            rotation_value: 旋转值列表
            from_mode: 源旋转模式
            to_mode: 目标旋转模式
            
        Returns:
            list: 转换后的旋转值
        """
        if from_mode == to_mode:
            return rotation_value
        
        # 先转换为旋转矩阵（通用中间格式）
        if from_mode == 'QUATERNION':
            if len(rotation_value) == 4:
                quat = Quaternion((rotation_value[0], rotation_value[1], rotation_value[2], rotation_value[3]))
            else:
                raise ValueError(f"QUATERNION mode requires 4 values, got {len(rotation_value)}")
            rotation_matrix = quat.to_matrix()
        elif from_mode == 'AXIS_ANGLE':
            if len(rotation_value) == 4:
                angle = rotation_value[0]
                axis = Vector((rotation_value[1], rotation_value[2], rotation_value[3]))
                quat = Quaternion(axis, angle)
                rotation_matrix = quat.to_matrix()
            else:
                raise ValueError(f"AXIS_ANGLE mode requires 4 values, got {len(rotation_value)}")
        else:
            # 欧拉角模式
            if len(rotation_value) == 3:
                euler = Euler((rotation_value[0], rotation_value[1], rotation_value[2]), from_mode)
                rotation_matrix = euler.to_matrix()
            else:
                raise ValueError(f"Euler mode requires 3 values, got {len(rotation_value)}")
        
        # 从旋转矩阵转换到目标模式
        if to_mode == 'QUATERNION':
            quat = rotation_matrix.to_quaternion()
            return [quat.w, quat.x, quat.y, quat.z]
        elif to_mode == 'AXIS_ANGLE':
            quat = rotation_matrix.to_quaternion()
            axis_angle = quat.to_axis_angle()
            return [axis_angle[0], axis_angle[1].x, axis_angle[1].y, axis_angle[1].z]
        else:
            # 欧拉角模式
            euler = rotation_matrix.to_euler(to_mode)
            return [euler.x, euler.y, euler.z]
    
    def set_rotation_unified(self, obj, rotation_value, rotation_mode=None, force_mode=None):
        """
        统一设置对象旋转
        
        Args:
            obj: Blender对象
            rotation_value: 旋转值
            rotation_mode: 旋转值的模式
            force_mode: 强制对象使用的旋转模式
            
        Returns:
            dict: 设置结果
        """
        try:
            current_mode = self.detect_rotation_mode(obj)
            input_mode = rotation_mode or current_mode
            target_mode = force_mode or current_mode
            
            # 如果需要转换旋转模式
            if target_mode != current_mode:
                obj.rotation_mode = target_mode
            
            # 转换旋转值到目标模式
            if input_mode != target_mode:
                converted_rotation = self.convert_rotation(rotation_value, input_mode, target_mode)
            else:
                converted_rotation = rotation_value
            
            # 设置旋转值
            if target_mode == 'QUATERNION':
                if len(converted_rotation) == 4:
                    obj.rotation_quaternion = converted_rotation
                else:
                    raise ValueError("QUATERNION requires 4 values")
            elif target_mode == 'AXIS_ANGLE':
                if len(converted_rotation) == 4:
                    obj.rotation_axis_angle = converted_rotation
                else:
                    raise ValueError("AXIS_ANGLE requires 4 values")
            else:
                # 欧拉角模式
                if len(converted_rotation) == 3:
                    obj.rotation_euler = converted_rotation
                else:
                    raise ValueError("Euler angles require 3 values")
            
            # 更新场景
            bpy.context.view_layer.update()
            
            return {
                'success': True,
                'object': obj.name,
                'input_mode': input_mode,
                'target_mode': target_mode,
                'input_rotation': rotation_value,
                'final_rotation': converted_rotation,
                'world_matrix_rotation': [list(row) for row in obj.matrix_world.to_3x3()]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'object': obj.name if obj else 'None'
            }
    
    def match_rotation_to_guide(self, asset_obj, guide_obj):
        """
        将资产的旋转匹配到导引线的旋转
        
        Args:
            asset_obj: 资产对象
            guide_obj: 导引线对象
            
        Returns:
            dict: 匹配结果
        """
        try:
            # 获取导引线的旋转信息
            guide_rotation, guide_mode = self.get_rotation_value(guide_obj)
            
            # 设置资产旋转匹配导引线
            result = self.set_rotation_unified(
                asset_obj, 
                guide_rotation, 
                guide_mode,
                force_mode=self.DEFAULT_MODE  # 统一使用默认模式
            )
            
            if result['success']:
                result['guide_object'] = guide_obj.name
                result['guide_rotation'] = guide_rotation
                result['guide_mode'] = guide_mode
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'asset_object': asset_obj.name if asset_obj else 'None',
                'guide_object': guide_obj.name if guide_obj else 'None'
            }
    
    def standardize_rotation_mode(self, obj, target_mode=None):
        """
        标准化对象的旋转模式
        
        Args:
            obj: Blender对象
            target_mode: 目标旋转模式，默认为DEFAULT_MODE
            
        Returns:
            dict: 标准化结果
        """
        target_mode = target_mode or self.DEFAULT_MODE
        current_mode = self.detect_rotation_mode(obj)
        
        if current_mode == target_mode:
            return {
                'success': True,
                'object': obj.name,
                'message': f'Object already using {target_mode} mode',
                'mode': target_mode
            }
        
        # 获取当前旋转值并转换
        current_rotation, _ = self.get_rotation_value(obj)
        result = self.set_rotation_unified(obj, current_rotation, current_mode, target_mode)
        
        if result['success']:
            result['message'] = f'Converted from {current_mode} to {target_mode}'
        
        return result

# 创建全局实例
rotation_manager = RotationManager() 