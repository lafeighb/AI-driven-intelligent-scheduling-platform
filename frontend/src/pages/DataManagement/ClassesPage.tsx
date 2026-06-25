// 班级管理页面（含查看课程分配）
import { useState } from 'react';
import {
  Form, Input, InputNumber, Select, Button, Drawer, Table, Descriptions,
  Statistic, Row, Col, Empty, message, Tag, Typography,
} from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import DataTable from '../../components/DataTable';
import { classApi } from '../../api/client';
import type { ClassCoursesResponse, ClassCourseInfo } from '../../types';

const { Text } = Typography;

export default function ClassesPage() {
  const [courseDrawerOpen, setCourseDrawerOpen] = useState(false);
  const [selectedClass, setSelectedClass] = useState<{ id: number; name: string; grade: string; department?: string } | null>(null);
  const [classCourses, setClassCourses] = useState<ClassCoursesResponse | null>(null);
  const [coursesLoading, setCoursesLoading] = useState(false);

  const handleViewCourses = async (record: any) => {
    setSelectedClass({ id: record.id, name: record.name, grade: record.grade, department: record.department });
    setCourseDrawerOpen(true);
    setCoursesLoading(true);
    try {
      const res = await classApi.getCourses(record.id) as ClassCoursesResponse;
      setClassCourses(res);
    } catch (e: any) {
      message.error(`加载课程失败: ${e.message}`);
      setClassCourses(null);
    } finally {
      setCoursesLoading(false);
    }
  };

  const courseColumns = [
    { title: '课程名称', dataIndex: 'course_name', key: 'course_name', width: 140 },
    { title: '课程编码', dataIndex: 'course_code', key: 'course_code', width: 90 },
    { title: '学期次数', dataIndex: 'semester_sessions', key: 'semester_sessions', width: 70 },
    { title: '周次数', dataIndex: 'weekly_sessions', key: 'weekly_sessions', width: 60 },
    { title: '每次课时', dataIndex: 'hours_per_session', key: 'hours_per_session', width: 70 },
    { title: '总课时', dataIndex: 'total_hours', key: 'total_hours', width: 60, render: (v: number | null) => v ?? '-' },
    {
      title: '授课教师', dataIndex: 'teacher_names', key: 'teacher_names', width: 140,
      render: (names: string[]) => names?.length > 0
        ? <>{names.map(n => <Tag key={n} color="blue">{n}</Tag>)}</>
        : <span style={{ color: '#ccc' }}>未分配</span>,
    },
    { title: '周排课次数', dataIndex: 'time_slots', key: 'time_slots', width: 80 },
  ];

  return (
    <>
      <DataTable
        title="班级管理"
        entityType="classes"
        api={classApi}
        columns={[
          { title: 'ID', dataIndex: 'id', width: 60 },
          { title: '班级名称', dataIndex: 'name', width: 140 },
          { title: '年级', dataIndex: 'grade', width: 80 },
          { title: '学生人数', dataIndex: 'student_count', width: 90 },
          { title: '所属专业', dataIndex: 'department', width: 120 },
          { title: '班主任', dataIndex: 'homeroom_teacher', width: 100 },
          { title: '备注', dataIndex: 'remarks', ellipsis: true },
        ]}
        formFields={() => (
          <>
            <Form.Item name="name" label="班级名称" rules={[{ required: true }]}>
              <Input placeholder="如: 计科1班" />
            </Form.Item>
            <Form.Item name="grade" label="年级" rules={[{ required: true }]}>
              <Select options={['大一', '大二', '大三', '大四'].map(g => ({ label: g, value: g }))} />
            </Form.Item>
            <Form.Item name="student_count" label="学生人数">
              <InputNumber min={1} max={200} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="department" label="所属专业">
              <Input placeholder="如: 计算机科学" />
            </Form.Item>
            <Form.Item name="homeroom_teacher" label="班主任">
              <Input placeholder="班主任姓名" />
            </Form.Item>
            <Form.Item name="remarks" label="备注">
              <Input.TextArea rows={2} />
            </Form.Item>
          </>
        )}
        extraRowActions={(record) => (
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewCourses(record)}
            style={{ color: '#533afd' }}
          >
            查看课程
          </Button>
        )}
      />

      {/* 班级课程分配 Drawer */}
      <Drawer
        title={selectedClass ? `${selectedClass.name} - 课程分配` : '课程分配'}
        open={courseDrawerOpen}
        onClose={() => setCourseDrawerOpen(false)}
        width={680}
        destroyOnClose
      >
        {selectedClass && (
          <Descriptions size="small" column={3} style={{ marginBottom: 20 }}>
            <Descriptions.Item label="班级">{selectedClass.name}</Descriptions.Item>
            <Descriptions.Item label="年级">{selectedClass.grade}</Descriptions.Item>
            <Descriptions.Item label="所属专业">{selectedClass.department || '未设置'}</Descriptions.Item>
          </Descriptions>
        )}

        {classCourses && classCourses.courses.length > 0 ? (
          <>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Statistic
                  title="课程门数"
                  value={classCourses.courses.length}
                  suffix="门"
                  valueStyle={{ color: '#533afd' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="每周总课时"
                  value={classCourses.total_weekly_hours}
                  suffix="学时"
                  valueStyle={{ color: '#10b981' }}
                />
              </Col>
            </Row>
            <Table
              dataSource={classCourses.courses}
              columns={courseColumns}
              rowKey="course_id"
              loading={coursesLoading}
              pagination={false}
              size="small"
              style={{ border: '1px solid #e3e8ee', borderRadius: 8 }}
            />
          </>
        ) : (
          <Empty
            description={coursesLoading ? '加载中...' : '该班级暂无排课记录，请先执行排课'}
            style={{ marginTop: 60 }}
          />
        )}
      </Drawer>
    </>
  );
}
