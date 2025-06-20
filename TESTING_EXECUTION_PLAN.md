# AI Flashcard Generator 测试执行计划

## 🎯 测试目标

验证项目重构后的功能完整性、性能提升和系统稳定性，确保新版本完全兼容并提供更好的用户体验。

---

## 📋 测试准备检查清单

### ✅ 已就绪的测试基础设施
- [x] 单元测试框架 (`test_prompt_system.py`)
- [x] 性能测试工具 (`performance_test.py`, `benchmark.py`)
- [x] 多版本代码对比 (原版 vs 重构版)
- [x] 前端测试界面 (`test_new_interface.html`)
- [x] 容器化测试环境 (`Dockerfile`, `docker-compose.yml`)
- [x] 监控配置 (`monitoring/` 目录)

### 🔧 需要准备的测试数据
- [ ] OpenRouter API 密钥 (用于实际API测试)
- [ ] 测试文本样本 (不同长度、不同领域)
- [ ] 预期结果基准 (用于回归测试)

---

## 🚀 Phase 1: 基础功能验证 (立即执行)

### 步骤1: 环境准备和依赖检查
```bash
# 1. 激活虚拟环境
source flashcard/bin/activate

# 2. 检查依赖
pip install -r requirements.txt

# 3. 验证pytest安装
pytest --version

# 4. 检查新增依赖
pip list | grep -E "(pytest|aiohttp)"
```

### 步骤2: Prompt系统单元测试
```bash
# 运行Prompt系统测试
python test_prompt_system.py

# 使用pytest运行
pytest test_prompt_system.py -v
```

**验证项目**:
- ✅ PromptTemplate类创建和验证
- ✅ PromptManager加载预设模板
- ✅ 自定义模板功能
- ✅ 模板格式化和参数替换
- ✅ 错误处理和边界条件

### 步骤3: 后端API功能测试
```bash
# 1. 启动原版本服务器 (作为对照)
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# 2. 启动重构版本服务器 (测试版本)
uvicorn main_refactored:app --reload --host 127.0.0.1 --port 8001

# 3. 运行API基础测试
curl http://127.0.0.1:8001/supported_models
```

**验证项目**:
- ✅ `/supported_models` 端点响应
- ✅ API响应格式兼容性
- ✅ 错误处理机制
- ✅ 新增字段功能

### 步骤4: 前端界面测试
```bash
# 打开浏览器测试页面
# 原版本: http://127.0.0.1:8000/local_index.html
# 新版本: http://127.0.0.1:8001/test_new_interface.html
# 统一版本: http://127.0.0.1:8001/unified_index.html
```

**验证项目**:
- ✅ 页面正常加载
- ✅ 模型列表获取
- ✅ 新增的Prompt自定义界面
- ✅ 卡片数量配置功能
- ✅ 导出功能完整性

---

## ⚡ Phase 2: 性能对比测试

### 步骤1: 基准性能测试
```bash
# 运行解析算法基准测试
python benchmark.py

# 生成性能报告
python benchmark.py --export-csv
```

### 步骤2: 并发性能测试
```bash
# 轻量级并发测试 (10用户)
python performance_test.py --concurrent-users 10 --requests-per-user 5

# 中等负载测试 (50用户) 
python performance_test.py --concurrent-users 50 --requests-per-user 3

# 重负载测试 (100用户)
python performance_test.py --concurrent-users 100 --requests-per-user 2
```

### 步骤3: 内存和资源监控
```bash
# 启动监控 (如果配置了)
docker-compose -f monitoring/docker-compose.yml up -d

# 查看资源使用
top -p $(pgrep -f uvicorn)
```

---

## 🧪 Phase 3: 端到端功能测试

### 步骤1: 实际API调用测试
**前提**: 需要有效的OpenRouter API密钥

```python
# 创建测试脚本 test_e2e.py
import asyncio
import httpx

async def test_flashcard_generation():
    payload = {
        "text": "机器学习是人工智能的一个重要分支，它让计算机能够从数据中学习模式，而无需明确编程。",
        "api_key": "YOUR_API_KEY",
        "model_name": "google/gemini-2.5-flash-preview",
        "max_cards": 5,  # 新功能
        "template_name": "academic"  # 新功能
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://127.0.0.1:8001/generate_flashcards/", 
            json=payload
        )
        
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

# 运行测试
asyncio.run(test_flashcard_generation())
```

### 步骤2: 新功能验证测试
- ✅ 自定义Prompt模板功能
- ✅ 可配置卡片数量 (5-50张)
- ✅ 预设模板选择功能
- ✅ 向后兼容性验证

### 步骤3: 导出功能完整性测试
- ✅ Anki Markdown格式
- ✅ CSV格式
- ✅ JSON格式
- ✅ 批量导出功能

---

## 🐳 Phase 4: 容器化部署测试

### 步骤1: Docker环境测试
```bash
# 构建Docker镜像
docker build -t flashcard-generator .

# 运行容器
docker run -p 8002:8000 flashcard-generator

# 测试容器化版本
curl http://127.0.0.1:8002/supported_models
```

### 步骤2: Docker Compose测试
```bash
# 启动完整服务栈
docker-compose up -d

# 验证所有服务
docker-compose ps

# 测试服务连通性
curl http://127.0.0.1:8000/supported_models
```

---

## 📊 Phase 5: 回归测试和对比分析

### 功能对比清单
| 功能项目 | 原版本 | 重构版本 | 状态 |
|---------|--------|----------|------|
| 基础卡片生成 | ✅ | ✅ | 向后兼容 |
| 模型选择 | ✅ | ✅ | 功能保持 |
| 导出格式 | ✅ | ✅ | 功能增强 |
| Prompt自定义 | ❌ | ✅ | 新增功能 |
| 卡片数量配置 | ❌ | ✅ | 新增功能 |
| 模板系统 | ❌ | ✅ | 新增功能 |
| 性能优化 | ❌ | ✅ | 新增功能 |

### 性能对比基准
- **解析速度**: 目标提升20-30%
- **内存使用**: 目标减少15-20%
- **并发处理**: 目标支持2-3倍用户数
- **响应时间**: 目标减少10-15%

---

## 🚨 测试失败处理流程

### 1. 单元测试失败
```bash
# 详细错误分析
pytest test_prompt_system.py -v -s

# 查看错误日志
tail -f logs/error.log
```

### 2. API测试失败
```bash
# 检查服务状态
ps aux | grep uvicorn

# 查看服务日志
uvicorn main_refactored:app --log-level debug
```

### 3. 性能测试异常
```bash
# 系统资源检查
htop

# 网络连接检查
netstat -tlnp | grep 8000
```

---

## ✅ 测试通过标准

### 基础功能测试
- [ ] 所有单元测试通过 (100%)
- [ ] API端点正常响应 (状态码200)
- [ ] 前端界面无JavaScript错误
- [ ] 新功能按预期工作

### 性能测试
- [ ] 解析性能提升 >20%
- [ ] 并发用户支持 >50人同时
- [ ] 内存使用稳定 (<512MB)
- [ ] 响应时间 <3秒 (正常文本)

### 兼容性测试
- [ ] 原有API调用完全兼容
- [ ] 前端界面在主流浏览器正常
- [ ] Docker部署成功运行
- [ ] 数据格式向后兼容

---

## 📈 测试结果记录模板

```markdown
# 测试执行报告

## 测试环境
- 操作系统: 
- Python版本: 
- 测试时间: 
- 测试人员: 

## 测试结果总览
- 单元测试: ✅/❌ (通过率: %)
- API测试: ✅/❌ 
- 性能测试: ✅/❌ (提升: %)
- 前端测试: ✅/❌
- 容器测试: ✅/❌

## 发现的问题
1. [问题描述]
   - 严重程度: High/Medium/Low
   - 影响范围: 
   - 解决方案: 

## 性能指标
- 解析速度: 原版 vs 新版
- 内存使用: 原版 vs 新版  
- 并发处理: 原版 vs 新版

## 建议和下一步
- [ ] 立即修复的问题
- [ ] 可以延后的改进
- [ ] 生产部署建议
```

---

## 🎯 立即执行建议

**建议立即开始Phase 1基础功能验证**，这是风险最低、收益最明确的测试阶段。

执行顺序:
1. **Prompt系统单元测试** (5分钟)
2. **启动重构版本服务** (2分钟)  
3. **前端界面基础测试** (10分钟)
4. **API功能验证** (10分钟)

总时间约30分钟即可完成基础验证，确认项目重构成功！