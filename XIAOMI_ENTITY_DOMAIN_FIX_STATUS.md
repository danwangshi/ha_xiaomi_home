# Xiaomi Home 实体 ID 修复记录

> 最后更新：2026-09-06

## 1. 项目与分支

```text
本地路径：C:\Users\evil\Desktop\agent_default_workdir\xiaomi_home
fork：https://github.com/danwangshi/ha_xiaomi_home.git
上游：https://github.com/XiaoMi/ha_xiaomi_home.git
分支：fix/entity-domain-mismatch
远程 HEAD：a9a0d01273eed10ac70e7f556241478a2f903de2
```

提交身份：

```text
danwangshi <scq1996@foxmail.com>
```

## 2. 问题

Xiaomi Home v0.4.7 生成部分实体时使用了错误的实体域名，例如：

```text
xiaomi_home.<entity_id>
```

Home Assistant 报告：

```text
sets an entity ID with wrong domain
```

同时，部分 Xiaomi 内部平台名称和服务描述不能直接作为 Home Assistant entity ID。

## 3. 修复内容

修改文件：

```text
custom_components/xiaomi_home/miot/miot_device.py
```

测试文件：

```text
test/test_entity_domain.py
```

修复包括：

1. 实体 ID 使用实际 Home Assistant 平台域名；
2. 保留旧的 `xiaomi_home.*` `unique_id`，兼容已有实体注册表；
3. 内部平台名称映射：

   ```text
   air-conditioner -> climate
   bath-heater -> climate
   dehumidifier -> humidifier
   electric-blanket -> climate
   heater -> climate
   thermostat -> climate
   wifi-speaker -> media_player
   television -> media_player
   ```

4. 服务描述使用 slug 化处理，例如：

   ```text
   Indicator Light -> indicator_light
   ```

## 4. 提交记录

由于 CLA Assistant 要求 commit email 与有效 GitHub 账号匹配，分支提交已经重写为当前账号身份：

```text
a07a1b3 fix: use platform domains for entity IDs
51603ea fix: preserve entity unique IDs during migration
a9a0d01 fix: normalize generated entity IDs
```

当前远程 HEAD：

```text
a9a0d01273eed10ac70e7f556241478a2f903de2
```

## 5. 测试

离线回归测试：

```text
4 passed
```

覆盖：

```text
service entity
property entity
event entity
action entity
平台域名映射
服务名称 slug 化
旧 unique_id 兼容
```

完整云端测试没有运行，因为会触发 Xiaomi OAuth 授权页面。

## 6. NAS 部署

当前部署文件：

```text
/config/custom_components/xiaomi_home/miot/miot_device.py
```

HA 使用飞牛 Compose 项目：

```text
项目：home-assistant
Compose 文件：/vol1/@appcenter/Home-Assistant/docker/docker-compose.yaml
容器：homeassistant
镜像：homeassistant/home-assistant:2026.8.2
配置挂载：/vol1/@appshare/Home-Assistant/config:/config
```

已验证：

```text
wrong domain WARNING：消失
invalid entity ID WARNING：消失
Xiaomi 实体：可用
HA pip check：通过
```

示例实体：

```text
event.mxiang_cn_1146963387_moc001_sound_and_light_warning_e_18_1
select.mxiang_cn_1146963387_moc001_light_warning_mode_p_18_6
switch.mxiang_cn_1146963387_moc001_auto_sound_and_light_warning_p_2_15
switch.mxiang_cn_1146963387_moc001_manual_sound_and_light_warning_p_2_16
climate.cuco_cn_690766450_cp6
```

## 7. 备份与回滚

自定义集成原始备份：

```text
/vol1/@appshare/Home-Assistant/xiaomi-home-backup-20260906-110634
```

实体注册表清理前备份：

```text
/vol1/@appshare/Home-Assistant/xiaomi-home-entity-registry-backup-20260906-114154
```

第一次测试产生的 172 个重复实体记录已经清理。

## 9. Issue、复现与预期

### 9.1 问题现象

在 Home Assistant 日志中，部分由 Xiaomi Home 创建的实体使用了集成域名：

```text
xiaomi_home.<entity_id>
```

Home Assistant 因实体域名与实际实体平台不一致而记录：

```text
sets an entity ID with wrong domain
```

同时，内部 MIoT 平台名 `air-conditioner` 等不能直接用作 Home Assistant 域名；服务描述例如 `Indicator Light` 包含空格，也不能直接拼入合法实体 ID。

### 9.2 复现步骤

```text
1. 在 Home Assistant 中安装 Xiaomi Home 0.4.7；
2. 配置一个包含 service、property、event 或 action 的 Xiaomi 设备；
3. 等待 Xiaomi Home 根据 MIoT spec 创建实体；
4. 查看实体注册表和 Home Assistant 日志；
5. 观察实体 ID 以 xiaomi_home. 开头，或出现错误平台名/空格。
```

### 9.3 预期结果

```text
1. service 实体使用实际平台域名，例如 switch.*；
2. property 实体使用实际平台域名，例如 select.*；
3. event 实体使用 event.*；
4. action 实体使用 button.*；
5. climate、humidifier、media_player 等内部平台名映射为 HA 合法域名；
6. 服务描述经过 slugify 后不包含空格或非法字符；
7. 已有实体的 unique_id 不改变，不产生重复实体。
```

## 10. 修复实现细节

修改文件：

```text
custom_components/xiaomi_home/miot/miot_device.py
```

### 10.1 实体域名

各实体构造器将生成实体 ID 时的 domain 传为实际平台，而不是固定使用 `DOMAIN`（`xiaomi_home`）。示例：

```python
self.entity_id = device.gen_prop_entity_id(
    ha_domain=spec.platform,
    spec_name=spec.name,
    siid=spec.service.iid,
    piid=spec.iid,
)
```

实际调用分别覆盖 service、property、event 和 action 实体。

### 10.2 旧 unique_id 兼容

实体 ID 修正不能同时修改已有 `unique_id`。当前保留逻辑为：

```python
self._attr_unique_id = f'{DOMAIN}.{self.entity_id.split(".", 1)[1]}'
```

因此：

```text
新 entity_id：select.test
旧 unique_id：xiaomi_home.test
```

Home Assistant 可以将原实体注册表条目匹配到新的实际平台域名，而不会创建 `select.test_2` 等重复实体。

### 10.3 平台映射

```python
HA_DOMAIN_MAP = {
    'air-conditioner': 'climate',
    'bath-heater': 'climate',
    'dehumidifier': 'humidifier',
    'electric-blanket': 'climate',
    'heater': 'climate',
    'television': 'media_player',
    'thermostat': 'climate',
    'wifi-speaker': 'media_player',
}
```

未列出的合法平台名保持原值。这样 `air-conditioner.cuco_cn_690766450_cp6` 被修正为：

```text
climate.cuco_cn_690766450_cp6
```

### 10.4 名称 slug 化

服务描述进入实体 ID 前使用 `slugify_name()`：

```text
Indicator Light → indicator_light
```

解决实体 ID 中的空格和其他非法字符问题。

## 11. 回归测试

测试文件：

```text
test/test_entity_domain.py
```

离线回归结果：

```text
4 passed
```

覆盖范围：

```text
service entity：使用 service platform domain
property entity：使用 property platform domain
 event entity：使用 event domain
action entity：使用 button domain
platform mapping：内部平台名映射到 HA domain
slugification：服务名称转换为合法 ID
unique_id：保持 xiaomi_home.* 兼容值
```

测试使用最小化 `MIoTDevice`、service、property、event 和 action 对象，不访问 Xiaomi 云端，不会打开 OAuth 页面。

完整 `test/` 未运行：其中 `test_cloud.py` 等云端测试会打开 Xiaomi OAuth 授权页面，需要人工登录，不属于本次离线实体 ID 回归范围。

## 12. 提交、CLA 和上游状态

活动分支提交已经统一为有效 fork 账号：

```text
danwangshi <scq1996@foxmail.com>
```

当前活动提交：

```text
a07a1b3 fix: use platform domains for entity IDs
51603ea fix: preserve entity unique IDs during migration
a9a0d01 fix: normalize generated entity IDs
```

此前使用的 `evilscq@foxmail.com` 属于已暂停账号，CLA Assistant 无法匹配。活动分支 commit 已重写并强制更新到 fork；现有 Issue/PR 的创建者不能修改，不能通过新建重复 PR 解决。

上游 PR：

```text
https://github.com/danwangshi/ha_xiaomi_home/tree/fix/entity-domain-mismatch
```

当前等待：

```text
CLA Assistant 重新检查
GitHub Actions CI
上游维护者审核
```

## 13. NAS 部署、迁移和验证

实际部署文件：

```text
/vol1/@appshare/Home-Assistant/config/custom_components/xiaomi_home/miot/miot_device.py
```

部署时保留飞牛应用商店的 Compose 项目：

```text
项目：home-assistant
Compose 文件：/vol1/@appcenter/Home-Assistant/docker/docker-compose.yaml
容器：homeassistant
镜像：homeassistant/home-assistant:2026.8.2
配置挂载：/vol1/@appshare/Home-Assistant/config:/config
```

部署验证的实际实体包括：

```text
event.mxiang_cn_1146963387_moc001_sound_and_light_warning_e_18_1
select.mxiang_cn_1146963387_moc001_light_warning_mode_p_18_6
switch.mxiang_cn_1146963387_moc001_auto_sound_and_light_warning_p_2_15
switch.mxiang_cn_1146963387_moc001_manual_sound_and_light_warning_p_2_16
climate.cuco_cn_690766450_cp6
```

已确认：

```text
wrong domain WARNING：无
invalid entity ID WARNING：无
climate 实体可用
select、switch、event 实体可用
HA pip check：通过
```

## 14. 实体注册表迁移和回滚

第一次只修改 entity domain，同时改变了 unique ID，HA 将旧实体识别为新实体并生成 `_2` 重复条目。该问题已通过保留旧 `xiaomi_home.*` unique ID 修复。

在清理第一次测试产生的 172 个重复条目前已备份：

```text
/vol1/@appshare/Home-Assistant/xiaomi-home-entity-registry-backup-20260906-114154
```

自定义集成原始备份：

```text
/vol1/@appshare/Home-Assistant/xiaomi-home-backup-20260906-110634
```

回滚原则：

```text
1. 停止或按 Compose 项目管理 HA；
2. 保留当前 /config 备份；
3. 恢复 custom_components/xiaomi_home；
4. 如需恢复实体注册表，只使用对应时间点备份；
5. 重启 home-assistant Compose 项目并检查日志。
```

不要删除整个 `/config`，也不要用 `docker run` 重建替代应用商店的 Compose 项目。

## 15. 日志边界和后续事项

已解决的两类 WARNING：

```text
sets an entity ID with wrong domain
invalid entity ID（空格或错误平台名）
```

如果后续仍看到 deprecated、设备离线、云端重试或其他集成 WARNING，需要按日志具体来源区分，不能将其继续归因于本次 entity domain 修复。

后续操作：

```text
1. 等待现有 PR 的 CLA、CI 和维护者审核；
2. 继续保留 /config 和两个 Xiaomi 备份；
3. 后续升级时重新运行 test/test_entity_domain.py；
4. 不重复创建 PR；
5. 上游合并后再替换 NAS 上的临时 custom component。
```

## 16. 实体迁移后的重复记录修复

2026-09-06 在 NAS 实际页面发现，service 描述从带空格/大写改为 slug 后，前院摄像头的两个灯产生了重复实体：

```text
旧实体：light.mxiang_cn_1146963387_moc001_s_16_white_light
重复实体：light.mxiang_cn_1146963387_moc001_s_16_white_light_2
旧实体：light.mxiang_cn_1146963387_moc001_s_4_indicator_light
重复实体：light.mxiang_cn_1146963387_moc001_s_4_indicator_light_2
```

根因是 service 的旧 `unique_id` 使用了未 slug 化的描述：

```text
xiaomi_home...._s_16_White Light
```

而修复后的代码根据新 entity ID 生成了：

```text
xiaomi_home...._s_16_white_light
```

修复方式：

- 新增 `_gen_legacy_service_unique_id()`；
- service 实体继续保留迁移前的原始 description 作为 `unique_id`；
- entity ID 仍使用合法的 slug 化结果；
- 新增 service unique ID 迁移回归测试。

离线测试：

```text
5 passed
```

NAS 部署前备份：

```text
/vol1/@appshare/Home-Assistant/xiaomi-home-entity-fix-backup-20260906-1323/miot_device.py
```

部署并重启后实际状态：

```text
light.mxiang_cn_1146963387_moc001_s_16_white_light：off，可用
light.mxiang_cn_1146963387_moc001_s_4_indicator_light：on，可用
```

重复的 `_2` 实体已从运行状态中移除；其他 Xiaomi 实体未修改。

## 18. 空调伴侣 climate 实体修复

2026-09-06 实机页面发现：

```text
switch.cuco_cn_690766450_cp6_on_p_2_1：可用，但只有开关
climate.cuco_cn_690766450_cp6：不可用，但应提供模式、风扇和温度控制
```

HA 日志显示：

```text
Error while setting up xiaomi_home platform for climate:
'MIoTSpecInstance' object has no attribute 'iid'
```

根因是 service unique ID 迁移逻辑错误地应用到设备级 `MIoTSpecInstance`。修复后：

- `MIoTSpecService` 使用旧 service description 保持迁移兼容；
- `MIoTSpecInstance` 保持原有 device entity unique ID 逻辑；
- 新增设备级 climate 回归测试；
- Xiaomi Home 配置条目重新加载成功。

实际验证：

```text
climate.cuco_cn_690766450_cp6：off，可用
hvac_modes：cool / heat / auto / fan_only / dry / off
fan_modes：Auto / 低风 / 中风 / 高风 / off
temperature：27
supported_features：393
```

本次修复后的离线回归测试：

```text
6 passed
```

## 19. 当前状态

```text
本地修复：完成
离线回归：6 passed
NAS 部署：完成
前院摄像头白光灯：可用
前院摄像头指示灯：可用
后院摄像头指示灯：可用
空调伴侣 climate：可用
重复实体运行状态：已清理
```