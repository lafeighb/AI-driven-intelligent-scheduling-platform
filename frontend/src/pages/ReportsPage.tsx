// 分析报告页面 - 排课统计、质量分析、AI说明
import { useState, useEffect } from 'react';
import {
  Card, Row, Col, Statistic, Typography, Progress, Spin, Empty,
  Select, Space, Tag
} from 'antd';
import {
  BarChartOutlined, ExperimentOutlined, DashboardOutlined
} from '@ant-design/icons';
import { ioApi, scheduleApi } from '../api/client';
import type { AnalysisReport } from '../types';

const { Title, Text, Paragraph } = Typography;

export default function ReportsPage() {
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [versions, setVersions] = useState<{ version: string }[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  const loadReport = async () => {
    setLoading(true);
    try {
      const [reportRes, verRes] = await Promise.all([
        ioApi.getReport(selectedVersion),
        scheduleApi.getVersions(),
      ]);
      setReport(reportRes as any);
      setVersions((verRes as unknown as any[]) || []);
    } catch {
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadReport(); }, [selectedVersion]);

  return (
    <div style={{ maxWidth: 1100 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, color: '#0d253d' }}>
          <BarChartOutlined style={{ color: '#533afd', marginRight: 8 }} />
          智能分析报告
        </Title>
        <Select
          allowClear
          placeholder="选择排课版本"
          value={selectedVersion}
          onChange={setSelectedVersion}
          style={{ width: 280 }}
          options={versions.map(v => ({ label: v.version, value: v.version }))}
        />
      </div>

      <Spin spinning={loading}>
        {!report ? (
          <Card bordered style={{ borderColor: '#e3e8ee' }}>
            <Empty description="暂无分析数据，请先执行排课" />
          </Card>
        ) : (
          <>
            {/* 基础统计 */}
            <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
              {[
                { title: '排课条目', value: report.summary.total_entries, icon: <DashboardOutlined />, color: '#533afd' },
                { title: '涉及课程', value: report.summary.unique_courses, icon: <BarChartOutlined />, color: '#3b82f6' },
                { title: '涉及教师', value: report.summary.unique_teachers, icon: <DashboardOutlined />, color: '#10b981' },
                { title: '涉及班级', value: report.summary.unique_classes, icon: <DashboardOutlined />, color: '#f59e0b' },
              ].map(item => (
                <Col xs={12} sm={6} key={item.title}>
                  <Card size="small" bordered style={{ textAlign: 'center', borderColor: '#e3e8ee' }}>
                    <Statistic title={item.title} value={item.value} valueStyle={{ color: item.color, fontSize: 22 }} />
                  </Card>
                </Col>
              ))}
            </Row>

            {/* 质量评分与分布 */}
            <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
              <Col xs={24} md={8}>
                <Card bordered size="small" style={{ borderColor: '#e3e8ee' }}>
                  <Text strong style={{ color: '#0d253d' }}>方案质量评分</Text>
                  <div style={{ textAlign: 'center', margin: '16px 0' }}>
                    <Progress
                      type="dashboard"
                      percent={report.quality_score}
                      strokeColor={{
                        '0%': '#ea2261', '50%': '#f59e0b', '80%': '#533afd', '100%': '#10b981',
                      }}
                      format={p => `${p}分`}
                      size={160}
                    />
                  </div>
                </Card>
              </Col>
              <Col xs={24} md={8}>
                <Card bordered size="small" style={{ borderColor: '#e3e8ee' }}>
                  <Text strong style={{ color: '#0d253d' }}>每日课时均衡度</Text>
                  <div style={{ textAlign: 'center', margin: '16px 0' }}>
                    <Progress
                      type="dashboard"
                      percent={report.daily_balance_score}
                      strokeColor="#533afd"
                      format={p => `${p}分`}
                      size={160}
                    />
                  </div>
                </Card>
              </Col>
              <Col xs={24} md={8}>
                <Card bordered size="small" style={{ borderColor: '#e3e8ee' }}>
                  <Text strong style={{ color: '#0d253d' }}>教室平均利用率</Text>
                  <div style={{ textAlign: 'center', margin: '16px 0' }}>
                    <Progress
                      type="dashboard"
                      percent={report.avg_room_utilization}
                      strokeColor="#3b82f6"
                      format={p => `${p}%`}
                      size={160}
                    />
                  </div>
                </Card>
              </Col>
            </Row>

            {/* 每日分布 */}
            <Card bordered size="small" title="每日课时分布" style={{ borderColor: '#e3e8ee', marginBottom: 20 }}>
              <Row gutter={16}>
                {Object.entries(report.daily_distribution).map(([day, count]) => (
                  <Col key={day} span={Math.floor(24 / Object.keys(report.daily_distribution).length)} style={{ textAlign: 'center' }}>
                    <Progress
                      type="circle"
                      percent={Math.round((count / report.summary.total_entries) * 100)}
                      format={() => count}
                      size={80}
                      strokeColor="#533afd"
                    />
                    <div style={{ marginTop: 8 }}><Text strong>{day}</Text></div>
                  </Col>
                ))}
              </Row>
            </Card>

            {/* AI优化说明 */}
            {report.ai_explanation && (
              <Card
                bordered
                size="small"
                title={<Space><ExperimentOutlined style={{ color: '#533afd' }} />AI优化说明</Space>}
                style={{ borderColor: '#e3e8ee', marginBottom: 20 }}
              >
                <Paragraph style={{ whiteSpace: 'pre-wrap', fontSize: 13, color: '#273951', lineHeight: 1.8 }}>
                  {report.ai_explanation}
                </Paragraph>
              </Card>
            )}

            {/* 冲突摘要 */}
            <Card bordered size="small" title="冲突检测摘要" style={{ borderColor: '#e3e8ee' }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Text strong style={{ color: '#ea2261' }}>硬冲突分类:</Text>
                  {Object.keys(report.conflict_summary.hard_by_category).length === 0 ? (
                    <Tag color="green" style={{ marginLeft: 8 }}>无硬冲突</Tag>
                  ) : (
                    Object.entries(report.conflict_summary.hard_by_category).map(([cat, count]) => (
                      <Tag color="red" key={cat}>{cat}: {count}</Tag>
                    ))
                  )}
                </Col>
                <Col span={12}>
                  <Text strong style={{ color: '#f59e0b' }}>软冲突分类:</Text>
                  {Object.keys(report.conflict_summary.soft_by_category).length === 0 ? (
                    <Tag color="green" style={{ marginLeft: 8 }}>无软冲突</Tag>
                  ) : (
                    Object.entries(report.conflict_summary.soft_by_category).map(([cat, count]) => (
                      <Tag color="orange" key={cat}>{cat}: {count}</Tag>
                    ))
                  )}
                </Col>
              </Row>
            </Card>
          </>
        )}
      </Spin>
    </div>
  );
}
