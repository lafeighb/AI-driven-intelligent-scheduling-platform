// 约束规则配置页面
import { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Tag, Typography, Switch, message } from 'antd';
import { ThunderboltOutlined, PlusOutlined } from '@ant-design/icons';
import { constraintApi } from '../../api/client';
import type { ConstraintRule, ConstraintLearningResult } from '../../types';

const { Title, Paragraph } = Typography;

const categoryColors: Record<string, string> = {
  teacher: 'blue', classroom: 'green', class: 'purple', course: 'orange', time: 'cyan',
};

export default function ConstraintsPage() {
  const [constraints, setConstraints] = useState<ConstraintRule[]>([]);
  const [learningResults, setLearningResults] = useState<ConstraintLearningResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [learning, setLearning] = useState(false);

  const loadConstraints = async () => {
    setLoading(true);
    try {
      const res = await constraintApi.list({ limit: 100 });
      setConstraints((res as unknown as any[]) || []);
    } catch { message.error('加载约束规则失败'); }
    finally { setLoading(false); }
  };

  const loadDefaults = async () => {
    try {
      const res: any = await constraintApi.getDefaults();
      const defaults = res.defaults || [];
      for (const d of defaults) {
        try { await constraintApi.create(d); } catch { /* 忽略已存在的 */ }
      }
      message.success('默认约束规则已加载');
      loadConstraints();
    } catch (e: any) { message.error(`加载失败: ${e.message}`); }
  };

  const handleToggle = async (id: number, active: boolean) => {
    try {
      await constraintApi.update(id, { is_active: active });
      loadConstraints();
      message.success(active ? '规则已启用' : '规则已禁用');
    } catch (e: any) { message.error(`操作失败: ${e.message}`); }
  };

  const handleLearn = async () => {
    setLearning(true);
    try {
      const res: any = await constraintApi.learn();
      setLearningResults(res || []);
      message.success('约束自学习分析完成');
    } catch (e: any) { message.error(`学习失败: ${e.message}`); }
    finally { setLearning(false); }
  };

  useEffect(() => { loadConstraints(); }, []);

  return (
    <div style={{ maxWidth: 1100 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, color: '#0d253d' }}>约束规则配置</Title>
        <Space>
          <Button icon={<PlusOutlined />} onClick={loadDefaults}>加载默认规则</Button>
          <Button type="primary" icon={<ThunderboltOutlined />} onClick={handleLearn} loading={learning}>
            AI约束学习
          </Button>
        </Space>
      </div>

      <Card bordered style={{ borderColor: '#e3e8ee', marginBottom: 20 }}>
        <Paragraph type="secondary" style={{ marginBottom: 16, fontSize: 13 }}>
          硬约束（Hard）：必须满足的排课条件，违反将导致排课方案无效。
          软约束（Soft）：尽量满足的条件，系统会自动权衡各约束的优先级和权重。
        </Paragraph>

        <Table
          dataSource={constraints}
          rowKey="id"
          loading={loading}
          pagination={false}
          columns={[
            { title: '规则名称', dataIndex: 'name', width: 180 },
            {
              title: '类型', dataIndex: 'rule_type', width: 80,
              render: (v: string) => <Tag color={v === 'hard' ? 'red' : 'blue'}>{v === 'hard' ? '硬约束' : '软约束'}</Tag>,
            },
            {
              title: '分类', dataIndex: 'category', width: 100,
              render: (v: string) => <Tag color={categoryColors[v]}>{v}</Tag>,
            },
            { title: '描述', dataIndex: 'description', ellipsis: true },
            { title: '权重', dataIndex: 'weight', width: 70 },
            { title: '惩罚分', dataIndex: 'penalty_score', width: 70 },
            { title: '优先级', dataIndex: 'priority', width: 70 },
            {
              title: '状态', dataIndex: 'is_active', width: 80,
              render: (v: boolean, record: ConstraintRule) => (
                <Switch checked={v} onChange={(checked) => handleToggle(record.id, checked)} size="small" />
              ),
            },
            {
              title: '来源', dataIndex: 'learned_from_history', width: 80,
              render: (v: boolean) => v ? <Tag color="purple">AI学习</Tag> : <Tag>手动</Tag>,
            },
          ]}
        />
      </Card>

      {/* AI学习结果 */}
      {learningResults.length > 0 && (
        <Card
          title={<Space><ThunderboltOutlined style={{ color: '#533afd' }} />AI约束学习分析结果</Space>}
          bordered
          style={{ borderColor: '#e3e8ee' }}
        >
          <Table
            dataSource={learningResults}
            rowKey="rule_id"
            pagination={false}
            columns={[
              { title: '规则', dataIndex: 'rule_name', width: 160 },
              {
                title: '满足率', dataIndex: 'satisfaction_rate', width: 100,
                render: (v: number) => `${(v * 100).toFixed(1)}%`,
              },
              { title: '冲突次数', dataIndex: 'conflict_count', width: 80 },
              { title: '严重程度', dataIndex: 'conflict_severity_mean', width: 80 },
              {
                title: '质量影响', dataIndex: 'impact_on_quality', width: 90,
                render: (v: number) => <span style={{ color: v < -0.3 ? '#ea2261' : '#10b981' }}>{v.toFixed(3)}</span>,
              },
              { title: 'AI建议', dataIndex: 'recommendation', ellipsis: true },
            ]}
          />
        </Card>
      )}
    </div>
  );
}
