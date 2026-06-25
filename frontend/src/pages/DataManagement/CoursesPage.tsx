// 课程管理页面
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
        { title: '类型', dataIndex: 'course_type', width: 80 },
        { title: '周课时', dataIndex: 'weekly_hours', width: 70 },
        { title: '学分', dataIndex: 'credits', width: 60 },
        { title: '需连排', dataIndex: 'requires_consecutive', width: 70, render: (v: boolean) => v ? '是' : '否' },
        { title: '需实验室', dataIndex: 'requires_lab', width: 80, render: (v: boolean) => v ? '是' : '否' },
        { title: '优先级', dataIndex: 'priority', width: 70 },
      ]}
      formFields={() => (
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
          <Form.Item name="weekly_hours" label="每周课时" rules={[{ required: true }]}>
            <InputNumber min={1} max={8} style={{ width: '100%' }} />
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
          <Form.Item name="department" label="开课部门">
            <Input placeholder="开课部门" />
          </Form.Item>
          <Form.Item name="remarks" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </>
      )}
    />
  );
}
