# 用 SQL 查游戏数据

拆解脚本是为「一次回答一个问题」写的。换一个问题就要改 Python、重跑、再看输出。

数据装进 SQLite 之后，新问题基本就是一句 SQL 的事——不用改代码，不用等脚本跑完。

## 为什么放在标准库里

`sqlite3` 是 Python 自带的。这一层**没有引入任何第三方依赖**，和工具包原本的承诺一致。

只有「从 xlsx 建库」那一步需要 `openpyxl`（读 Excel 绕不开），之后的查询全在标准库里跑。

## 建库

```bash
python tools/build_db.py <动作数据表.xlsx> data/game.db
```

输出：

```
已写入 data/game.db
  actions   5425 行
  enemies   1533 行
```

## 查询

先看有哪些预设：

```bash
python cli.py sql --db data/game.db --list
```

跑一个：

```bash
python cli.py sql --db data/game.db --query poise_top
```

```
== 削韧最高的 15 个动作 ==
action               poise  conc
-------------------  -----  ----
大招-一日唱          405    0
大招-伤害            400    0
...
```

也可以直接给 SQL：

```bash
python cli.py sql --db data/game.db --sql "SELECT action, poise FROM actions
  WHERE poise > 300 ORDER BY poise DESC LIMIT 10"
```

## 两张表

### actions

| 字段 | 含义 | 来源 |
|---|---|---|
| sheet | 来源工作表（角色-女 / 角色-男） | — |
| grp | 体型骨架，**不是角色名** | 名称列 |
| action | 动作名 | 动作列 |
| startup | 发生帧 | 发生帧列 |
| duration | 持续帧 | 持续帧列 |
| hitstop | 顿帧 | 自身顿帧列 |
| iframe_start | 无敌起始帧 | 无敌帧起始 |
| iframe_frames | 无敌帧数 | 无敌帧数 |
| end_frame | 动作结束帧 | 动作结束帧 |
| poise | 削韧值 | 削韧值 |
| ult | 大招回收（共鸣能量基础值） | 大招回收 |
| concerto | 协奏回收 | 协奏回收 |

> `grp` 那一列是体型骨架（通用-大 / 通用-中 / 通用-小），不是角色名。所以按角色分组做不了——这一点在第 01 篇里已经踩过。

### enemies

| 字段 | 含义 |
|---|---|
| name | 敌人名（同名可能是不同难度档） |
| level | 等级 |
| hp | 生命值 |
| defense | 防御 |

## 预设查询

| 名字 | 回答什么问题 |
|---|---|
| `poise_top` | 哪些动作削韧最高（已排除 9999/100000 这类哨兵值） |
| `iframe_top` | 无敌帧最长的动作 |
| `recovery_top` | 后摇最长的动作（结束帧 − 发生帧 − 持续帧） |
| `energy_ratio` | 大招回收 ÷ 协奏回收 的比值分布 |
| `zero_poise` | 完全不给削韧的动作占比 |
| `big_both` | 同时给高协奏与高大招回收的动作 |
| `enemy_levels` | 敌人血量按等级汇总 |
| `enemy_tough` | 同一等级里被多个敌人共用的血量档位 |

## 怎么加一个预设

在 `numerics/store.py` 的 `PRESETS` 里加一项：

```python
"my_query": {
    "title": "一句话说清它回答什么",
    "sql": """
        SELECT ...
        FROM actions
        WHERE ...
    """,
},
```

然后 `--list` 里就会出现它。`tests/test_store.py` 里有一条测试会遍历所有预设，语法写错会当场失败。

## 一个坑

`deconstructions/_shared.py` 用的字段名和表字段名不一样（`group` / `hitstop_self` / `iframe_dur` / `end`）。`numerics/store.py` 里有一张 `ACTION_ALIASES` 显式对齐它们。

**第一次建库时就是漏了这张表**，结果 `end_frame` 全是 NULL，`recovery_top` 查出来是空——但没有任何报错。所以建库后建议随手验一下：

```sql
SELECT COUNT(*) FROM actions WHERE end_frame IS NOT NULL;   -- 应该是 1886 左右
```
