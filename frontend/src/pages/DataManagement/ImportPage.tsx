// CSV数据导入页面
import { useState } from 'react';
import { Card, Upload, Button, Select, Space, Typography, Alert, message, Steps } from 'antd';
import { InboxOutlined, DownloadOutlined, UploadOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { ioApi } from '../../api/client';

const { Title, Text } = Typography;
const { Dragger } = Upload;

const entityOptions = [
  { label: '班级数据', value: 'classes' },
  { label: '教师数据', value: 'teachers' },
  { label: '课程数据', value: 'courses' },
  { label: '教室数据', value: 'classrooms' },
];

export default function ImportPage() {
  const [entityType, setEntityType] = useState<string>('classes');
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleDownloadTemplate = async () => {
    try {
      const res = await ioApi.downloadTemplate(entityType);
      const blob = new Blob([res as any], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${entityType}_template.csv`;
      a.click();
      URL.revokeObjectURL(url);
      message.success('模板下载成功');
    } catch (e: any) {
      message.error(`下载失败: ${e.message}`);
    }
  };

  const handleImport = async () => {
    if (!file) {
      message.warning('请先选择CSV文件');
      return;
    }
    setLoading(true);
    try {
      const res = await ioApi.importCsv(entityType, file);
      setResult(res);
      if ((res as any).success) {
        message.success((res as any).summary || '导入成功');
      }
    } catch (e: any) {
      message.error(`导入失败: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 900 }}>
      <Title level={4} style={{ color: '#0d253d', marginBottom: 20 }}>CSV批量数据导入</Title>

      <Steps
        current={result ? 2 : file ? 1 : 0}
        size="small"
        style={{ marginBottom: 24 }}
        items={[
          { title: '选择数据类型', icon: <CheckCircleOutlined /> },
          { title: '上传CSV文件', icon: <UploadOutlined /> },
          { title: '查看导入结果', icon: <CheckCircleOutlined /> },
        ]}
      />

      <Card bordered style={{ borderColor: '#e3e8ee', marginBottom: 20 }}>
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <div>
            <Text strong style={{ display: 'block', marginBottom: 8, color: '#0d253d' }}>
              1. 选择要导入的数据类型
            </Text>
            <Select
              options={entityOptions}
              value={entityType}
              onChange={(v) => { setEntityType(v); setResult(null); setFile(null); }}
              style={{ width: 200 }}
            />
          </div>

          <div>
            <Text strong style={{ display: 'block', marginBottom: 8, color: '#0d253d' }}>
              2. 下载CSV模板（按模板格式填写数据）
            </Text>
            <Button icon={<DownloadOutlined />} onClick={handleDownloadTemplate}>
              下载{entityOptions.find(e => e.value === entityType)?.label}模板
            </Button>
          </div>

          <div>
            <Text strong style={{ display: 'block', marginBottom: 8, color: '#0d253d' }}>
              3. 上传填写好的CSV文件
            </Text>
            <Dragger
              accept=".csv"
              maxCount={1}
              beforeUpload={(f) => { setFile(f); setResult(null); return false; }}
              onRemove={() => { setFile(null); setResult(null); }}
              style={{ background: '#f6f9fc' }}
            >
              <p className="ant-upload-drag-icon"><InboxOutlined style={{ color: '#533afd' }} /></p>
              <p className="ant-upload-text">点击或拖拽CSV文件到此区域</p>
              <p className="ant-upload-hint">支持.csv格式文件，请按模板格式填写数据</p>
            </Dragger>
          </div>

          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={handleImport}
            loading={loading}
            disabled={!file}
            size="large"
          >
            开始导入
          </Button>
        </Space>
      </Card>

      {/* 导入结果 */}
      {result && (
        <Card title="导入结果" bordered style={{ borderColor: '#e3e8ee' }}>
          {result.success ? (
            <Alert type="success" message={result.summary} showIcon style={{ marginBottom: 12 }} />
          ) : (
            <Alert type="warning" message={result.summary} showIcon style={{ marginBottom: 12 }} />
          )}

          {result.errors?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <Text strong style={{ color: '#ea2261' }}>错误信息：</Text>
              <ul style={{ marginTop: 4 }}>
                {result.errors.map((err: string, i: number) => (
                  <li key={i}><Text type="danger">{err}</Text></li>
                ))}
              </ul>
            </div>
          )}
          {result.warnings?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <Text strong style={{ color: '#f59e0b' }}>警告信息：</Text>
              <ul style={{ marginTop: 4 }}>
                {result.warnings.map((warn: string, i: number) => (
                  <li key={i}><Text type="warning">{warn}</Text></li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
