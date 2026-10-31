# 枪03 模型一句话改装 Agent 系统规划

## 1. 文档目标

本文档用于规划一个只服务于 `枪03` 的模型改装 Agent 系统。

系统目标是：

- 用户输入一句自然语言改装需求
- 系统基于固定基础枪模型：
  - `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/枪的模型`
- 自动完成分析、规划、脚本生成、沙箱执行、结果验证和资源打包
- 最终输出一个新的独立改装版本目录，而不破坏基础版本
- 输出目录的内部结构必须对齐：
  - `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/修改优化03`

这不是一个通用 3D 生成平台，而是一个“面向单款枪械资产的受控改装系统”。

## 2. 适用范围与边界

### 2.1 适用范围

系统只处理以下对象：

- 目标枪型：`枪03 / Red Dragon Tech Sniper`
- 基础模型来源：`/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/枪的模型`
- 基础资源格式：
  - `model.gltf`
  - `buffer.bin`
  - `model.glb`
  - 贴图 PNG
  - `viewer.html`
  - `viewer-data.js`
  - `weapon03_meta.json`

### 2.2 不在本期范围内

以下能力不建议在第一期系统中直接支持：

- 支持多把枪共用一套 Agent 逻辑
- 自动理解任意来源的陌生 glTF
- 复杂角色动画或骨骼重绑定
- 高精度雕刻级龙头、浮雕、布料、粒子等 DCC 级操作
- 任意拓扑重建、自动 UV 重展开
- 完全不经规则约束的“随便一句话就无限制改模型”

## 3. 现有基础资产与系统前提

### 3.1 当前可复用的基础枪资产

当前系统规划中的权威基础枪目录应为：

- `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/枪的模型`

这套资源已经具备：

- 规整的 glTF 结构
- 明确的节点层级：
  - `WeaponPose`
  - `ReceiverGroup`
  - `MagazineGroup`
- 可直接查看的 `model.glb`
- 可直接双击使用的本地 viewer
- 可读的 `weapon03_meta.json`

这意味着 Agent 系统不需要先“清洗原始资产”，而是可以把这套目录当成统一基础模板。

补充说明：

- 系统要表达的是：
  - 将基础版本的枪的模型生成一个像 修改优化03 那样的独立改装目录

### 3.2 当前可复用的 LLM 接入脚本

当前可用 LLM 接口参考脚本为：

- `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/Modification_System/参考脚本/test_gpt.py`

脚本特点：

- 已能访问 Responses API
- 已固定模型为 `gpt-5.4`
- 已具备流式输出能力
- 适合先封装成系统内部统一的 LLM Client

但它目前仍是“测试脚本”，不是工程化客户端。后续需要改造为：

- 可传入 developer prompt
- 可传入用户请求
- 可返回结构化 JSON
- 可支持失败重试
- 可记录 request / response 日志
- 可通过环境变量管理密钥，而不是写死在脚本里

## 4. 总体设计原则

系统设计建议遵循以下原则：

### 4.1 单枪专用优先

因为系统只服务 `枪03`，所以应该大胆利用这把枪的先验知识，而不是追求抽象过度。

例如：

- 已知有哪些核心节点
- 已知主要材质分类
- 已知基础动画有哪些
- 已知已有的改装方式包括：
  - 贴图增强
  - 材质增强
  - 外挂装甲几何
  - 在保证和其他模块能连接的前提下实行模块重做

### 4.2 先受控，再智能

不要第一版就让 LLM 直接自由写任意脚本。

更稳妥的路线是：

1. 先把可支持的改装类型收敛成有限类别
2. LLM 先把用户自然语言转换成结构化改装意图
3. 系统再根据结构化意图调用固定模板或固定脚本生成策略
4. 只有在模板无法覆盖时，才让 LLM 参与脚本生成

### 4.3 不破坏基础版本

系统必须保证：

- 不修改基础目录
- 每次改装输出到独立目录

### 4.4 沙箱执行优先

因为系统要自动运行生成脚本，所以必须在沙箱环境中执行，并对以下内容做限制：

- 可读目录
- 可写目录
- 可执行脚本范围
- 运行超时
- 输出文件类型

## 5. 系统目标输出

给定一句用户需求，系统应输出一个独立版本目录，目录中至少包含：

- `model.gltf`
- `buffer.bin`
- `model.glb`
- 贴图文件
- `viewer.html`
- `viewer-data.js`
- 预览图
- `weapon03_meta.json`
- `README.md`
- 改装日志
- 需求解析结果
- 运行报告

### 5.1 目录模板强约束

本系统最终输出的不是普通临时目录，而应当是一个“像 修改优化03 一样完整”的正式改装版本目录。

因此，每次正式输出都必须尽量对齐以下目录模板：

- `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/修改优化03`

也就是说，正式变体目录的设计目标应当是：

- 根目录就是一个完整版本
- 根目录下直接包含模型、贴图、查看器、说明文档和构建脚本
- 用户拿到该目录后，无需依赖其他目录即可查看、复现和交付

### 5.2 正式变体目录建议结构

推荐系统生成的每个正式变体目录都遵循如下结构：

```text
<variant_dir>/
├── model.gltf
├── buffer.bin
├── model.glb
├── EM_Orange.png
├── glass.png
├── T_XCR_Iron_Rouge_body_B.png
├── T_XCR_Iron_Rouge_magazine_B.png
├── T_XCR_Iron_Rouge_scope01_B.png
├── T_XCR_Iron_Rouge_scope02_B.png
├── viewer.html
├── viewer-data.js
├── viewer-assets/
├── weapon03_meta.json
├── README.md
├── <build_variant_script>.py
├── <variant_preview>.png
└── <variant_process_doc>.md
```

上面这个结构不是随意举例，而是建议系统把它作为“正式变体目录模板”固化下来。

### 5.3 生成目录命名建议

推荐正式产物放在：

- `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/Modification_System/variants/<variant_slug>/`

例如：

- `variants/true_3d_dragon_v04/`
- `variants/black_gold_dragon_v01/`
- `variants/frost_spine_v01/`

但该目录内部结构必须对齐 `修改优化03` 的布局。

如果后续需要平级发布，也可以把正式变体导出为：

- `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/修改优化04`
- `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/修改优化05`

### 5.4 正式变体目录中的特殊文件要求

参考 `修改优化03` 的做法，系统生成的每个正式变体目录中，建议强制包含：

- 一个构建脚本
  - 例如 `build_true_3d_dragon_v04.py`
  - 或 `build_black_gold_dragon_v01.py`
- 一份实现过程文档
  - 例如 `黑金龙装甲_实现过程.md`
- 一张预览图
  - 例如 `dragon_3d_armor_preview.png`
  - 或 `<variant_slug>_preview.png`

这样最终目录不仅是结果包，也是复现包。

### 5.5 运行目录与正式目录分离

系统内部可以保留 `runs/` 用于临时执行，但最终必须沉淀出一个正式变体目录。

推荐规则：

- `runs/`：执行中间态、调试日志、失败重试
- `variants/`：正式交付目录，结构按 `修改优化03` 模板组织

推荐输出路径模式：

- `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/Modification_System/runs/<run_id>/`

或：

- `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/Modification_System/variants/<variant_slug>/`

## 6. 建议的系统分层

推荐把整个系统拆成 6 层。

### 6.1 接入层

负责接收用户一句话输入。

输入示例：

- “给这把枪做成黑金龙风格，枪身两侧加立体鳞片，镜片保留。”
- “把这把枪改成冰霜主题，发光从橙色改成蓝白色，弹匣更厚重。”
- “我想要一个机械恶魔风版本，枪口更尖，枪身顶部加刺。”

这一层只负责：

- 接收文本
- 生成请求 ID
- 写入原始日志

### 6.2 语义解析层

这一层由 LLM 主导，把自然语言转成结构化改装规格。

建议输出 JSON，例如：

```json
{
  "theme": "black_gold_dragon",
  "style_tags": ["dragon", "luxury", "aggressive"],
  "modification_targets": [
    {
      "type": "add_geometry",
      "target": "receiver",
      "subtype": "scales",
      "intensity": "medium"
    },
    {
      "type": "material_change",
      "target": "emissive_parts",
      "color": "#ff7a00"
    }
  ],
  "constraints": [
    "keep_scope_glass",
    "keep_original_animation"
  ],
  "risk_level": "medium"
}
```

这一步的核心不是生成代码，而是把“人话”稳定转成“系统能执行的话”。

### 6.3 规划层

这一层根据结构化需求，决定应该走哪条改装路线。

建议把改装路线分成 4 类：

1. `texture_only`
  - 只改 base color / emissive / normal / ORM 等贴图
2. `material_only`
  - 只改 glTF 材质参数
3. `additive_geometry`
  - 在原模型外添加几何件
4. `hybrid`
  - 贴图、材质、几何联合修改

例如：

- “改成黑金风格”通常属于 `material_only` 或 `hybrid`
- “枪身长出龙鳞”属于 `additive_geometry`
- “橙色发光改蓝色”属于 `material_only`
- “做一个冰霜骨龙版本”通常属于 `hybrid`

### 6.4 执行层

这一层真正产生改装结果。

建议执行层再拆成 3 类执行器：

1. 模板执行器
  - 适合固定套路，例如龙鳞、尖刺、骨架装甲、改发光色
2. 参数化脚本执行器
  - 通过参数生成几何，例如：
    - spine positions
    - scale size
    - horn size
    - material color
3. LLM 脚本生成执行器
  - 当模板无法覆盖时，由 LLM 生成新脚本，再沙箱运行

第一期系统建议优先使用前两种，第三种只作为保底扩展。

### 6.5 验证层

执行完后，自动验证结果是否可交付。

至少应验证：

- `model.gltf` 可解析
- `buffer.bin` 存在且字节数匹配
- `model.glb` 可成功加载
- `viewer-data.js` 已同步
- 预览图已生成
- 新增 mesh / material / node 是否符合计划
- 基础目录未被修改

### 6.6 交付层

负责最终产出整理：

- 生成 `README.md`
- 更新 `weapon03_meta.json`
- 记录本次改装说明
- 输出最终目录路径
- 生成调试日志和失败回溯信息

## 7. 建议的 Agent 架构

如果要做成 Agent 系统，建议不要一开始就上太多 Agent。推荐分阶段推进。

### 7.1 MVP 版本：单主控 Agent + 工具链

第一期最实用的方案：

- 一个主控 Agent
- 外加一组确定性的执行工具

主控 Agent 负责：

- 读取用户需求
- 选择改装策略
- 组织执行步骤
- 调用 LLM 输出结构化需求
- 选择模板 / 参数 / 脚本
- 汇总验证结果

这版优点：

- 简单
- 易调试
- 成本低
- 最适合先把系统跑起来

### 7.2 第二期：双 Agent

推荐拆成两个核心 Agent：

1. `Planner Agent`
  - 负责需求理解和改装方案生成
2. `Builder Agent`
  - 负责脚本选择、脚本生成、执行和验证

这样可以把“创意规划”和“工程执行”分开。

### 7.3 第三期：多 Agent

成熟后可以拆成以下角色：

- `Intent Agent`
  - 把用户需求转成结构化意图
- `Constraint Agent`
  - 根据枪03的结构与边界判断哪些请求可做、哪些风险高
- `Design Agent`
  - 生成改装方案
- `Script Agent`
  - 生成或选取具体执行脚本
- `Execution Agent`
  - 在沙箱中运行
- `Validation Agent`
  - 解析输出并验收
- `Narration Agent`
  - 生成 README、meta 和变更说明

但这一版适合在模板和工具链都稳定后再做。

## 8. 推荐的目录规划

建议在：

- `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/Modification_System`

下新增以下结构：

```text
Modification_System/
├── docs/
├── agents/
│   ├── orchestrator.py
│   ├── planner_agent.py
│   ├── builder_agent.py
│   └── validator_agent.py
├── engine/
│   └── llm_client.py
├── prompts/
│   ├── intent_parser.md
│   ├── planner.md
│   └── script_generator.md
├── schemas/
│   ├── modification_request.schema.json
│   ├── modification_plan.schema.json
│   └── validation_report.schema.json
├── templates/
│   ├── dragon_armor.py
│   ├── horned_variant.py
│   ├── spine_variant.py
│   ├── emissive_recolor.py
│   └── material_theme_swap.py
├── validators/
│   ├── gltf_validator.py
│   ├── glb_validator.py
│   ├── viewer_validator.py
│   └── asset_diff_validator.py
├── sandbox/
│   ├── runner.py
│   └── policies.py
├── base_weapon_cache/
│   └── optional_mirror_of_枪03_枪的模型
├── runs/
├── variants/
├── logs/
└── 参考脚本/
    └── test_gpt.py
```

补充说明：

- `base_weapon_cache/` 只是可选缓存层，不是权威输入源
- 权威输入源仍然是：
  - `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/枪的模型`
- `variants/` 中每一个子目录都应当长得像一个新的 `修改优化XX`

## 9. 建议的数据流

建议整条数据流如下：

### 步骤 1

用户输入一句话需求。

### 步骤 2

系统读取基础枪模板目录：

- `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/枪的模型`

### 步骤 3

Intent Parser 调用 LLM，把自然语言转成结构化需求对象。

### 步骤 4

Planner 根据结构化需求输出执行计划。

计划内容应包括：

- 主题
- 目标部件
- 改装类型
- 风险等级
- 推荐模板
- 是否需要新脚本
- 验证重点

### 步骤 5

系统创建一次运行目录，例如：

- `runs/2026-04-11_001_black_gold_dragon/`

### 步骤 6

复制基础模型到运行目录，并按 `修改优化03` 模板准备正式变体目录骨架。

### 步骤 7

执行器开始改装：

- 如果是模板类需求，就执行模板脚本
- 如果是参数化类需求，就把规划结果转成参数调用脚本
- 如果是新需求，就让 LLM 生成脚本，再沙箱运行

### 步骤 8

验证器读取运行产物，做自动验收。

### 步骤 9

若验证成功：

- 生成 README
- 更新 meta
- 输出正式变体目录

若验证失败：

- 记录错误
- 尝试回退
- 可触发一次自动修复重试

## 10. 改装能力分类建议

为了让系统先稳定，建议把所有用户需求映射到有限能力集。

### 10.1 材质改装

支持内容：

- 改主色
- 改金属度
- 改粗糙度
- 改玻璃透明度
- 改发光颜色
- 改发光强度

适合需求：

- “改成黑金风格”
- “发光改蓝色”
- “整体更磨砂一些”

### 10.2 贴图增强

支持内容：

- 重着色
- 叠加图案
- 简单污损 / 烧蚀 / 纹理增强

适合需求：

- “做冰霜裂纹”
- “增加熔岩感”
- “做金属磨损”

### 10.3 外挂几何改装

支持内容：

- 顶部龙脊
- 左右鳞片
- 骨架肋片
- 龙头前额
- 角、尖刺、护甲片

适合需求：

- “枪身长出龙鳞”
- “增加恶魔尖刺”
- “枪口改得更像龙头”

### 10.4 结构级改装

支持内容：

- 增减附加装饰节点
- 给 `ReceiverGroup`、`MagazineGroup` 增挂新 mesh
- 对既有动画兼容

不建议第一期支持：

- 深度修改原 receiver 顶点拓扑
- 重新拆出骨骼或枪机结构

## 11. 对枪03的专用知识库建议

因为系统只服务枪03，所以建议建立一份专用知识库文件。

建议内容包括：

- 基础目录路径
- 核心节点名
- 主要 mesh / material 名
- 已知动画名
- 可安全挂载新几何的位置
- 已有成功改装案例

推荐知识条目示例：

```json
{
  "weapon_id": "weapon03_red_dragon_tech_sniper",
  "base_path": ".../枪03/枪的模型",
  "groups": ["ReceiverGroup", "MagazineGroup"],
  "preserved_animations": ["idle", "fire", "reload", "ads", "sprint"],
  "safe_additive_targets": ["ReceiverGroup"],
  "known_variant_examples": [
    "修改优化01",
    "修改优化02",
    "修改优化03"
  ]
}
```

## 12. LLM 使用方式建议

### 12.1 不要让 LLM 直接控制所有细节

LLM 最适合做：

- 自然语言理解
- 风格意图抽象
- 方案推荐
- 生成结构化计划
- 生成文档说明

LLM 不适合在第一期直接完全自由生成所有 3D 几何逻辑。

### 12.2 推荐的三段式 Prompt 流程

推荐分成三次调用：

1. `Intent Parse`
  - 用户话术 -> 结构化改装需求
2. `Plan Generate`
  - 结构化需求 -> 可执行改装计划
3. `Script Generate`
  - 仅在需要新脚本时触发

### 12.3 test_gpt.py 的改造建议

建议将：

- `/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪03/Modification_System/参考脚本/test_gpt.py`

改造成：

- `engine/llm_client.py`

统一提供方法：

```python
response = llm_client.generate_json(
    developer_prompt=...,
    user_prompt=...,
    schema=...
)
```

同时补上：

- 超时与重试
- 结构化 JSON 校验
- 流式可选
- 请求日志
- 响应日志
- 环境变量读取 API Key

## 13. 沙箱执行设计

### 13.1 执行原则

所有改装脚本都应在沙箱目录执行，不允许直接写基础目录。

建议流程：

1. 复制基础枪目录到运行目录
2. 在运行目录生成改装脚本
3. 在运行目录执行脚本
4. 只允许写运行目录
5. 验证通过后，再把结果整理为正式变体目录

补充要求：

- `runs/` 只负责执行
- `variants/` 才是正式交付
- `variants/` 中的正式目录必须对齐 `修改优化03` 的文件布局

### 13.2 执行对象

允许执行的内容包括：

- Python 脚本
- 贴图处理脚本
- glTF 打包脚本

### 13.3 执行限制

建议限制：

- 最大执行时长
- 最大文件生成数
- 最大输出目录体积
- 禁止删除基础目录
- 禁止访问基础目录外的无关路径

## 14. 结果验证设计

建议至少包含以下验证器。

### 14.1 结构验证

检查：

- `model.gltf` JSON 可解析
- `bufferViews / accessors / buffers` 引用完整
- 新增 mesh / material / node 是否存在

### 14.2 加载验证

检查：

- `model.glb` 可通过 `pygltflib` 加载
- viewer data 能成功生成

### 14.3 改装目标验证

检查：

- 若需求要求增加鳞片，是否真的新增几何
- 若要求改发光，emissive 是否变化
- 若要求保留镜片，scope glass 是否未破坏

### 14.4 回归验证

检查：

- 原有动画是否仍存在
- 基础枪的核心部件是否未丢失
- `ReceiverGroup`、`MagazineGroup` 层级是否仍正常

### 14.5 目录模板验证

因为本系统的目标不是只产出一个可加载 glTF，而是产出一个“像 修改优化03 那样完整的正式改装目录”，所以必须增加目录模板验证。

检查项建议包括：

- 是否存在 `model.gltf`
- 是否存在 `buffer.bin`
- 是否存在 `model.glb`
- 是否存在 `viewer.html`
- 是否存在 `viewer-data.js`
- 是否存在 `viewer-assets/`
- 是否存在 `weapon03_meta.json`
- 是否存在 `README.md`
- 是否存在构建脚本
- 是否存在实现过程文档
- 是否存在预览图

## 15. 推荐的输出文档与运行记录

每次运行建议记录：

- `request.txt`
- `intent.json`
- `plan.json`
- `execution_log.txt`
- `validation_report.json`
- `README.md`

这样后续你可以回看：

- 用户当时说了什么
- LLM 是怎么理解的
- 系统为什么这么改
- 生成失败时卡在哪一步

正式变体目录中还应保留：

- 变体构建脚本
- 变体实现过程文档
- 面向交付的 README

## 16. MVP 推荐能力范围

为了让第一版尽快落地，建议先只支持以下需求：

### 16.1 第一批支持

- 改色系
- 改发光色
- 改金属度和粗糙度
- 在 `ReceiverGroup` 上增加尖刺、龙脊、鳞片、装甲片
- 生成新的独立版本目录，且目录结构对齐 `修改优化03`

### 16.2 暂缓支持

- 改动画结构
- 深度修改弹匣几何
- 自动重做镜片折射
- 复杂贴图重绘
- 深度修改原始 receiver 顶点

## 17. 推荐的实施阶段

### 阶段 1：搭基础骨架

目标：

- 能接收一句话需求
- 能调用 LLM 输出结构化 JSON
- 能复制基础目录到运行目录
- 能调用固定模板做 1 到 2 种改装
- 能输出一个结构对齐 `修改优化03` 的正式变体目录

### 阶段 2：做模板库

目标：

- 沉淀若干可复用模板
- 支持多个主题变体
- 支持参数化几何外挂

### 阶段 3：做验证和回滚

目标：

- 自动校验 glTF / GLB
- 自动生成 validation report
- 支持失败回退与重试

### 阶段 4：引入多 Agent

目标：

- 拆分规划、执行、验证职责
- 提高复杂需求处理能力

## 18. 风险与对策

### 风险 1：用户需求太模糊

例如：

- “帮我改得更帅一点”

对策：

- LLM 输出低置信度
- 系统触发一次补充确认
- 或按默认主题库给出候选方案

### 风险 2：LLM 生成脚本不稳定

对策：

- 优先模板化
- 脚本生成前先输出计划 JSON
- 运行前做静态检查
- 运行后做结构验证

### 风险 3：改装破坏 viewer 或 GLB

对策：

- 执行后统一重建 `viewer-data.js`
- 强制执行 GLB 加载验证

### 风险 4：最终目录不像“修改优化03”那样完整

对策：

- 在系统中固化正式变体目录模板
- 交付前执行目录模板验证
- 缺失文件时自动补生成 README / meta / preview / viewer-data
- 构建脚本和实现过程文档作为正式交付必选项

### 风险 5：API Key 安全问题

当前参考脚本中密钥是写死的，这不适合正式系统。

对策：

- 改为环境变量
- 日志中屏蔽敏感字段

### 风险 6：系统越做越像“通用建模器”

对策：

- 始终坚持“枪03专用”
- 优先建设枪03的变体模板库
- 不要过早抽象成全武器通用系统

## 19. 推荐的首版成功标准

如果系统达到以下标准，就可以认为 MVP 成功：

- 用户输入一句中文需求
- 系统可自动生成一次运行目录
- 可成功输出一个结构对齐 `修改优化03` 的正式变体目录
- 改装后的 `model.gltf` / `model.glb` 可成功加载
- viewer 可直接打开
- 预览图可生成
- README 和 meta 会自动更新
- 正式变体目录中包含构建脚本和实现过程文档
- 基础枪目录完全不被污染
- 至少支持 3 类稳定改装：
  - 改发光
  - 改材质风格
  - 外挂龙鳞或尖刺

## 20. 一句话总结

这个 Agent 系统最合理的路线不是“让大模型直接凭一句话自由捏 3D 模型”，而是：

- 以 `枪03` 这一把枪为固定对象
- 以现有基础资源目录为模板
- 先用 LLM 做需求理解和规划
- 再通过模板化脚本、参数化几何和受控沙箱执行完成改装
- 最后自动验证并交付独立版本

也就是说，系统的本质应当是：

“一个由 LLM 驱动的、面向枪03的受控模型改装流水线。”