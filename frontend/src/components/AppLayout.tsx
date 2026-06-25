// 主布局组件 - 侧边导航 + 内容区
import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Button, Typography, Dropdown, Avatar, Space, message } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  UserOutlined,
  BookOutlined,
  BankOutlined,
  ScheduleOutlined,
  SettingOutlined,
  ImportOutlined,
  ExportOutlined,
  BarChartOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ThunderboltOutlined,
  AlertOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Header, Sider, Content, Footer } = Layout;
const { Text } = Typography;

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: '工作台',
  },
  {
    key: 'data',
    icon: <TeamOutlined />,
    label: '数据管理',
    children: [
      { key: '/data/classes', icon: <TeamOutlined />, label: '班级管理' },
      { key: '/data/teachers', icon: <UserOutlined />, label: '教师管理' },
      { key: '/data/courses', icon: <BookOutlined />, label: '课程管理' },
      { key: '/data/classrooms', icon: <BankOutlined />, label: '教室管理' },
      { key: '/data/import', icon: <ImportOutlined />, label: '数据导入' },
    ],
  },
  {
    key: 'schedule',
    icon: <ScheduleOutlined />,
    label: '智能排课',
    children: [
      { key: '/schedule/constraints', icon: <SettingOutlined />, label: '约束配置' },
      { key: '/schedule/engine', icon: <ThunderboltOutlined />, label: '执行排课' },
      { key: '/schedule/conflicts', icon: <AlertOutlined />, label: '冲突检测' },
    ],
  },
  {
    key: '/timetable',
    icon: <ScheduleOutlined />,
    label: '课表视图',
  },
  {
    key: '/reports',
    icon: <BarChartOutlined />,
    label: '分析报告',
  },
  {
    key: '/export',
    icon: <ExportOutlined />,
    label: '导出课表',
  },
];

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const selectedKey = location.pathname === '/' ? '/' : location.pathname;

  const handleLogout = () => {
    logout();
    message.success('已退出登录');
    navigate('/login', { replace: true });
  };

  // 找到展开的子菜单
  const openKeys = menuItems
    .filter((item) => 'children' in item)
    .filter((item) => item.children?.some((child) => selectedKey.startsWith(child.key)))
    .map((item) => item.key);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={240}
        style={{
          background: '#0d253d',
          borderRight: '1px solid rgba(227, 232, 238, 0.15)',
        }}
      >
        {/* Logo */}
        <div
          style={{
            height: 56,
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: collapsed ? 0 : '0 20px',
            borderBottom: '1px solid rgba(227, 232, 238, 0.1)',
          }}
        >
          <ThunderboltOutlined
            style={{ fontSize: 24, color: '#533afd', marginRight: collapsed ? 0 : 10 }}
          />
          {!collapsed && (
            <Text
              strong
              style={{
                color: '#ffffff',
                fontSize: 16,
                letterSpacing: '-0.2px',
              }}
            >
              AI 智能排课
            </Text>
          )}
        </div>

        {/* 菜单 */}
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          defaultOpenKeys={openKeys}
          onClick={({ key }) => navigate(key)}
          items={menuItems}
          style={{
            background: 'transparent',
            borderRight: 'none',
            marginTop: 8,
          }}
        />
      </Sider>

      {/* 主内容区 */}
      <Layout>
        <Header
          style={{
            padding: '0 24px',
            background: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #e3e8ee',
            height: 56,
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <Space size={16}>
            <Text type="secondary" style={{ fontSize: 13 }}>
              欢迎使用智能排课系统
            </Text>
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'username',
                    label: `当前用户：${user?.username || ''}`,
                    disabled: true,
                  },
                  { type: 'divider' },
                  {
                    key: 'logout',
                    icon: <LogoutOutlined />,
                    label: '退出登录',
                    danger: true,
                  },
                ],
                onClick: ({ key }) => {
                  if (key === 'logout') {
                    handleLogout();
                  }
                },
              }}
            >
              <Avatar
                style={{ backgroundColor: '#533afd', cursor: 'pointer' }}
                icon={<UserOutlined />}
              />
            </Dropdown>
          </Space>
        </Header>

        <Content
          style={{
            margin: 20,
            padding: 24,
            background: '#ffffff',
            borderRadius: 8,
            minHeight: 280,
            overflow: 'auto',
          }}
        >
          <Outlet />
        </Content>

        <Footer
          style={{
            textAlign: 'center',
            color: '#64748d',
            fontSize: 12,
            background: 'transparent',
            padding: '12px 24px',
          }}
        >
          AI驱动一体化智能排课平台 ©2025 — 遗传算法 · 约束学习 · 智能优化
        </Footer>
      </Layout>
    </Layout>
  );
}
