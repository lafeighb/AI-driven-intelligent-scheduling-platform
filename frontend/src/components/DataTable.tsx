// 通用数据管理表格组件
import { useState, useEffect } from 'react';
import { Table, Button, Space, Input, Modal, Form, message, Popconfirm, Typography } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const { Title } = Typography;

interface DataTableProps {
  title: string;
  entityType: string;
  columns: any[];
  formFields: (form: any) => React.ReactNode;
  api: {
    list: (params?: any) => Promise<any>;
    create: (data: any) => Promise<any>;
    update: (id: number, data: any) => Promise<any>;
    delete: (id: number) => Promise<any>;
  };
  extraFilters?: React.ReactNode;
  extraRowActions?: (record: any) => React.ReactNode;
}

export default function DataTable({ title, columns, formFields, api, extraFilters, extraRowActions }: DataTableProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  const loadData = async (searchText = '') => {
    setLoading(true);
    try {
      const res = await api.list({ search: searchText || undefined, limit: 500 });
      setData((res as any[]) || []);
    } catch (e: any) {
      message.error(`加载${title}数据失败: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleSearch = (value: string) => {
    setSearch(value);
    loadData(value);
  };

  const handleAdd = () => {
    setEditingRecord(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (record: any) => {
    setEditingRecord(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(id);
      message.success('删除成功');
      loadData(search);
    } catch (e: any) {
      message.error(`删除失败: ${e.message}`);
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      if (editingRecord) {
        await api.update(editingRecord.id, values);
        message.success('更新成功');
      } else {
        await api.create(values);
        message.success('创建成功');
      }
      setModalOpen(false);
      loadData(search);
    } catch (e: any) {
      if (e.message) message.error(`操作失败: ${e.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const actionColumn = {
    title: '操作',
    key: 'actions',
    width: extraRowActions ? 240 : 150,
    render: (_: any, record: any) => (
      <Space size="small">
        {extraRowActions?.(record)}
        <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
          编辑
        </Button>
        <Popconfirm title="确认删除?" onConfirm={() => handleDelete(record.id)} okText="确认" cancelText="取消">
          <Button type="link" size="small" danger icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      </Space>
    ),
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, color: '#0d253d' }}>{title}</Title>
        <Space>
          <Input.Search
            placeholder={`搜索${title}...`}
            allowClear
            prefix={<SearchOutlined />}
            onSearch={handleSearch}
            style={{ width: 240 }}
          />
          {extraFilters}
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            添加
          </Button>
        </Space>
      </div>

      <Table
        dataSource={data}
        columns={[...columns, actionColumn]}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 50, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }}
        scroll={{ x: 900 }}
        style={{ border: '1px solid #e3e8ee', borderRadius: 8 }}
      />

      <Modal
        title={editingRecord ? `编辑${title}` : `添加${title}`}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        confirmLoading={submitting}
        width={560}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          {formFields(form)}
        </Form>
      </Modal>
    </div>
  );
}
