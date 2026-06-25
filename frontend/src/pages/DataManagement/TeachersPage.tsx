// 教师管理页面
import { Form, Input, InputNumber, Select } from 'antd';
import DataTable from '../../components/DataTable';
import { teacherApi } from '../../api/client';

export default function TeachersPage() {
  return (
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
            <Select options={['教授','副教授','讲师','助教','高级教师','一级教师'].map(t => ({ label: t, value: t }))} />
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
    />
  );
}
