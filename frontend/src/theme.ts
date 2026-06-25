// Stripe 设计系统主题配置
// 参考: DESIGN.md - Stripe-Inspired Design Analysis

import type { ThemeConfig } from 'antd';

const theme: ThemeConfig = {
  token: {
    // === 品牌色 (Stripe 电光紫) ===
    colorPrimary: '#533afd',
    colorPrimaryHover: '#665efd',
    colorPrimaryActive: '#4434d4',
    colorPrimaryBg: '#f0eeff',
    colorPrimaryBgHover: '#e6e2ff',

    // === 文字色 (Stripe ink 深蓝墨色) ===
    colorText: '#0d253d',
    colorTextSecondary: '#273951',
    colorTextTertiary: '#64748d',
    colorTextQuaternary: '#61718a',

    // === 表面色 ===
    colorBgContainer: '#ffffff',
    colorBgLayout: '#f6f9fc',
    colorBgElevated: '#ffffff',
    colorBgSpotlight: '#0d253d',

    // === 边框 ===
    colorBorder: '#e3e8ee',
    colorBorderSecondary: '#e3e8ee',

    // === 其他 ===
    colorSuccess: '#10b981',
    colorWarning: '#f59e0b',
    colorError: '#ea2261',
    colorInfo: '#533afd',

    // === 字体 ===
    fontFamily: `"Inter", -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif`,
    fontSize: 14,
    fontSizeHeading1: 32,
    fontSizeHeading2: 24,
    fontSizeHeading3: 20,
    fontSizeHeading4: 18,
    fontSizeHeading5: 16,

    // === 圆角 (紧凑) ===
    borderRadius: 6,
    borderRadiusLG: 8,
    borderRadiusSM: 4,

    // === 行高 ===
    lineHeight: 1.5,

    // === 间距 ===
    padding: 16,
    paddingLG: 24,
    paddingXS: 8,
    paddingSM: 12,
    paddingXL: 32,

    // === 控件 ===
    controlHeight: 36,
    controlHeightLG: 42,
    controlHeightSM: 30,
  },
  components: {
    Button: {
      borderRadius: 6,
      controlHeight: 36,
      paddingContentHorizontal: 16,
      fontWeight: 500,
    },
    Card: {
      borderRadius: 8,
      padding: 24,
    },
    Table: {
      borderRadius: 8,
      headerBg: '#f6f9fc',
      headerColor: '#0d253d',
      rowHoverBg: '#f6f9fc',
      borderColor: '#e3e8ee',
    },
    Menu: {
      itemBg: 'transparent',
      subMenuItemBg: 'transparent',
      darkItemBg: '#0d253d',
      darkSubMenuItemBg: '#152d47',
      darkItemColor: '#c8d2dc',
      darkItemSelectedBg: '#533afd',
      darkItemHoverBg: 'rgba(83, 58, 253, 0.15)',
    },
    Layout: {
      siderBg: '#0d253d',
      triggerBg: '#0d253d',
      triggerColor: '#c8d2dc',
    },
    Input: {
      borderRadius: 6,
      controlHeight: 36,
      paddingInline: 12,
    },
    Select: {
      borderRadius: 6,
      controlHeight: 36,
    },
    Tag: {
      borderRadius: 9999,
    },
    Modal: {
      borderRadius: 10,
    },
    Tabs: {
      inkBarColor: '#533afd',
      itemActiveColor: '#533afd',
      itemHoverColor: '#665efd',
    },
    Progress: {
      defaultColor: '#533afd',
    },
  },
};

export default theme;
