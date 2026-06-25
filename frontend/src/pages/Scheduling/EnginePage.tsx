// AI排课引擎执行页面（三步流程：选范围 → 配参数 → 看结果）
import { useState, useEffect } from 'react';
import {
  Card, Button, Slider, Select, Space, Typography, Progress, Alert,
  Descriptions, Tag, Spin, Row, Col, Statistic, Divider, Steps,
  Checkbox, Empty, message,
} from 'antd';
import {
  ThunderboltOutlined, CheckCircleOutlined, ExperimentOutlined,
  RollbackOutlined, ArrowRightOutlined,
} from '@ant-design/icons';
import { scheduleApi, classApi, courseApi } from '../../api/client';
import type { ScheduleResult, ClassInfo, Course } from '../../types';

const { Title, Text, Paragraph } = Typography;

export default function EnginePage() {
  // 步骤控制
  const [currentStep, setCurrentStep] = useState(0);

  // Step 0: 数据
  const [allClasses, setAllClasses] = useState<ClassInfo[]>([]);
  const [allCourses, setAllCourses] = useState<Course[]>([]);
  const [selectedClassIds, setSelectedClassIds] = useState<number[]>([]);
  const [selectedCourseIds, setSelectedCourseIds] = useState<number[]>([]);
  const [dataLoading, setDataLoading] = useState(false);

  // Step 1: 配置
  const [config, setConfig] = useState({
    algorithm: 'genetic',
    population_size: 100,
    max_generations: 500,
  });

  // Step 2: 结果
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<ScheduleResult | null>(null);
  const [explanation, setExplanation] = useState('');

  // 加载班级和课程数据
  const loadSelectionData = async () => {
    setDataLoading(true);
    try {
      const [classes, courses] = await Promise.all([
        classApi.list({ limit: 500 }) as Promise<ClassInfo[]>,
        courseApi.list({ limit: 500 }) as Promise<Course[]>,
      ]);
      setAllClasses(classes);
      setAllCourses(courses);
      // 默认全选
      if (selectedClassIds.length === 0) {
        setSelectedClassIds(classes.map(c => c.id));
      }
      if (selectedCourseIds.length === 0) {
        setSelectedCourseIds(courses.map(c => c.id));
      }
    } catch (e: any) {
      message.error(`加载数据失败: ${e.message}`);
    } finally {
      setDataLoading(false);
    }
  };

  useEffect(() => { loadSelectionData(); }, []);

  // 执行排课
  const handleGenerate = async () => {
    if (selectedClassIds.length === 0 || selectedCourseIds.length === 0) {
      message.warning('请至少选择一个班级和一门课程');
      return;
    }

    setCurrentStep(2); // 先跳转到结果页
    setRunning(true);
    setProgress(10);
    setResult(null);
    setExplanation('');

    const timer = setInterval(() => {
      setProgress((p) => Math.min(p + Math.random() * 15, 90));
    }, 500);

    try {
      const res: any = await scheduleApi.generate({
        ...config,
        class_ids: selectedClassIds,
        course_ids: selectedCourseIds,
      });
      setResult(res);
      setExplanation(res.explanation || '');
      setProgress(100);
    } catch (e: any) {
      setProgress(0);
      setCurrentStep(1); // 失败回到配置页
      message.error(e.message || '排课失败，请检查数据配置');
    } finally {
      clearInterval(timer);
      setRunning(false);
    }
  };

  // 班级全选/取消
  const toggleAllClasses = (checked: boolean) => {
    setSelectedClassIds(checked ? allClasses.map(c => c.id) : []);
  };
  const toggleAllCourses = (checked: boolean) => {
    setSelectedCourseIds(checked ? allCourses.map(c => c.id) : []);
  };

  // 按专业分组课程
  const coursesByDept: Record<string, Course[]> = {};
  for (const c of allCourses) {
    const dept = c.department || '通用';
    if (!coursesByDept[dept]) coursesByDept[dept] = [];
    coursesByDept[dept].push(c);
  }

  return (
    <div style={{ maxWidth: 1100 }}>
      <Title level={4} style={{ color: '#0d253d', marginBottom: 20 }}>
        <ThunderboltOutlined style={{ color: '#533afd', marginRight: 8 }} />
        AI智能排课
      </Title>

      <Steps
        current={currentStep}
        size="small"
        style={{ marginBottom: 24 }}
        items={[
          { title: '选择排课范围', icon: <CheckCircleOutlined /> },
          { title: '配置排课参数', icon: <ExperimentOutlined /> },
          { title: '查看排课结果', icon: <ThunderboltOutlined /> },
        ]}
      />

      {/* ========== Step 0: 选择排课范围 ========== */}
      {currentStep === 0 && (
        <Spin spinning={dataLoading} tip="加载中...">
          <Row gutter={[16, 16]}>
            {/* 班级选择 */}
            <Col xs={24} lg={12}>
              <Card
                title={`选择班级（已选 ${selectedClassIds.length}/${allClasses.length}）`}
                bordered
                style={{ borderColor: '#e3e8ee' }}
                extra={
                  <Space size="small">
                    <Button size="small" type="link" onClick={() => toggleAllClasses(true)}>全选</Button>
                    <Button size="small" type="link" onClick={() => toggleAllClasses(false)}>取消</Button>
                  </Space>
                }
              >
                {allClasses.length === 0 ? (
                  <Empty description="暂无班级数据，请先在班级管理中录入" />
                ) : (
                  <Checkbox.Group
                    value={selectedClassIds}
                    onChange={(vals) => setSelectedClassIds(vals as number[])}
                    style={{ width: '100%' }}
                  >
                    <Row gutter={[4, 8]}>
                      {allClasses.map(cls => (
                        <Col span={12} key={cls.id}>
                          <Checkbox value={cls.id}>
                            <span style={{ fontSize: 13 }}>
                              {cls.name}
                              <Text type="secondary" style={{ fontSize: 11, marginLeft: 4 }}>
                                {cls.grade} {cls.department || ''}
                              </Text>
                            </span>
                          </Checkbox>
                        </Col>
                      ))}
                    </Row>
                  </Checkbox.Group>
                )}
              </Card>
            </Col>

            {/* 课程选择（按专业分组） */}
            <Col xs={24} lg={12}>
              <Card
                title={`选择课程（已选 ${selectedCourseIds.length}/${allCourses.length}）`}
                bordered
                style={{ borderColor: '#e3e8ee' }}
                extra={
                  <Space size="small">
                    <Button size="small" type="link" onClick={() => toggleAllCourses(true)}>全选</Button>
                    <Button size="small" type="link" onClick={() => toggleAllCourses(false)}>取消</Button>
                  </Space>
                }
              >
                {allCourses.length === 0 ? (
                  <Empty description="暂无课程数据，请先在课程管理中录入" />
                ) : (
                  <Checkbox.Group
                    value={selectedCourseIds}
                    onChange={(vals) => setSelectedCourseIds(vals as number[])}
                    style={{ width: '100%', maxHeight: 360, overflow: 'auto' }}
                  >
                    {Object.entries(coursesByDept).map(([dept, courses]) => (
                      <div key={dept} style={{ marginBottom: 12 }}>
                        <Tag color="purple" style={{ marginBottom: 4 }}>{dept}</Tag>
                        <Row gutter={[4, 4]}>
                          {courses.map(c => (
                            <Col span={24} key={c.id}>
                              <Checkbox value={c.id}>
                                <span style={{ fontSize: 13 }}>
                                  {c.name}
                                  <Text type="secondary" style={{ fontSize: 11, marginLeft: 4 }}>
                                    {c.course_code} ({c.semester_sessions}次/学期, {c.hours_per_session}课时/次)
                                  </Text>
                                </span>
                              </Checkbox>
                            </Col>
                          ))}
                        </Row>
                      </div>
                    ))}
                  </Checkbox.Group>
                )}
              </Card>
            </Col>
          </Row>

          <Divider />

          <Button
            type="primary"
            size="large"
            icon={<ArrowRightOutlined />}
            onClick={() => setCurrentStep(1)}
            disabled={selectedClassIds.length === 0 || selectedCourseIds.length === 0}
            style={{ height: 44, fontWeight: 600 }}
          >
            下一步：配置排课参数
          </Button>
          {selectedClassIds.length === 0 || selectedCourseIds.length === 0 ? (
            <Text type="danger" style={{ marginLeft: 12, fontSize: 12 }}>
              {selectedClassIds.length === 0 ? '请至少选择一个班级' : '请至少选择一门课程'}
            </Text>
          ) : null}
        </Spin>
      )}

      {/* ========== Step 1: 配置排课参数 ========== */}
      {currentStep === 1 && (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={10}>
            <Card title="排课参数配置" bordered style={{ borderColor: '#e3e8ee' }}>
              {/* 已选范围摘要 */}
              <Alert
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
                message={
                  <Space wrap>
                    <Tag color="blue">{selectedClassIds.length} 个班级</Tag>
                    <Tag color="purple">{selectedCourseIds.length} 门课程</Tag>
                  </Space>
                }
              />

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

                <Space style={{ width: '100%' }}>
                  <Button
                    icon={<RollbackOutlined />}
                    onClick={() => setCurrentStep(0)}
                  >
                    上一步
                  </Button>
                  <Button
                    type="primary"
                    size="large"
                    icon={<ThunderboltOutlined />}
                    onClick={handleGenerate}
                    loading={running}
                    style={{ height: 44, fontWeight: 600, flex: 1 }}
                  >
                    开始AI排课
                  </Button>
                </Space>

                {running && (
                  <Progress percent={Math.round(progress)} status="active" strokeColor="#533afd" />
                )}
              </Space>
            </Card>
          </Col>

          <Col xs={24} lg={14}>
            <Card bordered style={{ borderColor: '#e3e8ee', textAlign: 'center', padding: 60 }}>
              <ExperimentOutlined style={{ fontSize: 48, color: '#d0d6e0', marginBottom: 16 }} />
              <Paragraph type="secondary">
                已选择 {selectedClassIds.length} 个班级和 {selectedCourseIds.length} 门课程。
                <br />
                配置参数后点击"开始AI排课"，系统将自动生成最优排课方案。
              </Paragraph>
            </Card>
          </Col>
        </Row>
      )}

      {/* ========== Step 2: 查看排课结果 ========== */}
      {currentStep === 2 && (
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Space style={{ marginBottom: 12 }}>
              <Button
                icon={<RollbackOutlined />}
                onClick={() => { setCurrentStep(1); setResult(null); }}
                disabled={running}
              >
                重新排课
              </Button>
            </Space>
          </Col>

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
                      <Descriptions.Item label="排课范围">
                        <Tag color="blue">{selectedClassIds.length}班</Tag>
                        <Tag color="purple">{selectedCourseIds.length}课</Tag>
                      </Descriptions.Item>
                    </Descriptions>
                  </Card>

                  {result.hard_conflicts === 0 ? (
                    <Alert type="success" message="排课成功" description="所有硬性约束均已满足，方案可用于实际排课" showIcon style={{ marginBottom: 12 }} />
                  ) : (
                    <Alert type="error" message="存在硬性冲突" description={`发现${result.hard_conflicts}个硬性冲突，建议检查约束配置后重新排课`} showIcon style={{ marginBottom: 12 }} />
                  )}

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
              ) : running ? (
                <Card bordered style={{ borderColor: '#e3e8ee', textAlign: 'center', padding: 60 }}>
                  <Spin size="large" />
                  <Paragraph type="secondary" style={{ marginTop: 16 }}>AI正在优化排课方案，请稍候...</Paragraph>
                </Card>
              ) : (
                <Card bordered style={{ borderColor: '#e3e8ee', textAlign: 'center', padding: 60 }}>
                  <ThunderboltOutlined style={{ fontSize: 48, color: '#d0d6e0', marginBottom: 16 }} />
                  <Paragraph type="secondary">点击"重新排课"返回配置</Paragraph>
                </Card>
              )}
            </Spin>
          </Col>
        </Row>
      )}
    </div>
  );
}
