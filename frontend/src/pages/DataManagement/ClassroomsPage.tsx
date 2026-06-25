// 教室管理页面
import { Form, Input, InputNumber, Select, Switch } from 'antd';
import DataTable from '../../components/DataTable';
import { classroomApi } from '../../api/client';

export default function ClassroomsPage() {
  return (
    <DataTable
      title="教室管理"
      entityType="classrooms"
      api={classroomApi}
      columns={[
        { title: 'ID', dataIndex: 'id', width: 60 },
        { title: '教室名称', dataIndex: 'name', width: 130 },
        { title: '编号', dataIndex: 'room_code', width: 90 },
        { title: '教学楼', dataIndex: 'building', width: 100 },
        { title: '楼层', dataIndex: 'floor', width: 60 },
        { title: '容量', dataIndex: 'capacity', width: 70 },
        { title: '类型', dataIndex: 'room_type', width: 100 },
        { title: '多媒体', dataIndex: 'has_multimedia', width: 70, render: (v: boolean) => v ? '有' : '无' },
        { title: '可用', dataIndex: 'is_available', width: 60, render: (v: boolean) => v ? '是' : '否' },
      ]}
      formFields={() => (
        <>
          <Form.Item name="name" label="教室名称" rules={[{ required: true }]}>
            <Input placeholder="如: 教学楼A-101" />
          </Form.Item>
          <Form.Item name="room_code" label="教室编号" rules={[{ required: true }]}>
            <Input placeholder="如: A101" />
          </Form.Item>
          <Form.Item name="building" label="教学楼">
            <Input placeholder="教学楼名称" />
          </Form.Item>
          <Form.Item name="floor" label="楼层">
            <InputNumber min={1} max={20} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="capacity" label="容纳人数" rules={[{ required: true }]}>
            <InputNumber min={1} max={500} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="room_type" label="教室类型">
            <Select options={['普通教室','实验室','机房','多媒体教室','阶梯教室','会议室'].map(t => ({ label: t, value: t }))} />
          </Form.Item>
          <Form.Item name="has_multimedia" label="多媒体设备" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="is_available" label="是否可用" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="remarks" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </>
      )}
    />
  );
}
