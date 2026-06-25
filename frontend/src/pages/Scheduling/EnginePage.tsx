// AI排课引擎执行页面
import { useState } from 'react';
import {
  Card, Button, Slider, Select, Space, Typography, Progress, Alert,
  Descriptions, Tag, Spin, Row, Col, Statistic, Divider
} from 'antd';
import {
  ThunderboltOutlined, CheckCircleOutlined, ExperimentOutlined
} from '@ant-design/icons';
import { scheduleApi } from '../../api/client';
import type { ScheduleResult } from '../../types';

const { Title, Text, Paragraph } = Typography;

export default function EnginePage() {
  const [config, setConfig] = useState({
    algorithm: 'genetic',
    population_size: 100,
    max_generations: 500,
  });
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<ScheduleResult | null>(null);
  const [explanation, setExplanation] = useState('');

  const handleGenerate = async () => {
    setRunning(true);
    setProgress(10);
    setResult(null);
    setExplanation('');

    // 模拟进度
    const timer = setInterval(() => {
      setProgress((p) => Math.min(p + Math.random() * 15, 90));
    }, 500);

    try {
      const res: any = await scheduleApi.generate(config);
      setResult(res);
      setExplanation(res.explanation || '');
      setProgress(100);
    } catch (e: any) {
      setProgress(0);
    } finally {
      clearInterval(timer);
      setRunning(false);
    }
  };

  return (
    <div style={{ maxWidth: 1100 }}>
      <Title level={4} style={{ color: '#0d253d', marginBottom: 20 }}>
        <ThunderboltOutlined style={{ color: '#533afd', marginRight: 8 }} />
        AI智能排课
      </Title>

      <Row gutter={[16, 16]}>
        {/* 左侧：配置面板 */}
        <Col xs={24} lg={10}>
          <Card title="排课参数配置" bordered style={{ borderColor: '#e3e8ee' }}>
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              <div>
                <Text strong style={{ color: '#0d253d' }}>排课算法</Text>
                <Select
                  value={config.algorithm}
                  onChange={(v) => setConfig({ ...config, algorithm: v })}
                  style={{ width: '100%', marginTop: 6 }}
                  options={[
                    { label: '遗传算法 (推荐)', value: 'genetic' },
                    { label: '贪心算法', value: 'greedy' },
                    { label: '混合算法', value: 'hybrid' },
                  ]}
                />
              </div>

              <div>
                <Text strong style={{ color: '#0d253d' }}>
                  种群大小: {config.population_size}
                </Text>
                <Slider
                  value={config.population_size}
                  onChange={(v) => setConfig({ ...config, population_size: v })}
                  min={50} max={500} step={10}
                />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  较大的种群可获得更优解，但计算时间更长
                </Text>
              </div>

              <div>
                <Text strong style={{ color: '#0d253d' }}>
                  最大迭代代数: {config.max_generations}
                </Text>
                <Slider
                  value={config.max_generations}
                  onChange={(v) => setConfig({ ...config, max_generations: v })}
                  min={100} max={2000} step={50}
                />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  算法会在收敛后自动停止（早停机制）
                </Text>
              </div>

              <Divider style={{ margin: '8px 0' }} />

              <Button
                type="primary"
                size="large"
                icon={<ThunderboltOutlined />}
                onClick={handleGenerate}
                loading={running}
                block
                style={{ height: 44, fontWeight: 600 }}
              >
                {running ? '正在排课中...' : '开始AI排课'}
              </Button>

              {running && (
                <Progress percent={Math.round(progress)} status="active" strokeColor="#533afd" />
              )}
            </Space>
          </Card>
        </Col>

        {/* 右侧：结果面板 */}
        <Col xs={24} lg={14}>
          <Spin spinning={running} tip="AI正在优化排课方案...">
            {result ? (
              <>
                {/* 统计卡片 */}
                <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
                  <Col span={8}>
                    <Card size="small" bordered style={{ textAlign: 'center', borderColor: '#e3e8ee' }}>
                      <Statistic
                        title="质量评分"
                        value={result.quality_score}
                        suffix="分"
                        valueStyle={{ color: result.quality_score >= 85 ? '#10b981' : '#f59e0b', fontSize: 24 }}
                        prefix={<CheckCircleOutlined />}
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card size="small" bordered style={{ textAlign: 'center', borderColor: '#e3e8ee' }}>
                      <Statistic
                        title="硬性冲突"
                        value={result.hard_conflicts}
                        valueStyle={{ color: result.hard_conflicts === 0 ? '#10b981' : '#ea2261', fontSize: 24 }}
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card size="small" bordered style={{ textAlign: 'center', borderColor: '#e3e8ee' }}>
                      <Statistic
                        title="排课条目"
                        value={result.total_entries}
                        suffix="条"
                        valueStyle={{ color: '#533afd', fontSize: 24 }}
                      />
                    </Card>
                  </Col>
                </Row>

                {/* 结果详情 */}
                <Card bordered size="small" style={{ borderColor: '#e3e8ee', marginBottom: 12 }}>
                  <Descriptions size="small" column={2}>
                    <Descriptions.Item label="方案版本">{result.version}</Descriptions.Item>
                    <Descriptions.Item label="软性冲突">{result.soft_conflicts}</Descriptions.Item>
                    <Descriptions.Item label="排课算法">
                      <Tag color="purple">{config.algorithm}</Tag>
                    </Descriptions.Item>
                  </Descriptions>
                </Card>

                {/* 总体评估 */}
                {result.hard_conflicts === 0 ? (
                  <Alert type="success" message="排课成功" description="所有硬性约束均已满足，方案可用于实际排课" showIcon style={{ marginBottom: 12 }} />
                ) : (
                  <Alert type="error" message="存在硬性冲突" description={`发现${result.hard_conflicts}个硬性冲突，建议检查约束配置后重新排课`} showIcon style={{ marginBottom: 12 }} />
                )}

                {/* AI优化说明 */}
                {explanation && (
                  <Card
                    title={<Space><ExperimentOutlined style={{ color: '#533afd' }} />AI优化说明</Space>}
                    bordered size="small"
                    style={{ borderColor: '#e3e8ee' }}
                  >
                    <Paragraph style={{ whiteSpace: 'pre-wrap', fontSize: 13, color: '#273951', lineHeight: 1.8 }}>
                      {explanation}
                    </Paragraph>
                  </Card>
                )}
              </>
            ) : (
              <Card bordered style={{ borderColor: '#e3e8ee', textAlign: 'center', padding: 60 }}>
                <ThunderboltOutlined style={{ fontSize: 48, color: '#d0d6e0', marginBottom: 16 }} />
                <Paragraph type="secondary">
                  配置参数后点击"开始AI排课"，系统将自动生成最优排课方案
                </Paragraph>
              </Card>
            )}
          </Spin>
        </Col>
      </Row>
    </div>
  );
}
