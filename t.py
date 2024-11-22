import torch
import time
import torch_directml

# 定义矩阵大小
size = 1000
# 创建两个随机矩阵（CPU上）
mat1_cpu = torch.randn(size, size)
mat2_cpu = torch.randn(size, size)

# 测试仅使用CPU进行矩阵乘法的时间
start_time_cpu = time.time()
result_cpu = torch.matmul(mat1_cpu, mat2_cpu)
end_time_cpu = time.time()
cpu_time = end_time_cpu - start_time_cpu
print(f"Time taken for matrix multiplication on CPU: {cpu_time} seconds")

# 尝试将矩阵转移到DirectML设备上（如果可用）
try:
    dml_device = torch_directml.device()
    mat1_dml = mat1_cpu.to(dml_device)
    mat2_dml = mat2_cpu.to(dml_device)
    start_time_dml = time.time()
    result_dml = torch.matmul(mat1_dml, mat2_dml)
    end_time_dml = time.time()
    dml_time = end_time_dml - start_time_dml
    print(f"Time taken for matrix multiplication on torch_directml (AMD GPU): {dml_time} seconds")
    print(f"Speedup factor (CPU time / DML time): {cpu_time / dml_time}")
except:
    print("Failed to perform matrix multiplication on torch_directml device.")