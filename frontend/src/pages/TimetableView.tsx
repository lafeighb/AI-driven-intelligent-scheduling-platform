// 课表视图页面 - 甘特图风格，支持按班级/教师/教室三维度查看
import { useState, useEffect, useCallback } from 'react';
import {
  Card, Select, Space, Typography, Tabs, Button, Spin, Empty, Tooltip
} from 'antd';
import {
  TeamOutlined, UserOutlined, BankOutlined,
  LeftOutlined, RightOutlined
} from '@ant-design/icons';
import { scheduleApi } from '../api/client';
import type { ScheduleEntry } from '../types';

const { Title, Text } = Typography;

const DAYS = ['周一', '周二', '周三', '周四', '周五'];
const PERIODS = Array.from({ length: 8 }, (_, i) => i + 1);
const COLORS = [
  '#533afd', '#3b82f6', '#10b981', '#f59e0b', '#ea2261',
  '#8b5cf6', '#06b6d4', '#84cc16', '#f97316', '#ec4899',
];

export default function TimetableView() {
  const [entries, setEntries] = useState<ScheduleEntry[]>([]);
  const [viewType, setViewType] = useState<'class' | 'teacher' | 'classroom'>('class');
  const [groups, setGroups] = useState<string[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [weekNumber, setWeekNumber] = useState(1);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res: any = await scheduleApi.list({ limit: 2000 });
      const data = (res || []) as ScheduleEntry[];
      setEntries(data);

      // 提取分组
      const fieldMap = { class: 'class_name', teacher: 'teacher_name', classroom: 'classroom_name' };
      const field = fieldMap[viewType];
      const uniqueGroups = [...new Set(data.map(e => (e as any)[field] || ''))].filter(Boolean).sort();
      setGroups(uniqueGroups);
      if (!selectedGroup && uniqueGroups.length > 0) {
        setSelectedGroup(uniqueGroups[0]);
      }
    } catch {
      setEntries([]);
      setGroups([]);
    } finally {
      setLoading(false);
    }
  }, [viewType]);

  useEffect(() => { loadData(); }, [loadData]);

  // 过滤当前视图和分组的条目
  const fieldMap = { class: 'class_name', teacher: 'teacher_name', classroom: 'classroom_name' };
  const filteredEntries = entries.filter(e =>
    (e as any)[fieldMap[viewType]] === selectedGroup && e.week_number === weekNumber
  );

  // 构建网格数据
  const grid: Record<string, ScheduleEntry[]> = {};
  for (const day of DAYS) {
    for (const period of PERIODS) {
      grid[`${day}-${period}`] = [];
    }
  }
  for (const entry of filteredEntries) {
    const dayName = DAYS[entry.day_of_week - 1];
    for (let p = entry.period_start; p <= entry.period_end; p++) {
      const key = `${dayName}-${p}`;
      if (grid[key]) {
        grid[key].push(entry);
      }
    }
  }

  // 课程颜色映射
  const courseColorMap: Record<string, string> = {};
  const uniqueCourses = [...new Set(filteredEntries.map(e => e.course_name || ''))].filter(Boolean);
  uniqueCourses.forEach((c, i) => { courseColorMap[c] = COLORS[i % COLORS.length]; });

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <Title level={4} style={{ margin: 0, color: '#0d253d' }}>课表视图</Title>
        <Space wrap>
          <Tabs
            activeKey={viewType}
            onChange={(v) => { setViewType(v as any); setSelectedGroup(''); }}
            items={[
              { key: 'class', label: <span><TeamOutlined /> 按班级</span> },
              { key: 'teacher', label: <span><UserOutlined /> 按教师</span> },
              { key: 'classroom', label: <span><BankOutlined /> 按教室</span> },
            ]}
            style={{ marginBottom: 0 }}
          />
          <Select
            showSearch
            value={selectedGroup || undefined}
            onChange={setSelectedGroup}
            placeholder="选择..."
            style={{ width: 180 }}
            options={groups.map(g => ({ label: g, value: g }))}
            filterOption={(input, option) => (option?.label as string)?.includes(input)}
          />
          <Space>
            <Button icon={<LeftOutlined />} disabled={weekNumber <= 1} onClick={() => setWeekNumber(w => w - 1)} size="small" />
            <Text strong style={{ minWidth: 60, textAlign: 'center' }}>第{weekNumber}周</Text>
            <Button icon={<RightOutlined />} disabled={weekNumber >= 20} onClick={() => setWeekNumber(w => w + 1)} size="small" />
          </Space>
        </Space>
      </div>

      <Spin spinning={loading}>
        {filteredEntries.length === 0 ? (
          <Card bordered style={{ borderColor: '#e3e8ee' }}>
            <Empty description="暂无排课数据，请先执行排课生成课表" />
          </Card>
        ) : (
          <Card bordered style={{ borderColor: '#e3e8ee', padding: 0 }} bodyStyle={{ padding: 10 }}>
            {/* 甘特图风格课表 */}
            <div style={{ overflow: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 700 }}>
                <thead>
                  <tr>
                    <th style={thStyle}>节次</th>
                    {DAYS.map(day => (
                      <th key={day} style={{ ...thStyle, width: '18%' }}>{day}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {PERIODS.map(period => (
                    <tr key={period}>
                      <td style={{ ...tdStyle, fontWeight: 600, background: '#f6f9fc', textAlign: 'center' }}>
                        第{period}节
                      </td>
                      {DAYS.map(day => {
                        const key = `${day}-${period}`;
                        const cellEntries = grid[key] || [];
                        // 去重（同一门课可能跨多节）
                        const uniqueEntries = cellEntries.filter((e, i, arr) =>
                          arr.findIndex(x => x.id === e.id) === i
                        );
                        return (
                          <td key={key} style={tdStyle}>
                            {uniqueEntries.map(entry => (
                              <Tooltip
                                key={entry.id}
                                title={
                                  <div>
                                    <div>课程: {entry.course_name}</div>
                                    <div>教师: {entry.teacher_name}</div>
                                    <div>教室: {entry.classroom_name}</div>
                                    <div>
                                      {DAYS[entry.day_of_week - 1]} 第{entry.period_start}-{entry.period_end}节
                                    </div>
                                  </div>
                                }
                              >
                                <div style={{
                                  ...cellStyle,
                                  background: courseColorMap[entry.course_name || ''] || '#533afd',
                                  opacity: entry.is_manual ? 0.7 : 1,
                                }}>
                                  <Text strong style={{ color: '#fff', fontSize: 11, lineHeight: 1.3 }}>
                                    {entry.course_name}
                                  </Text>
                                  <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 10, display: 'block' }}>
                                    {entry.classroom_name}
                                  </Text>
                                </div>
                              </Tooltip>
                            ))}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </Spin>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  padding: '10px 8px',
  background: '#f6f9fc',
  borderBottom: '2px solid #e3e8ee',
  fontWeight: 600,
  color: '#0d253d',
  fontSize: 13,
  textAlign: 'center',
};

const tdStyle: React.CSSProperties = {
  padding: 4,
  borderBottom: '1px solid #e3e8ee',
  borderRight: '1px solid #f0f2f5',
  verticalAlign: 'top',
  minHeight: 60,
  height: 60,
};

const cellStyle: React.CSSProperties = {
  padding: '4px 6px',
  borderRadius: 4,
  marginBottom: 2,
  cursor: 'pointer',
  transition: 'opacity 0.2s',
  minHeight: 36,
};
