// 课表导出页面
import { useState, useEffect } from 'react';
import {
  Card, Button, Space, Select, Typography, Row, Col, Tag, message
} from 'antd';
import {
  FileExcelOutlined, FilePdfOutlined, DownloadOutlined,
  TeamOutlined, UserOutlined, BankOutlined
} from '@ant-design/icons';
import { ioApi, scheduleApi } from '../api/client';

const { Title, Text, Paragraph } = Typography;

export default function ExportPage() {
  const [versions, setVersions] = useState<{ version: string }[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<string | undefined>();
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    scheduleApi.getVersions().then((res: any) => setVersions(res || [])).catch(() => {});
  }, []);

  const handleExport = async (format: 'excel' | 'pdf', viewType?: string) => {
    setExporting(true);
    try {
      let res: any;
      if (format === 'excel') {
        res = await ioApi.exportExcel(selectedVersion);
      } else {
        res = await ioApi.exportPdf(selectedVersion, viewType);
      }
      const blob = new Blob([res as any], {
        type: format === 'excel'
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          : 'application/pdf'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `排课方案_${selectedVersion || 'latest'}_${viewType || 'all'}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      a.click();
      URL.revokeObjectURL(url);
      message.success(`${format.toUpperCase()}导出成功`);
    } catch (e: any) {
      message.error(`导出失败: ${e.message}`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div style={{ maxWidth: 900 }}>
      <Title level={4} style={{ color: '#0d253d', marginBottom: 20 }}>
        <DownloadOutlined style={{ color: '#533afd', marginRight: 8 }} />
        导出课表
      </Title>

      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card bordered style={{ borderColor: '#e3e8ee', marginBottom: 16 }}>
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              <div>
                <Text strong style={{ display: 'block', marginBottom: 8, color: '#0d253d' }}>
                  选择排课版本
                </Text>
                <Select
                  allowClear
                  placeholder="选择要导出的排课版本（留空则导出最新版本）"
                  value={selectedVersion}
                  onChange={setSelectedVersion}
                  style={{ width: '100%', maxWidth: 400 }}
                  options={versions.map(v => ({ label: v.version, value: v.version }))}
                />
              </div>
            </Space>
          </Card>
        </Col>

        {/* Excel 导出 */}
        <Col xs={24} md={12}>
          <Card
            bordered
            style={{ borderColor: '#e3e8ee', height: '100%' }}
            actions={[
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={() => handleExport('excel')}
                loading={exporting}
                block
                style={{ margin: '0 12px' }}
              >
                导出Excel
              </Button>
            ]}
          >
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <FileExcelOutlined style={{ fontSize: 48, color: '#10b981', marginBottom: 12 }} />
              <Title level={5} style={{ color: '#0d253d' }}>Excel 格式</Title>
              <Paragraph type="secondary" style={{ fontSize: 13 }}>
                包含4个工作表：按班级课表、按教师课表、按教室课表、全部排课数据 +
                统计信息。适合进一步数据处理和打印。
              </Paragraph>
              <Space>
                <Tag color="green">多工作表</Tag>
                <Tag color="blue">结构化数据</Tag>
                <Tag color="purple">可编辑</Tag>
              </Space>
            </div>
          </Card>
        </Col>

        {/* PDF 导出 */}
        <Col xs={24} md={12}>
          <Card
            bordered
            style={{ borderColor: '#e3e8ee', height: '100%' }}
          >
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <FilePdfOutlined style={{ fontSize: 48, color: '#ea2261', marginBottom: 12 }} />
              <Title level={5} style={{ color: '#0d253d' }}>PDF 格式</Title>
              <Paragraph type="secondary" style={{ fontSize: 13 }}>
                精美的格式化课表，支持按班级、教师、教室三种视图导出。
                适合直接打印和分发。
              </Paragraph>
              <Space direction="vertical" size={12} style={{ width: '100%', maxWidth: 280 }}>
                <Button
                  icon={<TeamOutlined />}
                  onClick={() => handleExport('pdf', 'class')}
                  loading={exporting}
                  block
                  style={{ borderColor: '#533afd', color: '#533afd' }}
                >
                  按班级视图导出
                </Button>
                <Button
                  icon={<UserOutlined />}
                  onClick={() => handleExport('pdf', 'teacher')}
                  loading={exporting}
                  block
                  style={{ borderColor: '#3b82f6', color: '#3b82f6' }}
                >
                  按教师视图导出
                </Button>
                <Button
                  icon={<BankOutlined />}
                  onClick={() => handleExport('pdf', 'classroom')}
                  loading={exporting}
                  block
                  style={{ borderColor: '#10b981', color: '#10b981' }}
                >
                  按教室视图导出
                </Button>
              </Space>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
