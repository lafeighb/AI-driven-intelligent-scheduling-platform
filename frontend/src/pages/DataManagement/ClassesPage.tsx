// 班级管理页面
import { Form, Input, InputNumber, Select } from 'antd';
import DataTable from '../../components/DataTable';
import { classApi } from '../../api/client';

export default function ClassesPage() {
  return (
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
            <Input placeholder="如: 高一(1)班" />
          </Form.Item>
          <Form.Item name="grade" label="年级" rules={[{ required: true }]}>
            <Select options={['高一','高二','高三','大一','大二','大三','大四'].map(g => ({ label: g, value: g }))} />
          </Form.Item>
          <Form.Item name="student_count" label="学生人数">
            <InputNumber min={1} max={200} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="department" label="所属专业">
            <Input placeholder="如: 理科/文科/计算机科学" />
          </Form.Item>
          <Form.Item name="homeroom_teacher" label="班主任">
            <Input placeholder="班主任姓名" />
          </Form.Item>
          <Form.Item name="remarks" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </>
      )}
    />
  );
}
