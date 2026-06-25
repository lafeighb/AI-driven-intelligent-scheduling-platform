// 冲突检测与化解页面
import { useState, useEffect } from 'react';
import { Card, Table, Tag, Space, Typography, Button, Alert, Spin, Statistic, Row, Col, Select } from 'antd';
import { AlertOutlined, CheckCircleOutlined, WarningOutlined, SearchOutlined } from '@ant-design/icons';
import { scheduleApi } from '../../api/client';
import type { ConflictInfo } from '../../types';

const { Title, Text } = Typography;

export default function ConflictsPage() {
  const [conflicts, setConflicts] = useState<ConflictInfo[]>([]);
  const [versions, setVersions] = useState<{ version: string }[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [confRes, verRes] = await Promise.all([
        scheduleApi.getConflicts(selectedVersion),
        scheduleApi.getVersions(),
      ]);
      setConflicts((confRes as unknown as any[]) || []);
      setVersions((verRes as unknown as any[]) || []);
    } catch { /* 使用空数据 */ }
    finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, [selectedVersion]);

  const hardConflicts = conflicts.filter(c => c.conflict_type === 'hard');
  const softConflicts = conflicts.filter(c => c.conflict_type === 'soft');

  return (
    <div style={{ maxWidth: 1100 }}>
      <Title level={4} style={{ color: '#0d253d', marginBottom: 20 }}>
        <AlertOutlined style={{ color: '#ea2261', marginRight: 8 }} />
        冲突检测与化解
      </Title>

      {/* 统计概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
        <Col span={8}>
          <Card size="small" bordered style={{ textAlign: 'center', borderColor: '#e3e8ee' }}>
            <Statistic
              title="硬性冲突"
              value={hardConflicts.length}
              valueStyle={{ color: hardConflicts.length === 0 ? '#10b981' : '#ea2261' }}
              prefix={hardConflicts.length === 0 ? <CheckCircleOutlined /> : <WarningOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" bordered style={{ textAlign: 'center', borderColor: '#e3e8ee' }}>
            <Statistic
              title="软性冲突"
              value={softConflicts.length}
              valueStyle={{ color: softConflicts.length <= 5 ? '#10b981' : '#f59e0b' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" bordered style={{ textAlign: 'center', borderColor: '#e3e8ee' }}>
            <Statistic
              title="冲突总计"
              value={conflicts.length}
              valueStyle={{ color: '#533afd' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选和操作 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Space>
          <Select
            allowClear
            placeholder="选择排课版本"
            value={selectedVersion}
            onChange={setSelectedVersion}
            style={{ width: 280 }}
            options={versions.map(v => ({ label: v.version, value: v.version }))}
          />
        </Space>
        <Space>
          <Button icon={<SearchOutlined />} onClick={loadData} loading={loading}>刷新检测</Button>
        </Space>
      </div>

      {/* 冲突列表 */}
      <Card bordered style={{ borderColor: '#e3e8ee' }}>
        <Spin spinning={loading}>
          {conflicts.length === 0 ? (
            <Alert type="success" message="未检测到冲突" description="当前排课方案满足所有约束条件，课表状态良好。" showIcon />
          ) : (
            <Table
              dataSource={conflicts}
              rowKey={(_, i) => String(i)}
              pagination={{ pageSize: 20 }}
              columns={[
                {
                  title: '类型', dataIndex: 'conflict_type', width: 80,
                  render: (v: string) => (
                    <Tag color={v === 'hard' ? 'red' : 'blue'}>{v === 'hard' ? '硬冲突' : '软冲突'}</Tag>
                  ),
                },
                {
                  title: '分类', dataIndex: 'category', width: 100,
                  render: (v: string) => {
                    const map: Record<string, { color: string; label: string }> = {
                      teacher: { color: 'blue', label: '教师' },
                      classroom: { color: 'green', label: '教室' },
                      class: { color: 'purple', label: '班级' },
                      capacity: { color: 'orange', label: '容量' },
                      time: { color: 'cyan', label: '时间' },
                      course: { color: 'magenta', label: '课程' },
                    };
                    const info = map[v] || { color: 'default', label: v };
                    return <Tag color={info.color}>{info.label}</Tag>;
                  },
                },
                { title: '冲突描述', dataIndex: 'description', ellipsis: true },
                {
                  title: '严重程度', dataIndex: 'severity', width: 90,
                  render: (v: number) => {
                    const color = v >= 8 ? '#ea2261' : v >= 5 ? '#f59e0b' : '#10b981';
                    return <span style={{ color, fontWeight: 600 }}>{v}/10</span>;
                  },
                },
                {
                  title: '化解建议', dataIndex: 'resolution_suggestion', width: 250, ellipsis: true,
                  render: (v: string) => v ? <Text type="secondary" style={{ fontSize: 12 }}>{v}</Text> : '-',
                },
              ]}
            />
          )}
        </Spin>
      </Card>
    </div>
  );
}
