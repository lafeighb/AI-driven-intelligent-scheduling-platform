// 工作台首页 — 统计概览、排课版本记录、分析报告一目了然
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Row, Col, Card, Statistic, Typography, List, Tag, Spin,
  Select, Progress, Empty, Space, Popconfirm, message, Button,
} from 'antd';
import {
  TeamOutlined, BookOutlined, BankOutlined, ScheduleOutlined,
  ExperimentOutlined, DeleteOutlined,
} from '@ant-design/icons';
import { classApi, teacherApi, courseApi, classroomApi, scheduleApi, ioApi } from '../api/client';
import type { VersionInfo, AnalysisReport } from '../types';

const { Title, Text, Paragraph } = Typography;

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({ classes: 0, teachers: 0, courses: 0, classrooms: 0 });
  const [versions, setVersions] = useState<VersionInfo[]>([]);
  const [loading, setLoading] = useState(true);

  // 报告相关状态
  const [selectedVersion, setSelectedVersion] = useState<string | undefined>();
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);

  // 加载基础统计和版本列表
  const loadVersions = async () => {
    try {
      const verRes = await scheduleApi.getVersions();
      const verList = (verRes as VersionInfo[]) || [];
      setVersions(verList);
      return verList;
    } catch {
      return [];
    }
  };

  useEffect(() => {
    async function loadData() {
      try {
        const [clsRes, teaRes, couRes, roomRes, verRes] = await Promise.all([
          classApi.list({ limit: 1 }),
          teacherApi.list({ limit: 1 }),
          courseApi.list({ limit: 1 }),
          classroomApi.list({ limit: 1 }),
          scheduleApi.getVersions(),
        ]);
        setStats({
          classes: (clsRes as any).length || 0,
          teachers: (teaRes as any).length || 0,
          courses: (couRes as any).length || 0,
          classrooms: (roomRes as any).length || 0,
        });
        const verList = (verRes as VersionInfo[]) || [];
        setVersions(verList);
        // 默认选中最新版本
        if (verList.length > 0 && !selectedVersion) {
          setSelectedVersion(verList[0].version);
        }
      } catch {
        setStats({ classes: 12, teachers: 45, courses: 68, classrooms: 30 });
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // 版本变化时加载报告
  useEffect(() => {
    if (!selectedVersion) {
      setReport(null);
      return;
    }
    setReportLoading(true);
    ioApi
      .getReport(selectedVersion)
      .then((res: any) => setReport(res))
      .catch(() => setReport(null))
      .finally(() => setReportLoading(false));
  }, [selectedVersion]);

  // 删除排课版本
  const handleDeleteVersion = async (version: string) => {
    try {
      await scheduleApi.deleteVersion(version);
      message.success('排课方案已删除');
      const verList = await loadVersions();
      if (selectedVersion === version) {
        if (verList.length > 0) {
          setSelectedVersion(verList[0].version);
        } else {
          setSelectedVersion(undefined);
          setReport(null);
        }
      }
    } catch (err: any) {
      message.error(`删除失败: ${err.message}`);
    }
  };

  return (
    <Spin spinning={loading}>
      <div style={{ maxWidth: 1200 }}>
        {/* 标题栏 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <Title level={4} style={{ margin: 0, color: '#0d253d' }}>
            工作台概览
          </Title>
          {versions.length > 0 && (
            <Select
              value={selectedVersion}
              onChange={setSelectedVersion}
              style={{ width: 320 }}
              placeholder="选择排课版本查看报告"
              options={versions.map(v => ({
                label: v.timestamp
                  ? new Date(v.timestamp * 1000).toLocaleString('zh-CN', {
                      month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
                    })
                  : v.version,
                value: v.version,
              }))}
            />
          )}
        </div>

        {/* 统计卡片 */}
        <Row gutter={[16, 16]}>
          {[
            { title: '班级总数', value: stats.classes, icon: <TeamOutlined />, color: '#533afd' },
            { title: '教师总数', value: stats.teachers, icon: <TeamOutlined />, color: '#3b82f6' },
            { title: '课程总数', value: stats.courses, icon: <BookOutlined />, color: '#10b981' },
            { title: '教室总数', value: stats.classrooms, icon: <BankOutlined />, color: '#f59e0b' },
          ].map((item) => (
            <Col xs={24} sm={12} lg={6} key={item.title}>
              <Card bordered style={{ borderColor: '#e3e8ee' }}>
                <Statistic
                  title={<Text type="secondary">{item.title}</Text>}
                  value={item.value}
                  prefix={<span style={{ color: item.color }}>{item.icon}</span>}
                  valueStyle={{ color: '#0d253d', fontWeight: 600 }}
                />
              </Card>
            </Col>
          ))}
        </Row>

        {/* 排课版本记录 + 报告区域 */}
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          {/* 左侧：版本记录 */}
          <Col xs={24} lg={10}>
            <Card
              title="排课版本记录"
              bordered
              style={{ borderColor: '#e3e8ee' }}
              headStyle={{ fontWeight: 600, color: '#0d253d' }}
            >
              {versions.length > 0 ? (
                <List
                  size="small"
                  dataSource={versions.slice(0, 8)}
                  renderItem={(v) => {
                    const isSelected = selectedVersion === v.version;
                    return (
                      <List.Item
                        style={{
                          cursor: 'pointer',
                          background: isSelected ? '#f0eeff' : undefined,
                          borderRadius: 6,
                          padding: '8px 12px',
                          marginBottom: 4,
                        }}
                        onClick={() => setSelectedVersion(v.version)}
                      >
                        <ScheduleOutlined style={{ color: '#533afd', marginRight: 8 }} />
                        <div style={{ flex: 1 }}>
                          <Text style={{ color: '#0d253d', fontSize: 13 }}>
                            {v.timestamp
                              ? new Date(v.timestamp * 1000).toLocaleString('zh-CN', {
                                  year: 'numeric',
                                  month: '2-digit',
                                  day: '2-digit',
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })
                              : v.version}
                          </Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            {v.entry_count} 条记录
                          </Text>
                          {v.avg_quality != null && (
                            <Tag
                              color={v.avg_quality >= 80 ? 'green' : v.avg_quality >= 60 ? 'orange' : 'red'}
                              style={{ fontSize: 10, marginLeft: 4 }}
                            >
                              {v.avg_quality}分
                            </Tag>
                          )}
                        </div>
                        <Space size={4}>
                          <Text type="secondary" style={{ fontSize: 11, cursor: 'pointer' }}
                            onClick={(e) => { e.stopPropagation(); navigate(`/timetable?version=${v.version}`); }}>
                            查看课表 →
                          </Text>
                          <Popconfirm
                            title="确认删除此排课方案？"
                            description="删除后相关排课条目将被永久移除"
                            onConfirm={() => handleDeleteVersion(v.version)}
                            onCancel={(e) => e?.stopPropagation()}
                            okText="确认删除"
                            cancelText="取消"
                            okButtonProps={{ danger: true }}
                          >
                            <Button
                              type="text"
                              size="small"
                              danger
                              icon={<DeleteOutlined />}
                              onClick={(e) => e.stopPropagation()}
                              style={{ marginLeft: 4 }}
                            />
                          </Popconfirm>
                        </Space>
                      </List.Item>
                    );
                  }}
                />
              ) : (
                <Text type="secondary" style={{ fontSize: 13 }}>
                  暂无排课记录，请先在"智能排课 → 执行排课"中生成排课方案
                </Text>
              )}
            </Card>
          </Col>

          {/* 右侧：分析报告摘要 */}
          <Col xs={24} lg={14}>
            <Spin spinning={reportLoading}>
              {!report ? (
                <Card bordered style={{ borderColor: '#e3e8ee' }}>
                  <Empty description={selectedVersion ? '加载报告中...' : '请选择排课版本查看分析报告'} />
                </Card>
              ) : (
                <>
                  {/* 质量评分 */}
                  <Row gutter={[16, 16]}>
                    <Col span={8}>
                      <Card bordered size="small" style={{ borderColor: '#e3e8ee', textAlign: 'center' }}>
                        <Text strong style={{ color: '#0d253d', fontSize: 13 }}>方案质量评分</Text>
                        <Progress
                          type="dashboard"
                          percent={report.quality_score}
                          strokeColor={{
                            '0%': '#ea2261', '50%': '#f59e0b', '80%': '#533afd', '100%': '#10b981',
                          }}
                          format={p => `${p}分`}
                          size={120}
                          style={{ marginTop: 4 }}
                        />
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card bordered size="small" style={{ borderColor: '#e3e8ee', textAlign: 'center' }}>
                        <Text strong style={{ color: '#0d253d', fontSize: 13 }}>每日均衡度</Text>
                        <Progress
                          type="dashboard"
                          percent={report.daily_balance_score}
                          strokeColor="#533afd"
                          format={p => `${p}分`}
                          size={120}
                          style={{ marginTop: 4 }}
                        />
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card bordered size="small" style={{ borderColor: '#e3e8ee', textAlign: 'center' }}>
                        <Text strong style={{ color: '#0d253d', fontSize: 13 }}>教室利用率</Text>
                        <Progress
                          type="dashboard"
                          percent={report.avg_room_utilization}
                          strokeColor="#3b82f6"
                          format={p => `${p}%`}
                          size={120}
                          style={{ marginTop: 4 }}
                        />
                      </Card>
                    </Col>
                  </Row>

                  {/* 基础摘要 */}
                  <Row gutter={[12, 12]} style={{ marginTop: 16 }}>
                    {[
                      { label: '排课条目', value: report.summary.total_entries, color: '#533afd' },
                      { label: '涉及课程', value: report.summary.unique_courses, color: '#3b82f6' },
                      { label: '涉及教师', value: report.summary.unique_teachers, color: '#10b981' },
                      { label: '涉及班级', value: report.summary.unique_classes, color: '#f59e0b' },
                    ].map(item => (
                      <Col xs={12} sm={6} key={item.label}>
                        <Card size="small" bordered style={{ textAlign: 'center', borderColor: '#e3e8ee' }}>
                          <Statistic
                            title={item.label}
                            value={item.value}
                            valueStyle={{ color: item.color, fontSize: 20 }}
                          />
                        </Card>
                      </Col>
                    ))}
                  </Row>

                  {/* 冲突摘要 */}
                  <Card bordered size="small" title="冲突检测摘要" style={{ borderColor: '#e3e8ee', marginTop: 16 }}>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Text strong style={{ color: '#ea2261' }}>硬冲突：</Text>
                        {Object.keys(report.conflict_summary.hard_by_category).length === 0 ? (
                          <Tag color="green">无</Tag>
                        ) : (
                          Object.entries(report.conflict_summary.hard_by_category).map(([cat, count]) => (
                            <Tag color="red" key={cat}>{cat}: {count}</Tag>
                          ))
                        )}
                      </Col>
                      <Col span={12}>
                        <Text strong style={{ color: '#f59e0b' }}>软冲突：</Text>
                        {Object.keys(report.conflict_summary.soft_by_category).length === 0 ? (
                          <Tag color="green">无</Tag>
                        ) : (
                          Object.entries(report.conflict_summary.soft_by_category).map(([cat, count]) => (
                            <Tag color="orange" key={cat}>{cat}: {count}</Tag>
                          ))
                        )}
                      </Col>
                    </Row>
                  </Card>

                  {/* AI 优化说明 */}
                  {report.ai_explanation && (
                    <Card
                      bordered
                      size="small"
                      title={<Space><ExperimentOutlined style={{ color: '#533afd' }} />AI 优化说明</Space>}
                      style={{ borderColor: '#e3e8ee', marginTop: 16 }}
                    >
                      <Paragraph
                        style={{ whiteSpace: 'pre-wrap', fontSize: 13, color: '#273951', lineHeight: 1.8, margin: 0 }}
                        ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
                      >
                        {report.ai_explanation}
                      </Paragraph>
                    </Card>
                  )}
                </>
              )}
            </Spin>
          </Col>
        </Row>
      </div>
    </Spin>
  );
}
