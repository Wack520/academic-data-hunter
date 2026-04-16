# 开发者指南

这份指南给需要集成 workflow 的开发者使用。

## 你可以怎样接入

- 直接调用 CLI 脚本
- 通过 API 进程调用
- 通过本地 MCP server 暴露工具

## 推荐接入思路

1. 先把任务定义标准化
2. 把数据采集和抽取结果落盘
3. 始终产出来源台账
4. 在交付前跑校验和 Benchmark Eval

## 当前可直接复用的能力

- run round
- validate round
- evidence pack export
- benchmark eval
