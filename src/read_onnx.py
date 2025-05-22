import onnx

def read_onnx_model(model_path):
    try:
        # 加载 ONNX 模型
        model = onnx.load(model_path)
        
        # 验证模型格式是否正确
        onnx.checker.check_model(model)
        
        # 获取模型的基本信息
        print(f'模型名称: {model.graph.name}')
        print('输入信息:')
        for input_tensor in model.graph.input:
            print(f'  名称: {input_tensor.name}')
            print(f'  类型: {onnx.helper.tensor_dtype_to_np_dtype(input_tensor.type.tensor_type.elem_type)}')
            print(f'  形状: {[d.dim_value for d in input_tensor.type.tensor_type.shape.dim]}')
        
        print('输出信息:')
        for output_tensor in model.graph.output:
            print(f'  名称: {output_tensor.name}')
            print(f'  类型: {onnx.helper.tensor_dtype_to_np_dtype(output_tensor.type.tensor_type.elem_type)}')
            print(f'  形状: {[d.dim_value for d in output_tensor.type.tensor_type.shape.dim]}')
        
        print(f'节点数量: {len(model.graph.node)}')
        node_types = {}
        for node in model.graph.node:
            if node.op_type in node_types:
                node_types[node.op_type] += 1
            else:
                node_types[node.op_type] = 1
        print('节点类型统计:')
        for op_type, count in node_types.items():
            print(f'  {op_type}: {count}')
        
        return model
    except FileNotFoundError:
        print(f'错误: 文件 {model_path} 未找到')
        return None
    except Exception as e:
        print(f'错误: 加载模型时发生异常: {e}')
        return None

if __name__ == '__main__':
    model_path = 'E:/Research/Program/else/swi_ipcr_swa_ipshock/src/shock_checking.onnx'
    model = read_onnx_model(model_path)
    if model:
        print('模型已成功加载并验证')