// 教师管理页面（含查看课程分配 + 分配可教课程）
import { useState, useEffect } from 'react';
import {
  Form, Input, InputNumber, Select, Button, Drawer, Table, Descriptions,
  Statistic, Row, Col, Empty, message, Tag, Typography,
  Checkbox, Divider, Alert, Spin,
} from 'antd';
import { EyeOutlined, SettingOutlined } from '@ant-design/icons';
import DataTable from '../../components/DataTable';
import { teacherApi, courseApi } from '../../api/client';
import type { TeacherCoursesResponse, TeacherCourseInfo, Course } from '../../types';

const { Text } = Typography;

export default function TeachersPage() {
  // ---- 查看课程分配状态 ----
  const [courseDrawerOpen, setCourseDrawerOpen] = useState(false);
  const [selectedTeacher, setSelectedTeacher] = useState<{ id: number; name: string; department?: string; title?: string } | null>(null);
  const [teacherCourses, setTeacherCourses] = useState<TeacherCoursesResponse | null>(null);
  const [coursesLoading, setCoursesLoading] = useState(false);

  // ---- 分配可教课程状态 ----
  const [assignDrawerOpen, setAssignDrawerOpen] = useState(false);
  const [assignTeacher, setAssignTeacher] = useState<any>(null);
  const [allCourses, setAllCourses] = useState<Course[]>([]);
  const [selectedCourseIds, setSelectedCourseIds] = useState<number[]>([]);
  const [assignLoading, setAssignLoading] = useState(false);
  const [assignSaving, setAssignSaving] = useState(false);

  // ---- 查看已排课程 ----
  const handleViewCourses = async (record: any) => {
    setSelectedTeacher({ id: record.id, name: record.name, department: record.department, title: record.title });
    setCourseDrawerOpen(true);
    setCoursesLoading(true);
    try {
      const res = await teacherApi.getCourses(record.id) as TeacherCoursesResponse;
      setTeacherCourses(res);
    } catch (e: any) {
      message.error(`加载课程失败: ${e.message}`);
      setTeacherCourses(null);
    } finally {
      setCoursesLoading(false);
    }
  };

  // ---- 分配可教课程 ----
  const handleOpenAssign = async (record: any) => {
    setAssignTeacher(record);
    setAssignDrawerOpen(true);
    setAssignLoading(true);

    // 解析教师当前的 courses_can_teach
    let currentIds: number[] = [];
    if (record.courses_can_teach) {
      try {
        const parsed = JSON.parse(record.courses_can_teach);
        currentIds = Array.isArray(parsed) ? parsed.map(Number) : [];
      } catch {
        currentIds = [];
      }
    }
    setSelectedCourseIds(currentIds);

    // 加载全量课程
    try {
      const courses = await courseApi.list({ limit: 500 }) as Course[];
      setAllCourses(courses);
    } catch (e: any) {
      message.error(`加载课程列表失败: ${e.message}`);
    } finally {
      setAssignLoading(false);
    }
  };

  const handleSaveAssign = async () => {
    if (!assignTeacher) return;
    setAssignSaving(true);
    try {
      await teacherApi.update(assignTeacher.id, {
        courses_can_teach: JSON.stringify(selectedCourseIds),
      });
      message.success(`${assignTeacher.name} 的课程分配已更新`);
      setAssignDrawerOpen(false);
    } catch (e: any) {
      message.error(`保存失败: ${e.message}`);
    } finally {
      setAssignSaving(false);
    }
  };

  // 课程表格列（查看已排课程用）
  const courseColumns = [
    { title: '课程名称', dataIndex: 'course_name', key: 'course_name', width: 130 },
    { title: '课程编码', dataIndex: 'course_code', key: 'course_code', width: 90 },
    { title: '授课班级', dataIndex: 'class_name', key: 'class_name', width: 100, render: (v: string) => <Tag color="purple">{v}</Tag> },
    { title: '学期次数', dataIndex: 'semester_sessions', key: 'semester_sessions', width: 65 },
    { title: '周次数', dataIndex: 'weekly_sessions', key: 'weekly_sessions', width: 55 },
    { title: '每次课时', dataIndex: 'hours_per_session', key: 'hours_per_session', width: 65 },
    { title: '总课时', dataIndex: 'total_hours', key: 'total_hours', width: 55, render: (v: number | null) => v ?? '-' },
    { title: '周排课次数', dataIndex: 'time_slots', key: 'time_slots', width: 75 },
  ];

  // 按专业分组的课程（分配可教课程用）
  const coursesByDept: Record<string, Course[]> = {};
  for (const c of allCourses) {
    const dept = c.department || '通用';
    if (!coursesByDept[dept]) coursesByDept[dept] = [];
    coursesByDept[dept].push(c);
  }

  return (
    <>
      <DataTable
        title="教师管理"
        entityType="teachers"
        api={teacherApi}
        columns={[
          { title: 'ID', dataIndex: 'id', width: 60 },
          { title: '姓名', dataIndex: 'name', width: 90 },
          { title: '工号', dataIndex: 'teacher_code', width: 100 },
          { title: '部门', dataIndex: 'department', width: 120 },
          { title: '职称', dataIndex: 'title', width: 100 },
          { title: '邮箱', dataIndex: 'email', width: 160 },
          { title: '每周最大课时', dataIndex: 'max_weekly_hours', width: 100 },
        ]}
        formFields={() => (
          <>
            <Form.Item name="name" label="姓名" rules={[{ required: true }]}>
              <Input placeholder="教师姓名" />
            </Form.Item>
            <Form.Item name="teacher_code" label="工号" rules={[{ required: true }]}>
              <Input placeholder="教师工号/编号" />
            </Form.Item>
            <Form.Item name="department" label="所属部门">
              <Input placeholder="如: 数学教研组" />
            </Form.Item>
            <Form.Item name="title" label="职称">
              <Select options={['教授', '副教授', '讲师', '助教', '高级教师', '一级教师'].map(t => ({ label: t, value: t }))} />
            </Form.Item>
            <Form.Item name="email" label="邮箱">
              <Input placeholder="email@school.edu.cn" />
            </Form.Item>
            <Form.Item name="phone" label="电话">
              <Input placeholder="联系电话" />
            </Form.Item>
            <Form.Item name="max_weekly_hours" label="每周最大课时">
              <InputNumber min={2} max={40} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="remarks" label="备注">
              <Input.TextArea rows={2} />
            </Form.Item>
          </>
        )}
        extraRowActions={(record) => (
          <>
            <Button
              type="link"
              size="small"
              icon={<SettingOutlined />}
              onClick={() => handleOpenAssign(record)}
              style={{ color: '#f59e0b' }}
            >
              分配课程
            </Button>
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewCourses(record)}
              style={{ color: '#533afd' }}
            >
              查看课程
            </Button>
          </>
        )}
      />

      {/* ===== Drawer 1: 查看已排课表 ===== */}
      <Drawer
        title={selectedTeacher ? `${selectedTeacher.name} - 已排课程` : '已排课程'}
        open={courseDrawerOpen}
        onClose={() => setCourseDrawerOpen(false)}
        width={620}
        destroyOnClose
      >
        {selectedTeacher && (
          <Descriptions size="small" column={2} style={{ marginBottom: 20 }}>
            <Descriptions.Item label="教师">{selectedTeacher.name}</Descriptions.Item>
            <Descriptions.Item label="部门">{selectedTeacher.department || '未设置'}</Descriptions.Item>
            <Descriptions.Item label="职称">{selectedTeacher.title || '未设置'}</Descriptions.Item>
          </Descriptions>
        )}

        {teacherCourses && teacherCourses.courses.length > 0 ? (
          <>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Statistic title="课程门数" value={teacherCourses.courses.length} suffix="门" valueStyle={{ color: '#533afd' }} />
              </Col>
              <Col span={12}>
                <Statistic title="每周总课时" value={teacherCourses.total_weekly_hours} suffix="学时" valueStyle={{ color: '#10b981' }} />
              </Col>
            </Row>
            <Table
              dataSource={teacherCourses.courses}
              columns={courseColumns}
              rowKey={(r: TeacherCourseInfo) => `${r.course_id}-${r.class_name}`}
              loading={coursesLoading}
              pagination={false}
              size="small"
              style={{ border: '1px solid #e3e8ee', borderRadius: 8 }}
            />
          </>
        ) : (
          <Empty description={coursesLoading ? '加载中...' : '该教师暂无排课记录，请先执行排课'} style={{ marginTop: 60 }} />
        )}
      </Drawer>

      {/* ===== Drawer 2: 分配可教课程 ===== */}
      <Drawer
        title={assignTeacher ? `${assignTeacher.name} - 分配可教课程` : '分配可教课程'}
        open={assignDrawerOpen}
        onClose={() => setAssignDrawerOpen(false)}
        width={560}
        destroyOnClose
        footer={
          <div style={{ textAlign: 'right' }}>
            <Button onClick={() => setAssignDrawerOpen(false)} style={{ marginRight: 8 }}>
              取消
            </Button>
            <Button
              type="primary"
              onClick={handleSaveAssign}
              loading={assignSaving}
              icon={<SettingOutlined />}
            >
              保存分配
            </Button>
          </div>
        }
      >
        {assignTeacher && (
          <Descriptions size="small" column={2} style={{ marginBottom: 12 }}>
            <Descriptions.Item label="教师">{assignTeacher.name}</Descriptions.Item>
            <Descriptions.Item label="部门">{assignTeacher.department || '未设置'}</Descriptions.Item>
          </Descriptions>
        )}

        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="勾选该教师可以教授的课程。排课时，该教师只会被分配到已勾选的课程，避免跨专业分配。"
        />

        {assignLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin tip="加载课程列表..." />
          </div>
        ) : (
          <Checkbox.Group
            value={selectedCourseIds}
            onChange={(vals) => setSelectedCourseIds(vals as number[])}
            style={{ width: '100%' }}
          >
            {Object.entries(coursesByDept).map(([dept, courses]) => {
              const deptCourseIds = courses.map(c => c.id);
              const allChecked = deptCourseIds.every(id => selectedCourseIds.includes(id));
              const someChecked = deptCourseIds.some(id => selectedCourseIds.includes(id));
              return (
                <div key={dept} style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                    <Tag color="purple">{dept}</Tag>
                    <Button
                      type="link"
                      size="small"
                      onClick={() => {
                        if (allChecked) {
                          setSelectedCourseIds(selectedCourseIds.filter(id => !deptCourseIds.includes(id)));
                        } else {
                          setSelectedCourseIds([...new Set([...selectedCourseIds, ...deptCourseIds])]);
                        }
                      }}
                    >
                      {allChecked ? '取消全选' : '全选'}
                    </Button>
                  </div>
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
              );
            })}
          </Checkbox.Group>
        )}

        <Divider />
        <Text type="secondary">
          已选择 <Text strong style={{ color: '#533afd' }}>{selectedCourseIds.length}</Text> / {allCourses.length} 门课程
        </Text>
      </Drawer>
    </>
  );
}
