// 工作台首页
import { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Typography, List, Tag, Spin } from 'antd';
import {
  TeamOutlined, BookOutlined, BankOutlined, ScheduleOutlined,
  ThunderboltOutlined, CheckCircleOutlined,
} from '@ant-design/icons';
import { classApi, teacherApi, courseApi, classroomApi, scheduleApi } from '../api/client';
import type { ScheduleEntry } from '../types';

const { Title, Text, Paragraph } = Typography;

export default function Dashboard() {
  const [stats, setStats] = useState({ classes: 0, teachers: 0, courses: 0, classrooms: 0 });
  const [, setSchedules] = useState<ScheduleEntry[]>([]);
  const [versions, setVersions] = useState<{ version: string }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [clsRes, teaRes, couRes, roomRes, verRes, schedRes] = await Promise.all([
          classApi.list({ limit: 1 }),
          teacherApi.list({ limit: 1 }),
          courseApi.list({ limit: 1 }),
          classroomApi.list({ limit: 1 }),
          scheduleApi.getVersions(),
          scheduleApi.list({ limit: 10 }),
        ]);
        setStats({
          classes: (clsRes as any).length || 0,
          teachers: (teaRes as any).length || 0,
          courses: (couRes as any).length || 0,
          classrooms: (roomRes as any).length || 0,
        });
        setVersions((verRes as any) || []);
        setSchedules((schedRes as any) || []);
      } catch {
        // 后端未启动时使用演示数据
        setStats({ classes: 12, teachers: 45, courses: 68, classrooms: 30 });
        setVersions([{ version: 'schedule_demo_001' }]);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const features = [
    { icon: <ThunderboltOutlined style={{ color: '#533afd' }} />, title: 'AI自动排课', desc: '基于改进遗传算法的多目标优化排课引擎，支持硬约束与软约束的灵活配置' },
    { icon: <CheckCircleOutlined style={{ color: '#10b981' }} />, title: '智能冲突检测', desc: '多层冲突检测机制，自动识别教师/教室/班级时间冲突及课时分布不合理问题' },
    { icon: <ScheduleOutlined style={{ color: '#f59e0b' }} />, title: '交互式课表调整', desc: '甘特图可视化课表，支持拖拽调整课程时间、地点和教师分配' },
    { icon: <BankOutlined style={{ color: '#3b82f6' }} />, title: '多维度视图', desc: '按班级、教师、教室三维度查看课表，支持筛选与导出' },
  ];

  return (
    <Spin spinning={loading}>
      <div style={{ maxWidth: 1200 }}>
        <Title level={4} style={{ marginBottom: 24, color: '#0d253d' }}>
          工作台概览
        </Title>

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

        {/* 排课版本 + 功能特性 */}
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={14}>
            <Card
              title="功能特性"
              bordered
              style={{ borderColor: '#e3e8ee' }}
              headStyle={{ fontWeight: 600, color: '#0d253d' }}
            >
              <Row gutter={[16, 16]}>
                {features.map((f) => (
                  <Col xs={24} sm={12} key={f.title}>
                    <Card
                      size="small"
                      bordered
                      style={{ borderColor: '#e3e8ee', background: '#f6f9fc', height: '100%' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                        <span style={{ fontSize: 22, marginTop: 2 }}>{f.icon}</span>
                        <div>
                          <Text strong style={{ color: '#0d253d', fontSize: 14 }}>{f.title}</Text>
                          <Paragraph type="secondary" style={{ fontSize: 12, margin: '4px 0 0' }}>
                            {f.desc}
                          </Paragraph>
                        </div>
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Card>
          </Col>

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
                  dataSource={versions.slice(0, 5)}
                  renderItem={(v) => (
                    <List.Item>
                      <ScheduleOutlined style={{ color: '#533afd', marginRight: 8 }} />
                      <Text style={{ color: '#0d253d', fontSize: 13 }}>{v.version}</Text>
                      <Tag color="green" style={{ marginLeft: 'auto' }}>完成</Tag>
                    </List.Item>
                  )}
                />
              ) : (
                <Text type="secondary" style={{ fontSize: 13 }}>
                  暂无排课记录，请先配置约束并执行排课
                </Text>
              )}
            </Card>
          </Col>
        </Row>
      </div>
    </Spin>
  );
}
