// 课程管理页面（含总课时自动计算）
import { useEffect } from 'react';
import { Form, Input, InputNumber, Select, Switch } from 'antd';
import DataTable from '../../components/DataTable';
import { courseApi } from '../../api/client';

export default function CoursesPage() {
  return (
    <DataTable
      title="课程管理"
      entityType="courses"
      api={courseApi}
      columns={[
        { title: 'ID', dataIndex: 'id', width: 60 },
        { title: '课程名称', dataIndex: 'name', width: 160 },
        { title: '课程编码', dataIndex: 'course_code', width: 100 },
        { title: '所属专业', dataIndex: 'department', width: 100, render: (v: string) => v || <span style={{color:'#ccc'}}>未设置</span> },
        { title: '类型', dataIndex: 'course_type', width: 80 },
        { title: '学期教学次数', dataIndex: 'semester_sessions', width: 100 },
        { title: '每周上课次数', dataIndex: 'weekly_sessions', width: 90 },
        { title: '每次课时', dataIndex: 'hours_per_session', width: 80 },
        { title: '总课时', dataIndex: 'total_hours', width: 70, render: (v: number|null) => v ?? '-' },
        { title: '学分', dataIndex: 'credits', width: 60 },
        { title: '需连排', dataIndex: 'requires_consecutive', width: 70, render: (v: boolean) => v ? '是' : '否' },
        { title: '需实验室', dataIndex: 'requires_lab', width: 80, render: (v: boolean) => v ? '是' : '否' },
        { title: '优先级', dataIndex: 'priority', width: 70 },
      ]}
      formFields={(form) => {
        // 监听学期教学次数和每次课时变化，自动计算总课时
        const semesterSessions = Form.useWatch('semester_sessions', form);
        const hoursPerSession = Form.useWatch('hours_per_session', form);

        useEffect(() => {
          if (semesterSessions != null && hoursPerSession != null) {
            const calculated = semesterSessions * hoursPerSession;
            form.setFieldValue('total_hours', calculated);
          }
        }, [semesterSessions, hoursPerSession, form]);

        return (
          <>
            <Form.Item name="name" label="课程名称" rules={[{ required: true }]}>
              <Input placeholder="如: 高等数学" />
            </Form.Item>
            <Form.Item name="course_code" label="课程编码" rules={[{ required: true }]}>
              <Input placeholder="如: MATH101" />
            </Form.Item>
            <Form.Item name="course_type" label="课程类型">
              <Select options={['必修','选修','公共课','实践课'].map(t => ({ label: t, value: t }))} />
            </Form.Item>
            <Form.Item name="semester_sessions" label="学期教学次数" rules={[{ required: true }]} help="一学期总共上几次课">
              <InputNumber min={1} max={40} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="weekly_sessions" label="每周上课次数" help="每周排几个时间段">
              <InputNumber min={1} max={8} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="hours_per_session" label="每次课时" help="一次课等于几学时，通常为2">
              <InputNumber min={1} max={6} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="total_hours"
              label="总课时"
              help="自动计算（学期教学次数 × 每次课时），可手动修改"
            >
              <InputNumber min={1} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="credits" label="学分">
              <InputNumber min={0} max={10} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="requires_consecutive" label="需要连排" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="requires_lab" label="需要实验室" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="priority" label="优先级(0-10)">
              <InputNumber min={0} max={10} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="department" label="所属专业" help="与班级的「所属专业」一致时，该课程优先分配给对应班级">
              <Input placeholder="如: 人工智能/理科/文科（留空则为通用课）" />
            </Form.Item>
            <Form.Item name="remarks" label="备注">
              <Input.TextArea rows={2} />
            </Form.Item>
          </>
        );
      }}
    />
  );
}
