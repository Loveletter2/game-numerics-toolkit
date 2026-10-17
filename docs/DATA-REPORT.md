# 数据拆解汇总报告

由 `python deconstructions/run_all.py` 自动生成，内容全部来自本地数据表，不含手写数字。

总耗时 10.9 秒，共 14 节。

## 读取动作帧表

耗时 9.8s，状态 ok

```json
{
 "actions": 5425,
 "sheets": [
  "角色-女",
  "角色-男"
 ]
}
```

## 01 无敌窗口

耗时 0.0s，状态 ok

```json
{
 "windows": [
  {
   "action": "极限闪避-前",
   "frames": 78.0,
   "seconds": 1.3,
   "samples": 19,
   "consistent": false
  },
  {
   "action": "极限闪避-后",
   "frames": 78.0,
   "seconds": 1.3,
   "samples": 19,
   "consistent": false
  },
  {
   "action": "赫卡忒-极限闪避",
   "frames": 78.0,
   "seconds": 1.3,
   "samples": 1,
   "consistent": true
  },
  {
   "action": "闪避反击",
   "frames": 77.0,
   "seconds": 1.283,
   "samples": 9,
   "consistent": false
  },
  {
   "action": "闪避反击-1",
   "frames": 76.0,
   "seconds": 1.267,
   "samples": 6,
   "consistent": false
  },
  {
   "action": "观测极限闪避-前",
   "frames": 59.0,
   "seconds": 0.983,
   "samples": 1,
   "consistent": true
  },
  {
   "action": "观测极限闪避-后",
   "frames": 59.0,
   "seconds": 0.983,
   "samples": 1,
   "consistent": true
  },
  {
   "action": "凌霄极限闪避-前",
   "frames": 55.0,
   "seconds": 0.917,
   "samples": 1,
   "consistent": true
  }
 ]
}
```

## 02 协奏能量

耗时 0.0s，状态 ok

```json
{
 "row_count": 5425,
 "with_concerto": 2816,
 "positive": 2806,
 "negative": 10,
 "buckets": {
  "≤0（消耗）": 10,
  "0～1": 868,
  "1～2": 765,
  "2～5": 633,
  "5～10": 364,
  "10～20": 153,
  "20～50": 23,
  ">50": 0
 },
 "common_values": [
  {
   "value": 10.0,
   "count": 178
  },
  {
   "value": 1.0,
   "count": 98
  },
  {
   "value": 20.0,
   "count": 91
  },
  {
   "value": 2.0,
   "count": 52
  },
  {
   "value": 5.0,
   "count": 44
  },
  {
   "value": 1.5,
   "count": 40
  },
  {
   "value": 0.7,
   "count": 36
  },
  {
   "value": 0.3,
   "count": 35
  },
  {
   "value": 0.5,
   "count": 31
  },
  {
   "value": 1.34,
   "count": 27
  },
  {
   "value": 1.05,
   "count": 26
  },
  {
   "value": 0.54,
   "count": 26
  },
  {
   "value": 6.0,
   "count": 24
  },
  {
   "value": 4.0,
   "count": 24
  }
 ],
 "top_actions": [
  {
   "action": "缭乱-1",
   "value": 50.0
  },
  {
   "action": "缭乱-1",
   "value": 50.0
  },
  {
   "action": "电锯A4",
   "value": 45.0
  },
  {
   "action": "强化重击-前置",
   "value": 40.0
  },
  {
   "action": "显明告解-前置",
   "value": 40.0
  },
  {
   "action": "E-C6反击",
   "value": 33.0
  },
  {
   "action": "大招-前置",
   "value": 32.0
  },
  {
   "action": "满能空中普攻-1",
   "value": 31.0
  }
 ],
 "negative_actions": [
  {
   "action": "地面E-椿花魔女",
   "value": -70.0
  },
  {
   "action": "空中E-椿花魔女",
   "value": -70.0
  },
  {
   "action": "E3-一日花",
   "value": -70.0
  },
  {
   "action": "E3-C2一日花",
   "value": -70.0
  },
  {
   "action": "强化E-长按超负荷",
   "value": -60.0
  },
  {
   "action": "空中强化E-长按",
   "value": -60.0
  },
  {
   "action": "E3-C3荷蓑出林",
   "value": -60.0
  },
  {
   "action": "强化E-长按超负荷",
   "value": -60.0
  }
 ],
 "concerto_cap": 100
}
```

## 03 削韧值

耗时 0.0s，状态 ok

```json
{
 "row_count": 5425,
 "with_poise": 3311,
 "normal": 3309,
 "sentinels": 2,
 "median": 30.0,
 "max_normal": 405.0,
 "common": [
  {
   "value": 100.0,
   "count": 107
  },
  {
   "value": 30.0,
   "count": 92
  },
  {
   "value": 50.0,
   "count": 85
  },
  {
   "value": 40.0,
   "count": 83
  },
  {
   "value": 5.0,
   "count": 66
  },
  {
   "value": 10.0,
   "count": 60
  },
  {
   "value": 15.0,
   "count": 60
  },
  {
   "value": 200.0,
   "count": 56
  },
  {
   "value": 60.0,
   "count": 53
  },
  {
   "value": 20.0,
   "count": 53
  },
  {
   "value": 80.0,
   "count": 50
  },
  {
   "value": 400.0,
   "count": 43
  }
 ],
 "by_category": [
  {
   "category": "共鸣解放",
   "count": 152,
   "median": 100.0,
   "max": 405.0
  },
  {
   "category": "变奏/延奏",
   "count": 12,
   "median": 100.0,
   "max": 200.0
  },
  {
   "category": "闪避/反击",
   "count": 49,
   "median": 45.0,
   "max": 150.0
  },
  {
   "category": "共鸣技能",
   "count": 787,
   "median": 40.0,
   "max": 400.0
  },
  {
   "category": "重击",
   "count": 411,
   "median": 28.8,
   "max": 280.0
  },
  {
   "category": "普攻",
   "count": 1535,
   "median": 26.7,
   "max": 384.0
  },
  {
   "category": "其他",
   "count": 363,
   "median": 26.7,
   "max": 400.0
  }
 ],
 "top_actions": [
  {
   "action": "大招-一日唱",
   "value": 405.0,
   "cat": "共鸣解放"
  },
  {
   "action": "大招",
   "value": 400.0,
   "cat": "共鸣解放"
  },
  {
   "action": "大招-伤害",
   "value": 400.0,
   "cat": "共鸣解放"
  },
  {
   "action": "大招-伤害",
   "value": 400.0,
   "cat": "共鸣解放"
  },
  {
   "action": "大招拔刀-伤害",
   "value": 400.0,
   "cat": "共鸣解放"
  },
  {
   "action": "大招-伤害",
   "value": 400.0,
   "cat": "共鸣解放"
  },
  {
   "action": "大招-伤害",
   "value": 400.0,
   "cat": "共鸣解放"
  },
  {
   "action": "大招-伤害",
   "value": 400.0,
   "cat": "共鸣解放"
  },
  {
   "action": "大招-C0伤害",
   "value": 400.0,
   "cat": "共鸣解放"
  },
  {
   "action": "大招-C3伤害",
   "value": 400.0,
   "cat": "共鸣解放"
  }
 ]
}
```

## 04 后摇

耗时 0.0s，状态 ok

```json
{
 "row_count": 5425,
 "usable": 1593,
 "median_frames": 70.0,
 "median_seconds": 1.167,
 "by_category": [
  {
   "category": "普攻",
   "count": 44,
   "median_length": 40.0,
   "median_recovery": 21.0,
   "median_pct": 57.1
  },
  {
   "category": "变奏/延奏",
   "count": 15,
   "median_length": 180.0,
   "median_recovery": 62.0,
   "median_pct": 36.7
  },
  {
   "category": "其他",
   "count": 852,
   "median_length": 69.0,
   "median_recovery": 22.0,
   "median_pct": 36.1
  },
  {
   "category": "闪避/反击",
   "count": 91,
   "median_length": 50.0,
   "median_recovery": 17.0,
   "median_pct": 35.0
  },
  {
   "category": "重击",
   "count": 179,
   "median_length": 69.0,
   "median_recovery": 24.0,
   "median_pct": 34.6
  },
  {
   "category": "共鸣技能",
   "count": 324,
   "median_length": 78.0,
   "median_recovery": 22.0,
   "median_pct": 31.0
  },
  {
   "category": "共鸣解放",
   "count": 88,
   "median_length": 211.0,
   "median_recovery": 22.0,
   "median_pct": 16.8
  }
 ],
 "longest_recovery": [
  {
   "action": "延奏-常规炮台",
   "cat": "变奏/延奏",
   "recovery": 779.0,
   "pct": 92.7
  },
  {
   "action": "延奏-飞仙翾舞3",
   "cat": "变奏/延奏",
   "recovery": 507.0,
   "pct": 33.8
  },
  {
   "action": "待机",
   "cat": "其他",
   "recovery": 465.0,
   "pct": 36.3
  },
  {
   "action": "空中A2-音影落地",
   "cat": "其他",
   "recovery": 371.0,
   "pct": 94.6
  },
  {
   "action": "黄-强化疾奔-强光",
   "cat": "其他",
   "recovery": 344.0,
   "pct": 68.8
  },
  {
   "action": "E3-P1伤害",
   "cat": "共鸣技能",
   "recovery": 309.0,
   "pct": 81.7
  },
  {
   "action": "待机动作1-吃橘子",
   "cat": "其他",
   "recovery": 275.0,
   "pct": 39.0
  },
  {
   "action": "运气-持续1",
   "cat": "其他",
   "recovery": 271.0,
   "pct": 71.1
  }
 ],
 "hitstop_median": 3.0,
 "hitstop_max": 56.0
}
```

## 09 判定范围

耗时 0.0s，状态 ok

```json
{
 "rows": 3982,
 "shapes": {
  "矩形": 2508,
  "圆柱": 1136,
  "球形": 298,
  "扇形": 34,
  "指定目标": 6
 },
 "by_category": {
  "闪避/反击": {
   "矩形": 110,
   "圆柱": 8,
   "球形": 6
  },
  "其他": {
   "矩形": 1433,
   "圆柱": 584,
   "球形": 135,
   "扇形": 9,
   "指定目标": 6
  },
  "普攻": {
   "矩形": 37,
   "圆柱": 17,
   "球形": 5
  },
  "重击": {
   "矩形": 316,
   "圆柱": 120,
   "球形": 24,
   "扇形": 6
  },
  "共鸣技能": {
   "矩形": 501,
   "圆柱": 293,
   "球形": 99,
   "扇形": 11
  },
  "共鸣解放": {
   "矩形": 85,
   "圆柱": 78,
   "球形": 25,
   "扇形": 8
  },
  "变奏/延奏": {
   "圆柱": 36,
   "矩形": 26,
   "球形": 4
  }
 },
 "rect_length_median": 240.0,
 "rect_length_min": 5.0,
 "rect_length_max": 4000.0,
 "cyl_radius_median": 600.0,
 "cyl_radius_max": 5000.0,
 "largest": [
  {
   "action": "被动1-雪绣1层",
   "shape": "球形",
   "dims": [
    5000.0,
    0.0,
    0.0
   ],
   "volume": 523600000000
  },
  {
   "action": "被动1-雪绣3层",
   "shape": "球形",
   "dims": [
    5000.0,
    0.0,
    0.0
   ],
   "volume": 523600000000
  },
  {
   "action": "C6被动1-雪锈2层",
   "shape": "球形",
   "dims": [
    5000.0,
    0.0,
    0.0
   ],
   "volume": 523600000000
  },
  {
   "action": "千面魅影-转化标记",
   "shape": "球形",
   "dims": [
    5000.0,
    0.0,
    0.0
   ],
   "volume": 523600000000
  },
  {
   "action": "千面魅影-刷新印记",
   "shape": "球形",
   "dims": [
    5000.0,
    0.0,
    0.0
   ],
   "volume": 523600000000
  },
  {
   "action": "审判之雷-判断",
   "shape": "球形",
   "dims": [
    5000.0,
    0.0,
    0.0
   ],
   "volume": 523600000000
  },
  {
   "action": "音律独奏",
   "shape": "球形",
   "dims": [
    5000.0,
    0.0,
    0.0
   ],
   "volume": 523600000000
  },
  {
   "action": "大招-音律独奏",
   "shape": "球形",
   "dims": [
    5000.0,
    0.0,
    0.0
   ],
   "volume": 523600000000
  }
 ]
}
```

## 06 敌人血量

耗时 0.3s，状态 ok

```json
{
 "row_count": 1533,
 "levels": [
  40,
  45,
  50,
  55,
  60,
  65,
  66,
  70,
  75,
  80,
  84,
  85,
  87,
  88,
  90,
  93,
  95,
  100,
  110,
  120
 ],
 "curve": [
  {
   "level": 40,
   "count": 30,
   "median_hp": 33188,
   "ttk_seconds": 0.4
  },
  {
   "level": 60,
   "count": 32,
   "median_hp": 162659,
   "ttk_seconds": 1.8
  },
  {
   "level": 80,
   "count": 68,
   "median_hp": 450355,
   "ttk_seconds": 5.0
  },
  {
   "level": 90,
   "count": 217,
   "median_hp": 1344542,
   "ttk_seconds": 14.8
  },
  {
   "level": 100,
   "count": 812,
   "median_hp": 336022,
   "ttk_seconds": 3.7
  },
  {
   "level": 110,
   "count": 34,
   "median_hp": 9111437,
   "ttk_seconds": 100.5
  },
  {
   "level": 120,
   "count": 34,
   "median_hp": 13849374,
   "ttk_seconds": 152.7
  }
 ],
 "resistance_histogram": {
  "0.1": 4457,
  "0.2": 4810,
  "0.4": 702,
  "0.5": 197,
  "0.6": 403,
  "0.8": 156,
  "1.0": 6
 },
 "dps_assumption": 90695.0,
 "tiers": [
  {
   "level": 85,
   "hp": 344939,
   "shared_by": 3,
   "ttk": 3.8
  },
  {
   "level": 87,
   "hp": 886432,
   "shared_by": 5,
   "ttk": 9.8
  },
  {
   "level": 88,
   "hp": 63851,
   "shared_by": 3,
   "ttk": 0.7
  },
  {
   "level": 90,
   "hp": 630254,
   "shared_by": 12,
   "ttk": 6.9
  },
  {
   "level": 95,
   "hp": 529394,
   "shared_by": 3,
   "ttk": 5.8
  },
  {
   "level": 100,
   "hp": 88014,
   "shared_by": 70,
   "ttk": 1.0
  },
  {
   "level": 110,
   "hp": 6815251,
   "shared_by": 11,
   "ttk": 75.1
  },
  {
   "level": 120,
   "hp": 13849374,
   "shared_by": 14,
   "ttk": 152.7
  }
 ]
}
```

## 14 敌人韧性

耗时 0.0s，状态 ok

```json
{
 "rows": 1533,
 "toughness_values": {
  "2000": 552,
  "40": 395,
  "800": 201,
  "1000": 94,
  "9999": 90,
  "150": 82,
  "500": 44,
  "200": 27,
  "900": 24,
  "400": 10,
  "600": 7,
  "50": 6,
  "80": 1
 },
 "recover_values": {
  "1": 387,
  "100": 311,
  "20": 248,
  "50": 205,
  "5": 69,
  "10": 50,
  "6.5": 46,
  "500": 45,
  "0": 39,
  "30": 36,
  "5000": 28,
  "22.5": 24,
  "10000": 23,
  "8": 21,
  "2": 1
 },
 "by_level": [
  {
   "level": 40,
   "count": 30,
   "median": 2000
  },
  {
   "level": 60,
   "count": 32,
   "median": 2000
  },
  {
   "level": 80,
   "count": 68,
   "median": 1000
  },
  {
   "level": 90,
   "count": 217,
   "median": 1000
  },
  {
   "level": 100,
   "count": 812,
   "median": 800
  },
  {
   "level": 110,
   "count": 34,
   "median": 2000
  },
  {
   "level": 120,
   "count": 34,
   "median": 2000
  }
 ],
 "cost": [
  {
   "toughness": 40,
   "ults": 0.1,
   "skills": 1.0,
   "normals": 1.5
  },
  {
   "toughness": 150,
   "ults": 0.4,
   "skills": 3.8,
   "normals": 5.6
  },
  {
   "toughness": 500,
   "ults": 1.2,
   "skills": 12.5,
   "normals": 18.7
  },
  {
   "toughness": 800,
   "ults": 2.0,
   "skills": 20.0,
   "normals": 30.0
  },
  {
   "toughness": 1000,
   "ults": 2.5,
   "skills": 25.0,
   "normals": 37.5
  },
  {
   "toughness": 2000,
   "ults": 5.0,
   "skills": 50.0,
   "normals": 74.9
  }
 ],
 "sentinel": 9999
}
```

## 11 更新日志

耗时 0.2s，状态 ok

```json
{
 "rows": 498,
 "versions": 91,
 "first": [
  "24.06.28",
  "1.1.0-"
 ],
 "last": [
  "26.9.28",
  "3.7.5-3.7.6"
 ],
 "median_per_version": 3,
 "max_per_version": 47,
 "top_chars": [
  [
   "千咲",
   42
  ],
  [
   "赞妮",
   23
  ],
  [
   "西格莉卡",
   18
  ],
  [
   "莫宁",
   15
  ],
  [
   "琳奈",
   13
  ],
  [
   "今汐",
   11
  ],
  [
   "仇远",
   11
  ],
  [
   "爱弥斯",
   10
  ],
  [
   "穗穗",
   9
  ],
  [
   "坎特蕾拉",
   8
  ]
 ],
 "kinds": {
  "其他": 157,
  "时间与帧": 87,
  "索敌/优先级": 61,
  "判定与子弹": 56,
  "伤害与倍率": 40,
  "敌人数值": 33,
  "削韧与韧性": 20,
  "无敌与闪避": 19,
  "弹刀/格挡": 18,
  "位置与偏移": 4,
  "范围与大小": 3
 },
 "by_year": {
  "24": 93,
  "25": 225,
  "26": 180
 }
}
```

## 05 武器白值

耗时 0.0s，状态 ok

```json
{
 "weapon_count": 133,
 "by_rank": [
  {
   "rank": 1,
   "label": "1★",
   "count": 5,
   "min": 250,
   "median": 250,
   "max": 250
  },
  {
   "rank": 2,
   "label": "2★",
   "count": 5,
   "min": 275,
   "median": 275,
   "max": 275
  },
  {
   "rank": 3,
   "label": "3★",
   "count": 21,
   "min": 300,
   "median": 300,
   "max": 325
  },
  {
   "rank": 4,
   "label": "4★",
   "count": 43,
   "min": 338,
   "median": 412,
   "max": 462
  },
  {
   "rank": 5,
   "label": "5★",
   "count": 50,
   "min": 412,
   "median": 588,
   "max": 675
  }
 ],
 "five_minus_four_median": 176,
 "scenarios": [
  {
   "atk_pct": 0.0,
   "final_gap": 176
  },
  {
   "atk_pct": 0.5,
   "final_gap": 264
  },
  {
   "atk_pct": 1.0,
   "final_gap": 352
  },
  {
   "atk_pct": 1.5,
   "final_gap": 440
  },
  {
   "atk_pct": 2.0,
   "final_gap": 528
  }
 ],
 "substats": {
  "1★": {
   "ATK": 5
  },
  "2★": {
   "ATK": 5
  },
  "3★": {
   "ATK": 12,
   "DEF": 3,
   "Energy Regen": 3,
   "HP": 2,
   "Crit. DMG": 1
  },
  "5★": {
   "ATK": 3,
   "Crit. DMG": 13,
   "Crit. Rate": 25,
   "Energy Regen": 7,
   "HP": 2
  },
  "4★": {
   "Energy Regen": 9,
   "DEF": 2,
   "ATK": 23,
   "Crit. Rate": 5,
   "Crit. DMG": 3,
   "HP": 1
  }
 }
}
```

## 07 角色成长

耗时 0.1s，状态 ok

```json
{
 "characters": 60,
 "analysed": 60,
 "by_rarity": [
  {
   "rarity": 5,
   "count": 49,
   "median_multiple": 12.5,
   "min_multiple": 12.5,
   "max_multiple": 12.5,
   "median_atk90": 425.0,
   "min_atk90": 287.5,
   "max_atk90": 462.5
  },
  {
   "rarity": 4,
   "count": 11,
   "median_multiple": 12.5,
   "min_multiple": 12.5,
   "max_multiple": 12.5,
   "median_atk90": 262.5,
   "min_atk90": 212.5,
   "max_atk90": 337.5
  }
 ],
 "curve_5star": [
  {
   "level": 1,
   "median_atk": 34.0,
   "count": 49
  },
  {
   "level": 20,
   "median_atk": 113.9,
   "count": 49
  },
  {
   "level": 40,
   "median_atk": 196.7,
   "count": 49
  },
  {
   "level": 60,
   "median_atk": 305.0,
   "count": 49
  },
  {
   "level": 80,
   "median_atk": 396.3,
   "count": 49
  },
  {
   "level": 90,
   "median_atk": 425.0,
   "count": 49
  }
 ],
 "jump_count": 120,
 "top_jumps": [
  {
   "name": "散华",
   "level": 20,
   "prev_level": 19,
   "ratio": 1.331,
   "atk_prev": 55.3696,
   "atk_cur": 73.7242
  },
  {
   "name": "白芷",
   "level": 20,
   "prev_level": 19,
   "ratio": 1.331,
   "atk_prev": 42.7856,
   "atk_cur": 56.9687
  },
  {
   "name": "凌阳",
   "level": 20,
   "prev_level": 19,
   "ratio": 1.331,
   "atk_prev": 88.088,
   "atk_cur": 117.2885
  },
  {
   "name": "折枝",
   "level": 20,
   "prev_level": 19,
   "ratio": 1.331,
   "atk_prev": 75.504,
   "atk_cur": 100.533
  },
  {
   "name": "釉瑚",
   "level": 20,
   "prev_level": 19,
   "ratio": 1.331,
   "atk_prev": 52.8528,
   "atk_cur": 70.3731
  },
  {
   "name": "珂莱塔",
   "level": 20,
   "prev_level": 19,
   "ratio": 1.331,
   "atk_prev": 93.1216,
   "atk_cur": 123.9907
  },
  {
   "name": "绯雪",
   "level": 20,
   "prev_level": 19,
   "ratio": 1.331,
   "atk_prev": 93.1216,
   "atk_cur": 123.9907
  },
  {
   "name": "洛瑟菈",
   "level": 20,
   "prev_level": 19,
   "ratio": 1.331,
   "atk_prev": 75.504,
   "atk_cur": 100.533
  },
  {
   "name": "穗穗",
   "level": 20,
   "prev_level": 19,
   "ratio": 1.331,
   "atk_prev": 57.8864,
   "atk_cur": 77.0753
  },
  {
   "name": "炽霞",
   "level": 20,
   "prev_level": 19,
   "ratio": 1.331,
   "atk_prev": 60.4032,
   "atk_cur": 80.4264
  }
 ]
}
```

## 08 声骸套装

耗时 0.0s，状态 ok

```json
{
 "sets": 37,
 "by_piece": {
  "2": {
   "count": 31,
   "kinds": {
    "伤害加成": 21,
    "充能": 4,
    "治疗": 3,
    "攻击": 2,
    "生命": 1
   },
   "with_param": 31,
   "long_desc": 0
  },
  "5": {
   "count": 31,
   "kinds": {
    "伤害加成": 25,
    "攻击": 5,
    "机制/其他": 1
   },
   "with_param": 31,
   "long_desc": 22
  }
 },
 "rows": [
  {
   "set": "凝夜白霜",
   "piece": "2",
   "desc": "冷凝伤害提升10%",
   "params": [
    "10%"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "凝夜白霜",
   "piece": "5",
   "desc": "使用普攻或重击时，冷凝伤害提升10%，该效果可叠加三层，持续15秒",
   "params": [
    "30%",
    "15"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "熔山裂谷",
   "piece": "2",
   "desc": "热熔伤害提升10%",
   "params": [
    "10%"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "熔山裂谷",
   "piece": "5",
   "desc": "使用共鸣技能时，热熔伤害提升30%，持续15秒",
   "params": [
    "30%"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "彻空冥雷",
   "piece": "2",
   "desc": "导电伤害提升10%",
   "params": [
    "10%"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "彻空冥雷",
   "piece": "5",
   "desc": "使用重击或共鸣技能时，各获得一层导电伤害提升15%的效果，该效果可叠加两层，每层各持续15秒",
   "params": [
    "15%",
    "15"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "啸谷长风",
   "piece": "2",
   "desc": "气动伤害提升10%",
   "params": [
    "10%"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "啸谷长风",
   "piece": "5",
   "desc": "使用变奏技能登场时，气动伤害提升30%，持续15秒",
   "params": [
    "30%"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "浮星祛暗",
   "piece": "2",
   "desc": "衍射伤害提升10%",
   "params": [
    "10%"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "浮星祛暗",
   "piece": "5",
   "desc": "使用变奏技能登场时，衍射伤害提升30%，持续15秒",
   "params": [
    "30%"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "沉日劫明",
   "piece": "2",
   "desc": "湮灭伤害提升10%",
   "params": [
    "10%"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "沉日劫明",
   "piece": "5",
   "desc": "使用普攻或重击时，湮灭伤害提升7.5%，该效果可叠加四层，持续15秒",
   "params": [
    "6%",
    "5",
    "15"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "隐世回光",
   "piece": "2",
   "desc": "治疗效果提升10%",
   "params": [
    "10%"
   ],
   "kind": "治疗"
  },
  {
   "set": "隐世回光",
   "piece": "5",
   "desc": "自身为友方提供治疗时，全队共鸣者攻击提升15%，持续30秒",
   "params": [
    "15%",
    "30"
   ],
   "kind": "攻击"
  },
  {
   "set": "轻云出月",
   "piece": "2",
   "desc": "共鸣效率提升{0}",
   "params": [
    "10%"
   ],
   "kind": "充能"
  },
  {
   "set": "轻云出月",
   "piece": "5",
   "desc": "使用延奏技能后，下一个登场的共鸣者攻击提升22.5%，持续15秒",
   "params": [
    "22.5%",
    "15"
   ],
   "kind": "攻击"
  },
  {
   "set": "不绝余音",
   "piece": "2",
   "desc": "攻击提升10%",
   "params": [
    "10%"
   ],
   "kind": "攻击"
  },
  {
   "set": "不绝余音",
   "piece": "5",
   "desc": "在场时，自身攻击每1.5秒提升5%，该效果最多叠加四层。延奏技能伤害提升60%",
   "params": [
    "1.5",
    "5%",
    "20%",
    "60%"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "凌冽决断之心",
   "piece": "2",
   "desc": "共鸣技能伤害提升{0}",
   "params": [
    "12%"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "凌冽决断之心",
   "piece": "5",
   "desc": "施放共鸣技能时，自身冷凝伤害提升{0}，持续{1}秒；施放共鸣解放时，自身共鸣技能伤害提升{2}，持续{3}秒，可叠加{4}层。",
   "params": [
    "22.5%",
    "15",
    "18%",
    "5",
    "2"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "此间永驻之光",
   "piece": "2",
   "desc": "衍射伤害提升{0}",
   "params": [
    "10%"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "此间永驻之光",
   "piece": "5",
   "desc": "角色为敌人添加【光噪效应】时，自身暴击提升{0}，持续{1}秒；攻击存在{2}层【光噪效应】的敌人时，自身衍射伤害加成提升{3}，持续{4}秒。",
   "params": [
    "20%",
    "15",
    "10",
    "15%",
    "15"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "幽夜隐匿之帷",
   "piece": "2",
   "desc": "湮灭属性伤害提升{0}",
   "params": [
    "10%"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "幽夜隐匿之帷",
   "piece": "5",
   "desc": "角色触发延奏技能离场时，额外对周围敌人造成{0}的湮灭伤害，该伤害为延奏技能伤害，并使下一个登场角色湮灭属性伤害加成提升{1}，持续{2}秒。",
   "params": [
    "480%",
    "15%",
    "15"
   ],
   "kind": "伤害加成"
  },
  {
   "set": "高天共奏之曲",
   "piece": "2",
   "desc": "共鸣效率提升{0}",
   "params": [
    "10%"
   ],
   "kind": "充能"
  },
  {
   "set": "高天共奏之曲",
   "piece": "5",
   "desc": "当前角色协同攻击造成的伤害提升{0}；协同攻击命中敌人且暴击时，队伍中登场角色攻击力提升{1}，持续{2}秒。",
   "params": [
    "80%",
    "20%",
    "4"

```

## 10 技能倍率

耗时 0.2s，状态 ok

```json
{
 "characters": 60,
 "median_total": 44.944,
 "min": 7.324,
 "max": 118.63,
 "share_by_type": {
  "回路": 29.6,
  "普攻": 28.0,
  "解放": 24.1,
  "技能": 11.3,
  "变奏": 6.0,
  "其他": 0.7,
  "延奏": 0.3
 },
 "top": [
  {
   "name": "心",
   "total": 118.63,
   "by_type": {
    "普攻": 30.838,
    "技能": 3.898,
    "解放": 20.24,
    "变奏": 21.637,
    "回路": 42.017
   },
   "count": 37
  },
  {
   "name": "琳奈",
   "total": 106.261,
   "by_type": {
    "普攻": 32.241,
    "技能": 5.112,
    "解放": 10.759,
    "变奏": 2.248,
    "回路": 37.093,
    "其他": 18.808
   },
   "count": 30
  },
  {
   "name": "露西",
   "total": 83.557,
   "by_type": {
    "普攻": 24.275,
    "技能": 6.673,
    "解放": 37.548,
    "变奏": 1.383,
    "回路": 13.678
   },
   "count": 28
  },
  {
   "name": "尤诺",
   "total": 78.607,
   "by_type": {
    "普攻": 17.876,
    "技能": 15.536,
    "解放": 10.935,
    "变奏": 1.591,
    "回路": 32.669
   },
   "count": 30
  },
  {
   "name": "锁暝",
   "total": 74.295,
   "by_type": {
    "普攻": 22.759,
    "技能": 2.641,
    "解放": 7.555,
    "变奏": 17.908,
    "回路": 23.431
   },
   "count": 24
  },
  {
   "name": "丽贝卡",
   "total": 70.275,
   "by_type": {
    "普攻": 22.642,
    "技能": 4.732,
    "解放": 7.82,
    "变奏": 4.732,
    "回路": 30.349
   },
   "count": 28
  },
  {
   "name": "爱弥斯",
   "total": 69.336,
   "by_type": {
    "普攻": 10.148,
    "技能": 14.06,
    "解放": 27.933,
    "变奏": 2.978,
    "回路": 14.216
   },
   "count": 26
  },
  {
   "name": "漂泊者·导电",
   "total": 68.069,
   "by_type": {
    "普攻": 11.316,
    "技能": 3.407,
    "解放": 11.929,
    "变奏": 1.67,
    "回路": 39.747
   },
   "count": 33
  }
 ],
 "bottom": [
  {
   "name": "渊武",
   "total": 21.51,
   "by_type": {
    "普攻": 10.16,
    "技能": 2.0,
    "解放": 3.499,
    "变奏": 0.636,
    "回路": 5.215
   },
   "count": 23
  },
  {
   "name": "穗穗",
   "total": 20.904,
   "by_type": {
    "普攻": 7.25,
    "技能": 3.184,
    "解放": 0.057,
    "变奏": 0.286,
    "回路": 10.127
   },
   "count": 19
  },
  {
   "name": "卜灵",
   "total": 20.339,
   "by_type": {
    "普攻": 7.919,
    "技能": 1.168,
    "解放": 3.579,
    "变奏": 2.106,
    "回路": 5.567
   },
   "count": 17
  },
  {
   "name": "莫特斐",
   "total": 18.49,
   "by_type": {
    "普攻": 9.544,
    "技能": 2.088,
    "解放": 1.909,
    "变奏": 1.69,
    "回路": 3.26
   },
   "count": 14
  },
  {
   "name": "秋水",
   "total": 17.165,
   "by_type": {
    "普攻": 8.508,
    "技能": 1.597,
    "解放": 4.076,
    "变奏": 1.988,
    "回路": 0.997
   },
   "count": 16
  },
  {
   "name": "维里奈",
   "total": 16.919,
   "by_type": {
    "普攻": 7.552,
    "技能": 1.79,
    "解放": 2.433,
    "变奏": 0.994,
    "回路": 4.151
   },
   "count": 22
  },
  {
   "name": "守岸人",
   "total": 10.506,
   "by_type": {
    "普攻": 5.169,
    "技能": 0.373,
    "解放": 0.024,
    "变奏": 2.879,
    "回路": 2.061
   },
   "count": 17
  },
  {
   "name": "白芷",
   "total": 7.324,
   "by_type": {
    "普攻": 6.207,
    "技能": 0.217,
    "解放": 0.094,
    "变奏": 0.803,
    "回路": 0.003
   },
   "count": 15
  }
 ]
}
```

## 12/13 充能预算

耗时 0.2s，状态 ok

```json
{
 "characters": 58,
 "ratio": 0.5,
 "by_cost": [
  {
   "cost": 100.0,
   "count": 4,
   "median_concerto": 82.5,
   "ult_energy": 41.2,
   "coverage": 41.2
  },
  {
   "cost": 125.0,
   "count": 41,
   "median_concerto": 60.0,
   "ult_energy": 30.0,
   "coverage": 24.0
  },
  {
   "cost": 150.0,
   "count": 7,
   "median_concerto": 65.0,
   "ult_energy": 32.5,
   "coverage": 21.7
  },
  {
   "cost": 175.0,
   "count": 6,
   "median_concerto": 56.0,
   "ult_energy": 28.0,
   "coverage": 16.0
  }
 ],
 "rows": [
  {
   "name": "散华",
   "cost": 100.0,
   "concerto": 90.0
  },
  {
   "name": "白芷",
   "cost": 175.0,
   "concerto": 52.0
  },
  {
   "name": "凌阳",
   "cost": 125.0,
   "concerto": 65.0
  },
  {
   "name": "折枝",
   "cost": 125.0,
   "concerto": 80.0
  },
  {
   "name": "釉瑚",
   "cost": 100.0,
   "concerto": 100.0
  },
  {
   "name": "珂莱塔",
   "cost": 125.0,
   "concerto": 87.0
  },
  {
   "name": "绯雪",
   "cost": 125.0,
   "concerto": 60.0
  },
  {
   "name": "穗穗",
   "cost": 175.0,
   "concerto": 30.0
  },
  {
   "name": "炽霞",
   "cost": 150.0,
   "concerto": 50.5
  },
  {
   "name": "安可",
   "cost": 125.0,
   "concerto": 70.0
  },
  {
   "name": "莫特斐",
   "cost": 125.0,
   "concerto": 66.0
  },
  {
   "name": "长离",
   "cost": 125.0,
   "concerto": 67.0
  },
  {
   "name": "布兰特",
   "cost": 175.0,
   "concerto": 60.0
  },
  {
   "name": "露帕",
   "cost": 125.0,
   "concerto": 40.0
  },
  {
   "name": "嘉贝莉娜",
   "cost": 125.0,
   "concerto": 40.0
  },
  {
   "name": "莫宁",
   "cost": 175.0,
   "concerto": 40.0
  },
  {
   "name": "爱弥斯",
   "cost": 125.0,
   "concerto": 60.0
  },
  {
   "name": "达妮娅",
   "cost": 125.0,
   "concerto": 60.0
  },
  {
   "name": "景燃",
   "cost": 125.0,
   "concerto": 30.0
  },
  {
   "name": "卡卡罗",
   "cost": 125.0,
   "concerto": 50.0
  },
  {
   "name": "吟霖",
   "cost": 125.0,
   "concerto": 60.0
  },
  {
   "name": "渊武",
   "cost": 125.0,
   "concerto": 58.0
  },
  {
   "name": "今汐",
   "cost": 150.0,
   "concerto": 62.0
  },
  {
   "name": "相里要",
   "cost": 125.0,
   "concerto": 69.0
  },
  {
   "name": "卜灵",
   "cost": 150.0,
   "concerto": 113.0
  },
  {
   "name": "丽贝卡",
   "cost": 125.0,
   "concerto": 40.0
  },
  {
   "name": "漂泊者·导电",
   "cost": 125.0,
   "concerto": 30.0
  },
  {
   "name": "漂泊者·导电",
   "cost": 125.0,
   "concerto": 30.0
  },
  {
   "name": "心",
   "cost": 125.0,
   "concerto": 80.0
  },
  {
   "name": "锁暝",
   "cost": 125.0,
   "concerto": 100.0
  },
  {
   "name": "秧秧",
   "cost": 100.0,
   "concerto": 75.0
  },
  {
   "name": "秋水",
   "cost": 150.0,
   "concerto": 45.0
  },
  {
   "name": "忌炎",
   "cost": 125.0,
   "concerto": 46.0
  },
  {
   "name": "鉴心",
   "cost": 150.0,
   "concerto": 129.0
  },
  {
   "name": "漂泊者·气动",
   "cost": 150.0,
   "concerto": 65.0
  },
  {
   "name": "夏空",
   "cost": 125.0,
   "concerto": 80.0
  },
  {
   "name": "漂泊者·气动",
   "cost": 150.0,
   "concerto": 65.0
  },
  {
   "name": "尤诺",
   "cost": 125.0,
   "concerto": 98.0
  },
  {
   "name": "仇远",
   "cost": 125.0,
   "concerto": 50.0
  },
  {
   "name": "西格莉卡",
   "cost": 125.0,
   "concerto": 40.0
  },
  {
   "name": "清宵",
   "cost": 125.0,
   "concerto": 55.0
  },
  {
   "name": "漂泊者·衍射",
   "cost": 125.0,
   "concerto": 68.0
  },
  {
   "name": "漂泊者·衍射",
   "cost": 125.0,
   "concerto": 68.0
  },
  {
   "name": "维里奈",
   "cost": 175.0,
   "concerto": 72.0
  },
  {
   "name": "灯灯",
   "cost": 125.0,
   "concerto": 54.0
  },
  {
   "name": "守岸人",
   "cost": 175.0,
   "concerto": 82.0
  },
  {
   "name": "菲比",
   "cost": 125.0,
   "concerto": 80.0
  },
  {
   "name": "赞妮",
   "cost": 125.0,
   "concerto": 70.0
  },
  {
   "name": "千咲",
   "cost": 125.0,
   "concerto": 75.0
  },
  {
   "name": "琳奈",
   "cost": 125.0,
   "concerto": 30.0
  },
  {
   "name": "陆·赫斯",
   "cost": 125.0,
   "concerto": 40.0
  },
  {
   "name": "露西",
   "cost": 125.0,
   "concerto": 62.0
  },
  {
   "name": "丹瑾",
   "cost": 100.0,
   "concerto": 30.0
  },
  {
   "name": "椿",
   "cost": 125.0,
   "concer
```
